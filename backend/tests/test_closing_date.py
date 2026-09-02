from datetime import datetime, timedelta, UTC
from app.domains.jobs.closing_date import parse_job_closing_date

def test_parse_job_closing_date_future():
    future_date = (datetime.now(UTC).date() + timedelta(days=10)).strftime("%d/%m/%Y")
    desc = f"## Work Location\n- **Application Closing Date**: {future_date}\n\n## Responsibilities"
    date_str, is_closed = parse_job_closing_date(desc)
    assert date_str == future_date
    assert is_closed is False

def test_parse_job_closing_date_past():
    past_date = (datetime.now(UTC).date() - timedelta(days=5)).strftime("%d/%m/%Y")
    desc = f"## Work Location\n- **Application Closing Date**: {past_date}\n\n## Responsibilities"
    date_str, is_closed = parse_job_closing_date(desc)
    assert date_str == past_date
    assert is_closed is True

def test_parse_job_closing_date_none():
    desc = "## Work Location\n- **Location**: Remote\n\n## Responsibilities"
    date_str, is_closed = parse_job_closing_date(desc)
    assert date_str is None
    assert is_closed is False
