import os
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration."""

    search_api: str = os.getenv(
        "SEARCH_API", "https://www.recreation.gov/api/facilities"
    )
    availability_api: str = os.getenv(
        "AVAILABILITY_API",
        "https://www.recreation.gov/api/camps/availability/campground/{campground_id}/month",
    )
    db_uri: str = os.getenv("DATABASE_URI", "sqlite:///watchers.db")


config = Config()
