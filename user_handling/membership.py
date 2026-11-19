"""Cancelling a membership: it ends at the end of a quarter, if the cancellation comes in at least
one month before that; later, it ends at the end of the next quarter."""
import calendar
from datetime import date, timedelta


def quarter_end(day):
    month = ((day.month - 1) // 3 + 1) * 3
    return date(day.year, month, calendar.monthrange(day.year, month)[1])


def month_before(day):
    """The same day one calendar month earlier (31.12. -> 30.11., 31.03. -> 28./29.02.)."""
    year, month = (day.year, day.month - 1) if day.month > 1 else (day.year - 1, 12)
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def cancellation_dates(today=None):
    """(end, deadline): when the membership ends if cancelled today, and the last day to cancel for it."""
    today = today or date.today()
    end = quarter_end(today)
    if today > month_before(end):
        end = quarter_end(end + timedelta(days=1))
    return end, month_before(end)
