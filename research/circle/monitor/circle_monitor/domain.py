from __future__ import annotations

import calendar
import datetime as dt
import hashlib
import json
import math
from dataclasses import dataclass

UTC = dt.timezone.utc


class DataError(ValueError):
    """A source or model precondition failed; do not invent a replacement."""


class ReviewRequired(DataError):
    """A disclosure cannot be interpreted unambiguously."""


def timestamp(value: str | dt.datetime) -> dt.datetime:
    result = dt.datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    if result.tzinfo is None:
        raise DataError("Timestamps must include a timezone")
    return result.astimezone(UTC)


def iso(value: dt.datetime) -> str:
    return timestamp(value).isoformat().replace("+00:00", "Z")


def date_only_end(value: str) -> str:
    """Date-only financial/fund availability is conservatively end-of-day UTC."""
    return value[:10] + "T23:59:59.999999Z"


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def digest(value) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def number(value, *, minimum=None, maximum=None) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise DataError("Invalid numeric value") from exc
    if not math.isfinite(result) or (minimum is not None and result < minimum) or (maximum is not None and result > maximum):
        raise DataError(f"Non-finite or out-of-range value: {result}")
    return result


@dataclass(frozen=True, order=True)
class Quarter:
    year: int
    quarter: int

    def __post_init__(self):
        if not 1900 <= self.year <= 2200 or self.quarter not in range(1, 5):
            raise DataError("Invalid quarter")

    @classmethod
    def parse(cls, text: str) -> Quarter:
        if len(text) != 6 or text[4] != "Q":
            raise DataError("Quarter must be YYYYQn")
        return cls(int(text[:4]), int(text[5]))

    @classmethod
    def containing(cls, day: dt.date) -> Quarter:
        return cls(day.year, (day.month - 1) // 3 + 1)

    @property
    def key(self):
        return f"{self.year}Q{self.quarter}"

    @property
    def start(self):
        return dt.date(self.year, self.quarter * 3 - 2, 1)

    @property
    def end(self):
        month = self.quarter * 3
        return dt.date(self.year, month, calendar.monthrange(self.year, month)[1])

    @property
    def days(self):
        return (self.end - self.start).days + 1

    def shift(self, count):
        index = self.year * 4 + self.quarter - 1 + count
        return Quarter(index // 4, index % 4 + 1)

    def dates(self):
        return [self.start + dt.timedelta(days=i) for i in range(self.days)]


def duration_quarter(start: str, end: str):
    q = Quarter.containing(dt.date.fromisoformat(end))
    return q if start == q.start.isoformat() and end == q.end.isoformat() else None
