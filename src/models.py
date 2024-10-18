from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


class User(declarative_base()):

    """Модель пользователей."""

    __tablename__ = 'users'

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=True)
    is_blocked = Column(Integer, default=False)
    applications = relationship("ApplicationModel", back_populates="user")
