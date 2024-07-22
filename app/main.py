import logging
from contextlib import asynccontextmanager
from logging.config import dictConfig

from fastapi import (
    FastAPI,
    Request,
)
from fastapi.responses import HTMLResponse

from .database.database import create_db_and_tables
from .internal.log_config import LogConfig
from .internal.templates import templates
from .routers import auth, dash

dictConfig(LogConfig().model_dump())
logger = logging.getLogger("bmt")


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)
app.include_router(dash.router)


@app.get("/", name="root", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(request, "index.html")
