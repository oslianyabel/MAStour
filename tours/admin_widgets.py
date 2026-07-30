import datetime
import re

from django import forms

TWELVE_HOUR_PATTERN = re.compile(r'^(\d{1,2}):(\d{2})(?::(\d{2}))?(am|pm)$')


class TwelveHourTimeWidget(forms.TimeInput):
    """Renders times as ``hh:mm AM/PM`` and hooks the custom clock picker.

    The value is formatted manually instead of via ``strftime('%p')`` so the output
    never depends on the process locale.
    """

    def __init__(self, attrs: dict | None = None) -> None:
        # A class other than Django's ``vTimeField`` keeps the built-in (24h) clock
        # shortcuts from attaching, so only the custom picker is active.
        default_attrs = {'class': 'vTime12Field', 'placeholder': 'hh:mm AM', 'size': '12'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)

    def format_value(self, value: object) -> str | None:
        if isinstance(value, datetime.datetime | datetime.time):
            hour = value.hour % 12 or 12
            meridiem = 'AM' if value.hour < 12 else 'PM'
            return f'{hour:02d}:{value.minute:02d} {meridiem}'
        if isinstance(value, str) and value:
            return value
        return super().format_value(value)


class TwelveHourTimeField(forms.TimeField):
    """Time field that accepts ``hh:mm AM/PM`` in addition to the 24h formats.

    Parsing is done without ``strptime('%p')`` so it works regardless of locale.
    """

    widget = TwelveHourTimeWidget

    def to_python(self, value: object) -> datetime.time | None:
        if isinstance(value, str):
            normalized = self._normalize_meridiem(value)
            if normalized is not None:
                value = normalized
        return super().to_python(value)

    @staticmethod
    def _normalize_meridiem(raw_value: str) -> str | None:
        """Convert ``08:30 PM`` into ``20:30:00``; return None if not a 12h value."""
        text = raw_value.strip().lower().replace('.', '').replace(' ', '')
        match = TWELVE_HOUR_PATTERN.match(text)
        if match is None:
            return None
        hour = int(match.group(1))
        if not 1 <= hour <= 12:
            return None
        minute = match.group(2)
        second = match.group(3) or '00'
        if hour == 12:
            hour = 0
        if match.group(4) == 'pm':
            hour += 12
        return f'{hour:02d}:{minute}:{second}'


def format_time_12h(value: datetime.time | None) -> str:
    """Format a time as ``hh:mm AM/PM`` for admin list columns."""
    if value is None:
        return '—'
    hour = value.hour % 12 or 12
    meridiem = 'AM' if value.hour < 12 else 'PM'
    return f'{hour:02d}:{value.minute:02d} {meridiem}'
