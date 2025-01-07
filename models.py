from sqlalchemy import Column, Integer, String
from app.database import Base

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    email_id = Column(String, unique=True, index=True, nullable=False)
    phone_no = Column(String, unique=True, nullable=False)
    random_path = Column(String, nullable=False)

