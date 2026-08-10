"""CP4 — Stateless: state sống ngoài process.

Nếu lịch sử hội thoại nằm trong một dict trong RAM, thì khi scale lên 3
instance, client gửi tin 1 vào instance A và tin 2 vào instance B sẽ thấy
service "mất trí nhớ". Container còn bị restart bất cứ lúc nào. Vì vậy state
phải nằm ở nơi mọi instance cùng nhìn thấy: Redis.
"""

from __future__ import annotations

import json

import redis

from .config import get_settings

HISTORY_MAX_MESSAGES = 12
HISTORY_TTL_SECONDS = 3 * 24 * 3600


def get_redis_client(url: str | None = None):
    """CHO SẴN — tạo client Redis từ URL.

    ``fake://`` trả về Redis giả chạy trong RAM, dùng khi máy bạn chưa có
    Docker. Tiện cho lúc học, nhưng KHÔNG dùng khi deploy: nó vẫn là state
    trong process, đúng cái mà CP4 đang tìm cách loại bỏ.
    """
    url = url or get_settings().redis_url
    if url.startswith("fake://"):
        import fakeredis

        return fakeredis.FakeRedis(decode_responses=True)
    return redis.from_url(url, decode_responses=True)


class ChatStore:
    """Lưu lịch sử hội thoại của từng client trong Redis List."""

    def __init__(self, client) -> None:
        self.client = client

    @staticmethod
    def _key(client_id: str) -> str:
        """CHO SẴN."""
        return f"chat:{client_id}"

    def ping(self) -> bool:
        try:
            return bool(self.client.ping())
        except Exception:
            return False

    def add_turn(self, client_id: str, role: str, content: str) -> None:
        key = self._key(client_id)
        payload = json.dumps({"role": role, "content": content}, ensure_ascii=False)
        with self.client.pipeline(transaction=True) as pipe:
            pipe.rpush(key, payload)
            pipe.ltrim(key, -HISTORY_MAX_MESSAGES, -1)
            pipe.expire(key, HISTORY_TTL_SECONDS)
            pipe.execute()

    def add_exchange(
        self,
        client_id: str,
        user_content: str,
        assistant_content: str,
    ) -> None:
        """Ghi trọn cặp user/assistant để request đồng thời không xen kẽ."""
        key = self._key(client_id)
        payloads = (
            json.dumps({"role": "user", "content": user_content}, ensure_ascii=False),
            json.dumps(
                {"role": "assistant", "content": assistant_content},
                ensure_ascii=False,
            ),
        )
        with self.client.pipeline(transaction=True) as pipe:
            pipe.rpush(key, *payloads)
            pipe.ltrim(key, -HISTORY_MAX_MESSAGES, -1)
            pipe.expire(key, HISTORY_TTL_SECONDS)
            pipe.execute()

    def history(self, client_id: str) -> list[dict]:
        key = self._key(client_id)
        raw_items = self.client.lrange(key, 0, -1)
        if not raw_items:
            return []
        return [json.loads(item) for item in raw_items]


    def reset(self, client_id: str) -> None:
        """CHO SẴN — xóa lịch sử của một client."""
        self.client.delete(self._key(client_id))
