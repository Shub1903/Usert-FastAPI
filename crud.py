from sqlalchemy.orm import Session
from . import models, schemas
from .utils import hash_password

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        username=user.username,
        password=hash_password(user.password),
        email_id=user.email_id,
        phone_no=user.phone_no,
        random_path=user.random_path,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session):
    return db.query(models.User).all()

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def delete_user(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)
    if user:
        db.delete(user)
        db.commit()
        return True
    return False

def update_user(db: Session, email_or_phone: str, updates: schemas.UserUpdate):
    user = (
        db.query(models.User)
        .filter((models.User.email_id == email_or_phone) | (models.User.phone_no == email_or_phone))
        .first()
    )
    if user:
        user.username = updates.username
        user.password = hash_password(updates.password)
        user.random_path = updates.random_path
        db.commit()
        db.refresh(user)
        return user
    return None

