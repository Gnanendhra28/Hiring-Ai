import re
from datetime import datetime, UTC

def parse_job_closing_date(description: str | None) -> tuple[str | None, bool]:
    """
    Parses Application Closing Date from job description markdown:
    - **Application Closing Date**: YYYY-MM-DD or DD/MM/YYYY
    Returns (closing_date_str: str | None, is_closed: bool).
    """
    if not description:
        return None, False

    match = re.search(r"Application Closing Date\*\*: ([^\n]+)", description)
    if not match or not match.group(1):
        return None, False

    raw_date_str = match.group(1).strip()
    if not raw_date_str:
        return None, False

    closing_dt = None
    # Try YYYY-MM-DD
    try:
        closing_dt = datetime.strptime(raw_date_str, "%Y-%m-%d").date()
    except ValueError:
        pass

    # Try DD/MM/YYYY
    if not closing_dt:
        try:
            closing_dt = datetime.strptime(raw_date_str, "%d/%m/%Y").date()
        except ValueError:
            pass

    if closing_dt:
        today = datetime.now(UTC).date()
        if today > closing_dt:
            return raw_date_str, True
        return raw_date_str, False

    return raw_date_str, False
