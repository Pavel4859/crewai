import json
from datetime import datetime
from pathlib import Path

REPORTS_DIR = Path(__file__).parent / "reports"


def get_reports_dir() -> Path:
    return ensure_reports_dir()


def ensure_reports_dir() -> Path:
    REPORTS_DIR.mkdir(exist_ok=True)
    return REPORTS_DIR


def _meta_path(report_path: Path) -> Path:
    return report_path.with_suffix(".meta.json")


def save_report(
    content: str,
    *,
    niche: str,
    target_audience: str,
    competitor_channels: str,
    posts_per_channel: int,
) -> Path:
    ensure_reports_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR / f"channel_analysis_{timestamp}.md"
    report_path.write_text(content, encoding="utf-8")

    meta = {
        "filename": report_path.name,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "niche": niche,
        "target_audience": target_audience,
        "competitor_channels": competitor_channels,
        "posts_per_channel": posts_per_channel,
    }
    _meta_path(report_path).write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report_path


def list_reports() -> list[dict]:
    ensure_reports_dir()
    reports: list[dict] = []

    for report_path in sorted(REPORTS_DIR.glob("channel_analysis_*.md"), reverse=True):
        meta_path = _meta_path(report_path)
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        else:
            meta = {
                "filename": report_path.name,
                "created_at": datetime.fromtimestamp(
                    report_path.stat().st_mtime
                ).isoformat(timespec="seconds"),
                "niche": "",
                "target_audience": "",
                "competitor_channels": "",
                "posts_per_channel": 0,
            }

        meta["size_kb"] = round(report_path.stat().st_size / 1024, 1)
        reports.append(meta)

    return reports


def load_report(filename: str) -> str:
    path = REPORTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Отчёт не найден: {filename}")
    return path.read_text(encoding="utf-8")


def delete_report(filename: str) -> None:
    path = REPORTS_DIR / filename
    if path.exists():
        path.unlink()
    meta_path = _meta_path(path)
    if meta_path.exists():
        meta_path.unlink()
