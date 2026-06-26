import os

import streamlit as st

from analysis_crew import run_analysis
from llm_config import get_llm_info
from reports_store import (
    delete_report,
    get_reports_dir,
    list_reports,
    load_report,
    save_report,
)
from tools.telegram_reader import fetch_public_channel, format_channel_report
from tools.channel_fetch import normalize_channel

st.set_page_config(
    page_title="Telegram Channel Analyzer",
    page_icon="📊",
    layout="wide",
)

IS_RENDER = bool(os.getenv("RENDER"))

# --- Sidebar ---
llm_info = get_llm_info()
with st.sidebar:
    if IS_RENDER:
        st.success("Сервер: **Render**")
        st.caption("Telegram и CrewAI работают на сервере")
        st.info(
            "Чтобы сохранить отчёт **на свой ПК** — нажмите "
            "«Скачать отчёт (.md)» после анализа."
        )
    else:
        st.warning("Локальный режим")
        st.caption(f"Отчёты: `{get_reports_dir().resolve()}`")

    st.divider()
    st.subheader("Подключение LLM")
    st.write(f"**Провайдер:** {llm_info['provider']}")
    st.write(f"**Модель:** {llm_info['model']}")
    st.write(f"**Base URL:** `{llm_info['base_url']}`")
    if llm_info["api_key_set"]:
        st.success("API-ключ задан")
    else:
        st.error("Добавьте OPENAI_API_KEY (Render → Environment)")

    st.divider()
    st.markdown(
        "**Как пользоваться**\n"
        "1. «Проверка каналов» — быстрый просмотр постов\n"
        "2. «Полный анализ» — 2 агента: анализ ниши + готовые посты\n"
        "3. «Сохранённые отчёты» — история на сервере\n"
        "4. Скачайте .md на ПК для постоянного хранения"
    )

st.title("📊 Telegram Channel Analyzer")
st.caption("Управление из браузера: проверка каналов и AI-анализ ниши")

tab_check, tab_analyze, tab_saved = st.tabs(
    ["🔍 Проверка каналов", "🚀 Полный анализ", "📁 Сохранённые отчёты"]
)


def parse_channels(text: str) -> list[str]:
    raw = text.replace(",", "\n").splitlines()
    return [line.strip() for line in raw if line.strip()]


# --- Tab 1: Quick channel check ---
with tab_check:
    st.subheader("Быстрая проверка публичных каналов")
    st.write("Читает каналы с сервера (без AI).")

    check_channels = st.text_area(
        "Каналы",
        placeholder="durov\n@letsfly_sletat_ru\nt.me/s/durov",
        height=120,
        key="check_channels",
    )
    check_limit = st.slider("Постов с канала", 5, 30, 10, key="check_limit")

    if st.button("🔍 Проверить каналы", type="primary", key="btn_check"):
        channels = parse_channels(check_channels)
        if not channels:
            st.error("Введите хотя бы один канал.")
        else:
            for ch in channels:
                with st.spinner(f"Читаю @{normalize_channel(ch)}…"):
                    try:
                        data = fetch_public_channel(ch, post_limit=check_limit)
                        st.markdown(f"### @{data['channel']} — {data['title']}")
                        if data.get("subscribers"):
                            st.write(f"**Подписчики:** {data['subscribers']}")
                        if data.get("description"):
                            st.write(f"**Описание:** {data['description']}")
                        st.markdown(format_channel_report(data))
                    except Exception as exc:
                        st.error(f"@{ch}: {exc}")
                st.divider()

# --- Tab 2: Full AI analysis ---
with tab_analyze:
    st.subheader("Полный анализ ниши (CrewAI)")
    st.write(
        "Два агента: **аналитик** читает каналы, **копирайтер** пишет посты только "
        "на основе реальных постов конкурентов (без выдуманных фактов). "
        "Занимает несколько минут — не закрывайте вкладку."
    )

    with st.form("analysis_form"):
        col1, col2 = st.columns(2)

        with col1:
            niche = st.text_input("Ниша / тема", placeholder="инвестиции для новичков")
            posts_per_channel = st.slider("Постов читать с каждого канала", 5, 30, 20)
            posts_to_generate = st.slider("Постов написать для вас", 5, 20, 10)

        with col2:
            target_audience = st.text_area(
                "Целевая аудитория",
                placeholder="25–35 лет, хотят начать без большого капитала",
                height=100,
            )

        competitor_channels = st.text_area(
            "Каналы для анализа",
            placeholder="channel1\nchannel2",
            height=120,
        )

        submitted = st.form_submit_button("🚀 Запустить анализ", type="primary")

    if submitted:
        channels = parse_channels(competitor_channels)
        if not niche.strip():
            st.error("Укажите нишу.")
        elif not channels:
            st.error("Укажите хотя бы один канал.")
        else:
            audience = target_audience.strip() or "не указана"
            channels_str = ", ".join(channels)

            status = st.status("Анализ на сервере…", expanded=True)
            status.write(f"Ниша: **{niche.strip()}**")
            status.write(f"Каналы: **{channels_str}**")
            status.write("Чтение Telegram → анализ → написание постов…")

            try:
                report_text = run_analysis(
                    niche=niche.strip(),
                    target_audience=audience,
                    competitor_channels=channels_str,
                    posts_per_channel=posts_per_channel,
                    posts_to_generate=posts_to_generate,
                    verbose=False,
                )
                report_path = save_report(
                    report_text,
                    niche=niche.strip(),
                    target_audience=audience,
                    competitor_channels=channels_str,
                    posts_per_channel=posts_per_channel,
                )
                status.update(label="Готово!", state="complete", expanded=False)

                if IS_RENDER:
                    st.success(
                        f"Отчёт готов. Скачайте файл на ПК — "
                        f"`{report_path.name}`"
                    )
                else:
                    st.success(f"Отчёт сохранён: `{report_path.resolve()}`")

                st.markdown(report_text)
                st.download_button(
                    "⬇️ Скачать отчёт на компьютер (.md)",
                    data=report_text,
                    file_name=report_path.name,
                    mime="text/markdown",
                    type="primary",
                )
            except Exception as exc:
                status.update(label="Ошибка", state="error", expanded=True)
                st.error(str(exc))
                st.info(
                    "На Render проверьте Environment: OPENAI_API_KEY (ProxyAPI), "
                    "OPENAI_BASE_URL=https://api.proxyapi.ru/openai/v1"
                )

# --- Tab 3: Saved reports ---
with tab_saved:
    reports = list_reports()

    if not reports:
        st.info("Отчётов пока нет. Запустите анализ на вкладке «Полный анализ».")
    else:
        if IS_RENDER:
            st.caption(
                "Отчёты хранятся на сервере до перезапуска. "
                "Скачивайте .md на ПК для постоянного хранения."
            )
        st.subheader(f"Всего отчётов: {len(reports)}")

        for item in reports:
            with st.expander(
                f"📄 {item['filename']} — {item.get('niche', 'без темы')} "
                f"({item.get('created_at', '')})"
            ):
                st.write(f"**Ниша:** {item.get('niche', '—')}")
                st.write(f"**ЦА:** {item.get('target_audience', '—')}")
                st.write(f"**Каналы:** {item.get('competitor_channels', '—')}")
                st.write(f"**Размер:** {item.get('size_kb', 0)} KB")

                try:
                    content = load_report(item["filename"])
                    st.markdown(content)
                    st.download_button(
                        "⬇️ Скачать на компьютер",
                        data=content,
                        file_name=item["filename"],
                        mime="text/markdown",
                        key=f"dl_{item['filename']}",
                    )
                except FileNotFoundError:
                    st.warning("Файл не найден.")

                if st.button("🗑 Удалить", key=f"del_{item['filename']}"):
                    delete_report(item["filename"])
                    st.rerun()
