import os

from fastapi import (
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.security import APIKeyCookie
from fief_client import FiefAsync
from fief_client.integrations.fastapi import FiefAuth

from ..dependencies.fief import get_memory_userinfo_cache


class CustomFiefAuth(FiefAuth):
    client: FiefAsync

    async def get_unauthorized_response(self, request: Request, response: Response):
        redirect_uri = request.url_for("auth_callback")
        auth_url = await self.client.auth_url(redirect_uri, scope=["openid"])
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": str(auth_url)},
        )


fief = FiefAsync(
    "https://auth.jmkassman.com",
    os.environ["CLIENT_ID"],
    os.environ["CLIENT_SECRET"],
    verify=(os.environ["ENVIRONMENT"] == "production"),
)

SESSION_COOKIE_NAME = "user_session"
scheme = APIKeyCookie(name=SESSION_COOKIE_NAME, auto_error=False)
fief_auth = CustomFiefAuth(fief, scheme, get_userinfo_cache=get_memory_userinfo_cache)
