from datetime import datetime
import uuid
from sqlmodel import Field, SQLModel


class MeasurementBase(SQLModel):
    weight: float
    fat_perc: float | None
    muscle_perc: float | None
    water_perc: float | None
    bmi: float | None


class Measurement(MeasurementBase, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    timestamp: datetime | None = Field(default_factory=datetime.now, nullable=False)
    user_id: uuid.UUID = Field(index=True)


class MeasurementCreate(MeasurementBase):
    timestamp: datetime | None


class MeasurementPublic(MeasurementBase):
    id: uuid.UUID
    timestamp: datetime


class MeasurementUpdate(SQLModel):
    id: uuid.UUID
    weight: float | None
    fat_perc: float | None
    muscle_perc: float | None
    water_perc: float | None
    bmi: float | None
