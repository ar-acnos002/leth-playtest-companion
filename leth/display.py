"""Display formatting; persisted session values remain unchanged."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def format_journal_timestamp(value):
    """Render an ISO timestamp in IST, with no leading zero on the hour."""
    timestamp = datetime.fromisoformat(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    local = timestamp.astimezone(ZoneInfo("Asia/Kolkata"))
    return f"{local:%d %b %Y} · {local.hour % 12 or 12}:{local:%M %p}"
