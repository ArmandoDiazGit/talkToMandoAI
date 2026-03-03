from datetime import datetime, timezone

from database import Base
from sqlalchemy import Column, Integer, Text, DateTime


class TalkToMandoAI(Base):
    __tablename__ = 'MandoAI'

    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
