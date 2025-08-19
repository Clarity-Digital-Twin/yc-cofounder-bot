from __future__ import annotations

from ..storage import read_count, write_count


class FileQuota:
    def check_and_increment(self, limit: int) -> bool:
        n = read_count()
        if n >= limit:
            return False
        write_count(n + 1)
        return True

