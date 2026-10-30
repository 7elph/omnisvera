"""Share overlapping reads; optional short TTL is for presentation metadata only."""
from concurrent.futures import Future
from threading import Lock
from time import monotonic


class ConcurrentReads:
    def __init__(self):
        self._lock = Lock()
        self._pending = {}
        self._recent = {}

    def run(self, key, load, *, ttl=0):
        with self._lock:
            now = monotonic()
            self._recent = {k: v for k, v in self._recent.items() if v[0] > now}
            if ttl > 0 and key in self._recent:
                return self._recent[key][1]
            future = self._pending.get(key)
            leader = future is None
            if leader:
                future = Future()
                self._pending[key] = future
        if not leader:
            return future.result()
        try:
            result = load()
            if ttl > 0:
                with self._lock:
                    self._recent[key] = (monotonic() + ttl, result)
            future.set_result(result)
            return result
        except BaseException as error:
            future.set_exception(error)
            raise
        finally:
            with self._lock:
                self._pending.pop(key, None)
