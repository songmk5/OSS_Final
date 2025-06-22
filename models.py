from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone, timedelta

Base = declarative_base()

# 한국 시간대 설정
KST = timezone(timedelta(hours=9))


def get_kst_now():
    return datetime.now(KST)


class Consultation(Base):
    __tablename__ = "consultations"

    id = Column(Integer, primary_key=True, index=True)
    user_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    prescription = Column(Text, nullable=True)  # 처방 요약
    created_at = Column(DateTime, default=get_kst_now)