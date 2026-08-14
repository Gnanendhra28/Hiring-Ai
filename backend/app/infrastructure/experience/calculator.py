import re
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

class ExperienceCalculator:
    """
    Deterministic Experience Calculator.
    Calculates total candidate years/months of experience from employment records.
    Merges overlapping employment periods to prevent double-counting.
    """

    @staticmethod
    def parse_date(date_str: Optional[str]) -> Tuple[Optional[date], bool]:
        if not date_str or not date_str.strip():
            return None, False

        cleaned = date_str.strip().lower()
        if cleaned in ("present", "current", "now", "ongoing"):
            return date.today(), True

        # Try parsing YYYY-MM or YYYY-MM-DD or YYYY
        try:
            match_full = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", cleaned)
            if match_full:
                year, month, day = int(match_full.group(1)), int(match_full.group(2)), int(match_full.group(3))
                return date(year, month, day), False

            match_ym = re.search(r"(\d{4})[-/](\d{1,2})", cleaned)
            if match_ym:
                year, month = int(match_ym.group(1)), int(match_ym.group(2))
                return date(year, month, 1), False

            match_y = re.search(r"(\d{4})", cleaned)
            if match_y:
                year = int(match_y.group(1))
                return date(year, 1, 1), False
        except Exception:
            pass

        return None, False

    @classmethod
    def calculate_employment_duration_months(cls, start_date: Optional[date], end_date: Optional[date]) -> int:
        if not start_date:
            return 0

        target_end = end_date or date.today()
        if target_end < start_date:
            return 0

        months = (target_end.year - start_date.year) * 12 + (target_end.month - start_date.month)
        return max(1, months)

    @classmethod
    def calculate_total_experience(cls, experiences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merges overlapping date ranges and computes net total experience in months and years.
        """
        ranges: List[Tuple[date, date]] = []

        for exp in experiences:
            start, _ = cls.parse_date(exp.get("raw_start_date") or str(exp.get("start_date") or ""))
            end, is_current = cls.parse_date(exp.get("raw_end_date") or str(exp.get("end_date") or ""))

            if is_current or exp.get("is_current"):
                end = date.today()

            if start:
                ranges.append((start, end or date.today()))

        if not ranges:
            return {"total_months": 0, "total_years": 0.0, "merged_periods_count": 0}

        # Sort ranges by start date
        ranges.sort(key=lambda r: r[0])

        # Merge overlapping ranges
        merged: List[Tuple[date, date]] = []
        for curr_start, curr_end in ranges:
            if not merged:
                merged.append((curr_start, curr_end))
            else:
                prev_start, prev_end = merged[-1]
                if curr_start <= prev_end:
                    # Overlap detected! Extend end date if necessary
                    merged[-1] = (prev_start, max(prev_end, curr_end))
                else:
                    merged.append((curr_start, curr_end))

        total_months = 0
        for start, end in merged:
            total_months += cls.calculate_employment_duration_months(start, end)

        total_years = round(total_months / 12.0, 1)

        return {
            "total_months": total_months,
            "total_years": total_years,
            "merged_periods_count": len(merged),
        }
