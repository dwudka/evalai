from sqlalchemy import Boolean, Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import config

engine = create_engine(config.db_uri)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)


class Watcher(Base):
    """Database model for stored watchers."""

    __tablename__ = "watchers"

    id = Column(Integer, primary_key=True)
    campground_id = Column(String, nullable=False)
    site_type = Column(String, nullable=True)
    tent_only = Column(Boolean, default=False)
    no_rv = Column(Boolean, default=False)
    loop = Column(String, nullable=True)
    check_time = Column(String, nullable=False)  # HH:MM
    email = Column(String, nullable=True)


Base.metadata.create_all(engine)
