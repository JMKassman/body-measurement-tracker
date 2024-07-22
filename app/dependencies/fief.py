import uuid

from fief_client import FiefUserInfo


class MemoryUserInfoCache:
    def __init__(self) -> None:
        self.storage: dict[uuid.UUID, FiefUserInfo] = {}

    async def get(self, user_id: uuid.UUID) -> FiefUserInfo | None:
        return self.storage.get(user_id)

    async def set(self, user_id: uuid.UUID, userinfo: FiefUserInfo) -> None:
        self.storage[user_id] = userinfo


class RedisUserInfoCache: ...


memory_userinfo_cache = MemoryUserInfoCache()


async def get_memory_userinfo_cache() -> MemoryUserInfoCache:
    return memory_userinfo_cache
