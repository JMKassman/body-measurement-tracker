from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Request,
)
from fastapi.responses import HTMLResponse
from fief_client import FiefUserInfo
from sqlmodel import Session, select
from zoneinfo import ZoneInfo

from ..database.database import get_session
from ..database.models import Measurement, MeasurementCreate
from ..dependencies.timezone import get_timezone
from ..internal.fief import fief_auth
from ..internal.templates import templates

router = APIRouter()


@router.get("/dash", name="dash", response_class=HTMLResponse)
async def dash(
    request: Request, user: FiefUserInfo = Depends(fief_auth.current_user())
):
    return templates.TemplateResponse(request, "dash.html", {"email": user["email"]})


@router.get("/new_measurement", response_class=HTMLResponse)
async def new_measurement(
    request: Request, user: FiefUserInfo = Depends(fief_auth.current_user())
):
    return templates.TemplateResponse(request, "new_measurement_form.html")


@router.post("/measurement", response_class=HTMLResponse)
async def create_measurement(
    request: Request,
    measurement: MeasurementCreate,
    timezone: Annotated[ZoneInfo, Depends(get_timezone)],
    user: FiefUserInfo = Depends(fief_auth.current_user()),
    session: Session = Depends(get_session),
):
    if measurement.timestamp is not None:
        measurement.timestamp = measurement.timestamp.replace(tzinfo=timezone)
    db_measurement = Measurement.model_validate(
        measurement, update={"user_id": user["sub"]}
    )
    session.add(db_measurement)
    session.commit()
    return get_table(request, timezone, user, session)


@router.get("/table", response_class=HTMLResponse)
def get_table(
    request: Request,
    timezone: Annotated[ZoneInfo, Depends(get_timezone)],
    user: FiefUserInfo = Depends(fief_auth.current_user()),
    session: Session = Depends(get_session),
):
    clean_measurements = []
    for measurement in session.exec(
        select(Measurement)
        .where(Measurement.user_id == user["sub"])
        .order_by(Measurement.timestamp)
    ).all():
        clean_measurement = {}
        for field, value in measurement:
            if field == "timestamp":
                value = (
                    value.replace(tzinfo=ZoneInfo("UTC"))  # make aware
                    .astimezone(timezone)  # swap to local
                    .strftime("%Y-%m-%d %I:%M:%S %p")
                )
            if value is None:
                value = ""
            clean_measurement[field] = value
        clean_measurements.append(clean_measurement)
    return templates.TemplateResponse(
        request, "table.html", {"measurements": clean_measurements}
    )
