import datetime as dt
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict, Tuple


@dataclass
class RateLimitResult:
    allowed: bool
    detail: str
    retry_after_seconds: int


class InMemoryUsageGuard:
    """
    In-memory usage guard.

    This is enough for a single-process deployment. If deployed with multiple
    workers/instances, replace this with Redis or another shared store.
    """

    def __init__(self, per_minute_limit: int, daily_limit_per_ip: int) -> None:
        self.per_minute_limit = max(1, per_minute_limit)
        self.daily_limit_per_ip = max(1, daily_limit_per_ip)

        self._minute_windows: Dict[str, Deque[float]] = defaultdict(deque)
        self._daily_counts: Dict[Tuple[str, dt.date], int] = defaultdict(int)
        self._lock = threading.Lock()

    def check_and_consume(self, client_ip: str) -> RateLimitResult:
        now = time.time()
        today = dt.date.today()

        with self._lock:
            # Minute-based window.
            window = self._minute_windows[client_ip]
            cutoff = now - 60
            while window and window[0] < cutoff:
                window.popleft()

            if len(window) >= self.per_minute_limit:
                retry_after = int(max(1, 60 - (now - window[0])))
                return RateLimitResult(
                    allowed=False,
                    detail="Rate limit tercapai. Coba lagi sebentar.",
                    retry_after_seconds=retry_after,
                )

            # Daily cap per IP.
            day_key = (client_ip, today)
            if self._daily_counts[day_key] >= self.daily_limit_per_ip:
                return RateLimitResult(
                    allowed=False,
                    detail="Batas harian penggunaan API tercapai.",
                    retry_after_seconds=60,
                )

            # Consume request.
            window.append(now)
            self._daily_counts[day_key] += 1

        return RateLimitResult(
            allowed=True,
            detail="OK",
            retry_after_seconds=0,
        )
