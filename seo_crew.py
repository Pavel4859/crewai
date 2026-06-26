"""
CLI-запуск (альтернатива веб-интерфейсу).
Для работы из браузера используйте: streamlit run app.py  или  run_web.bat
"""
from analysis_crew import run_analysis
from reports_store import save_report

if __name__ == "__main__":
    inputs = {
        "niche": "инвестиции для новичков",
        "target_audience": "25–35 лет, хотят начать без большого капитала",
        "competitor_channels": "durov, telegram",
        "posts_per_channel": 20,
    }

    result = run_analysis(**inputs, verbose=True)
    report_path = save_report(result, **inputs)

    print(f"\nОтчёт сохранён: {report_path}")
    print(result)
