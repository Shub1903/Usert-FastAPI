from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# app/database.py
SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://root:Shubh_0307@localhost:3306/user_db"



engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

