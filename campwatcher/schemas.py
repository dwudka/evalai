"""Request and response models."""

from pydantic import BaseModel, Field, validator


class WatcherCreate(BaseModel):
    """Schema for creating a watcher."""

    campground_id: str = Field(..., description="Recreation.gov campground ID")
    site_type: str | None = Field(None, description="Campsite type")
    tent_only: bool = Field(False, description="Only tent sites")
    no_rv: bool = Field(False, description="Exclude RV sites")
    loop: str | None = Field(None, description="Campground loop")

    check_time: str = Field(..., regex=r"^\d{2}:\d{2}$", description="Time in HH:MM")
    email: str | None = Field(None, description="Notification email")

    @validator("check_time")
    def _validate_time(cls, v: str) -> str:  # noqa: D401,N802
        hour, minute = map(int, v.split(":"))
        if hour not in range(24) or minute not in range(60):
            raise ValueError("check_time must be valid HH:MM")
        return v
