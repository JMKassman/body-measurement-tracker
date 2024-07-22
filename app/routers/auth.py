import uuid
from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import RedirectResponse

from ..dependencies.fief import MemoryUserInfoCache, get_memory_userinfo_cache
from ..internal.fief import fief, SESSION_COOKIE_NAME

router = APIRouter()


@router.get("/logout")
async def logout(request: Request, response: Response):
    response = RedirectResponse(await fief.logout_url(request.url_for("root")))
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response


@router.get("/auth-callback", name="auth_callback")
async def auth_callback(
    request: Request,
    response: Response,
    code: str = Query(...),
    memory_userinfo_cache: MemoryUserInfoCache = Depends(get_memory_userinfo_cache),
):
    redirect_uri = request.url_for("auth_callback")
    tokens, userinfo = await fief.auth_callback(code, redirect_uri)

    response = RedirectResponse(request.url_for("dash"))
    response.set_cookie(
        SESSION_COOKIE_NAME,
        tokens["access_token"],
        max_age=tokens["expires_in"],
        httponly=True,
        secure=False,
    )
    await memory_userinfo_cache.set(uuid.UUID(userinfo["sub"]), userinfo)

    return response
