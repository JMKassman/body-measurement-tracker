import logging
from logging.config import dictConfig
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Path
from fastapi.responses import HTMLResponse
from fief_client import FiefUserInfo
from prophet import Prophet
from prophet.plot import plot_plotly, plot_components_plotly
from sqlmodel import Session, select
from zoneinfo import ZoneInfo
import pandas as pd
import plotly.express as px

from app.internal.log_config import LogConfig

from ..database.database import get_session
from ..database.models import Measurement, MeasurementCreate, MeasurementUpdate
from ..dependencies.timezone import get_timezone
from ..internal.fief import fief_auth
from ..internal.templates import templates

dictConfig(LogConfig().model_dump())
logger = logging.getLogger("bmt").getChild("dash")

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


@router.get("/measurement/{measurement_id}", response_class=HTMLResponse)
def get_measurement(
    measurement_id: Annotated[uuid.UUID, Path()],
    request: Request,
    timezone: Annotated[ZoneInfo, Depends(get_timezone)],
    user: FiefUserInfo = Depends(fief_auth.current_user()),
    session: Session = Depends(get_session),
):
    measurement = session.get(Measurement, measurement_id)
    if measurement is None:
        raise HTTPException(status_code=404)
    if str(measurement.user_id) != user["sub"]:
        raise HTTPException(status_code=403)
    clean_measurement = {}
    for field, value in measurement:
        if field == "timestamp":
            value = (
                value.replace(tzinfo=ZoneInfo("UTC"))  # make aware
                .astimezone(timezone)  # swap to local
                .strftime("%Y-%m-%d %I:%M %p")
            )
        if value is None:
            value = ""
        clean_measurement[field] = value
    return templates.TemplateResponse(
        request, "measurement.html", {"measurement": clean_measurement}
    )


@router.get("/measurement/{measurement_id}/edit", response_class=HTMLResponse)
def edit_measurement_form(
    measurement_id: Annotated[uuid.UUID, Path()],
    request: Request,
    timezone: Annotated[ZoneInfo, Depends(get_timezone)],
    user: FiefUserInfo = Depends(fief_auth.current_user()),
    session: Session = Depends(get_session),
):
    measurement = session.get(Measurement, measurement_id)
    if measurement is None:
        raise HTTPException(status_code=404)
    if str(measurement.user_id) != user["sub"]:
        raise HTTPException(status_code=403)
    clean_measurement = {}
    for field, value in measurement:
        if field == "timestamp":
            value = (
                value.replace(tzinfo=ZoneInfo("UTC"))  # make aware
                .astimezone(timezone)  # swap to local
                .strftime("%Y-%m-%dT%H:%M")
            )
        if value is None:
            value = ""
        clean_measurement[field] = value
    return templates.TemplateResponse(
        request, "edit_measurement.html", {"measurement": clean_measurement}
    )


@router.put("/measurement/{measurement_id}", response_class=HTMLResponse)
def update_measurement(
    measurement_id: Annotated[uuid.UUID, Path()],
    measurement: MeasurementUpdate,
    request: Request,
    timezone: Annotated[ZoneInfo, Depends(get_timezone)],
    user: FiefUserInfo = Depends(fief_auth.current_user()),
    session: Session = Depends(get_session),
):
    db_measurement = session.get(Measurement, measurement_id)
    if db_measurement is None:
        raise HTTPException(status_code=404)
    if str(db_measurement.user_id) != user["sub"]:
        raise HTTPException(status_code=403)
    measurement.timestamp = measurement.timestamp.replace(tzinfo=timezone)
    db_measurement.sqlmodel_update(measurement)
    session.add(db_measurement)
    session.commit()
    return get_measurement(measurement_id, request, timezone, user, session)


@router.delete("/measurement/{measurement_id}", response_class=HTMLResponse)
def delete_measurement(
    measurement_id: Annotated[uuid.UUID, Path()],
    user: FiefUserInfo = Depends(fief_auth.current_user()),
    session: Session = Depends(get_session),
):
    db_measurement = session.get(Measurement, measurement_id)
    if db_measurement is None:
        raise HTTPException(status_code=404)
    if str(db_measurement.user_id) != user["sub"]:
        raise HTTPException(status_code=403)
    session.delete(db_measurement)
    session.commit()
    return HTMLResponse(status_code=200)


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
                    .strftime("%Y-%m-%d %I:%M %p")
                )
            if value is None:
                value = ""
            clean_measurement[field] = value
        clean_measurements.append(clean_measurement)
    return templates.TemplateResponse(
        request, "table.html", {"measurements": clean_measurements}
    )


@router.get("/edit", response_class=HTMLResponse)
def edit_table(
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
                    .strftime("%Y-%m-%d %I:%M %p")
                )
            if value is None:
                value = ""
            clean_measurement[field] = value
        clean_measurements.append(clean_measurement)
    return templates.TemplateResponse(
        request, "edit_table.html", {"measurements": clean_measurements}
    )


@router.get("/graph", response_class=HTMLResponse)
def get_graph_page(
    request: Request,
    user: FiefUserInfo = Depends(fief_auth.current_user()),
):
    return templates.TemplateResponse(request, "graph.html")


@router.get("/graph/{variable}", response_class=HTMLResponse)
def get_graph(
    variable: Annotated[str, Path()],
    timezone: Annotated[ZoneInfo, Depends(get_timezone)],
    user: FiefUserInfo = Depends(fief_auth.current_user()),
    session: Session = Depends(get_session),
):
    measurements: list[Measurement] = session.exec(
        select(Measurement)
        .where(Measurement.user_id == user["sub"])
        .order_by(Measurement.timestamp)
    ).all()
    clean_measurements = []
    for measurement in measurements:
        measurement_dict = measurement.model_dump()
        measurement_dict["timestamp"] = (
            measurement_dict["timestamp"]
            .replace(tzinfo=ZoneInfo("UTC"))
            .astimezone(timezone)
        )
        clean_measurements.append(measurement_dict)
    df = pd.DataFrame.from_records(clean_measurements)
    return px.line(df, "timestamp", variable, markers=True).to_html(
        include_plotlyjs=False, full_html=False
    )


@router.get("/graph/{variable}/forecast", response_class=HTMLResponse)
def get_forecast_graph(
    variable: Annotated[str, Path()],
    timezone: Annotated[ZoneInfo, Depends(get_timezone)],
    user: FiefUserInfo = Depends(fief_auth.current_user()),
    session: Session = Depends(get_session),
):
    measurements: list[Measurement] = session.exec(
        select(Measurement)
        .where(Measurement.user_id == user["sub"])
        .order_by(Measurement.timestamp)
    ).all()
    clean_measurements = []
    for measurement in measurements:
        measurement_dict = measurement.model_dump()
        measurement_dict["timestamp"] = (
            measurement_dict["timestamp"]
            .replace(tzinfo=ZoneInfo("UTC"))
            .astimezone(timezone)
        )
        clean_measurements.append(measurement_dict)
    df = pd.DataFrame.from_records(clean_measurements)
    df["date"] = df["timestamp"].dt.date
    grouped_df = df.groupby("date").agg({variable: "mean"}).reset_index()
    grouped_df.columns = ["ds", "y"]
    m = Prophet()
    m.fit(grouped_df)
    future = m.make_future_dataframe(periods=max(len(grouped_df) // 10, 30))
    forecast = m.predict(future)
    main_graph = plot_plotly(
        m, forecast, xlabel="Date", ylabel=variable.title()
    ).to_html(include_plotlyjs=False, full_html=False)
    component_graph = plot_components_plotly(m, forecast).to_html(
        include_plotlyjs=False, full_html=False
    )
    return main_graph + "<br/>" + component_graph
