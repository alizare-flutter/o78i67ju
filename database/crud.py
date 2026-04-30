from sqlalchemy.orm import Session
from database.models import User, SessionLocal

def get_user(telegram_id: int):
    """
    ? Fetch a user from the database by Telegram ID.
    """
    with SessionLocal() as session:
        return session.query(User).filter(User.telegram_id == telegram_id).first()

def create_or_update_user(telegram_id: int, **kwargs):
    """
    ? Create a new user or update existing user's fields.
    """
    with SessionLocal() as session:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()

        if not user:
            user = User(telegram_id=telegram_id, **kwargs)
            session.add(user)
        else:
            for key, value in kwargs.items():
                setattr(user, key, value)

        session.commit()
        return user