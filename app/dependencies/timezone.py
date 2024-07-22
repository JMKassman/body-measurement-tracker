import logging
from logging.config import dictConfig
from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException, Header

from ..internal.log_config import LogConfig

dictConfig(LogConfig().model_dump())
logger = logging.getLogger("bmt").getChild("timezone")


async def get_timezone(x_timezone: Annotated[str, Header()]) -> ZoneInfo:
    try:
        return ZoneInfo(x_timezone)
    except ZoneInfoNotFoundError as e:
        logger.error(e)
        return HTTPException(status_code=400, detail="X-Timezone header is invalid")
