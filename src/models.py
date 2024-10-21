from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):

    """Базовый класс для моделей."""

    pass


# class UserRole(StrEnum):

#     """Варианты ролей пользователей."""

#     USER = 'клиент'
#     ADMIN = 'администратор'
#     OPERATOR = 'оператор'


# class Status(StrEnum):

#     """Варианты статусов заявки."""

#     OPEN = 'открыта'
#     IN_WORK = 'в работе'
#     CLOSE = 'закрыта'


class User(Base):

    """Модель пользователя."""

    __tablename__ = 'users'

    id = Column(String, primary_key=True, index=True)  # ID из Telegram
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    phone = Column(String, nullable=True)
    role = Column(
        Enum('user', 'admin', 'operator', name='role_enum'),
        default='user',
    )
    is_blocked = Column(Boolean, default=False)
    applications = relationship('Application', back_populates='user')


class Application(Base):

    """Модель заявок клиента."""

    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True)
    user_id = Column(
        String,
        ForeignKey('users.id', name='fk_applications_user_id_users'),
        nullable=False,
    )
    status_id = Column(
        Integer,
        ForeignKey('statuses.id', name='fk_applications_status_id_statuses'),
        nullable=False,
    )
    answers = Column(String, nullable=False)  # Ответы клиента на вопросы


class ApplicationStatus(Base):

    """Модель статусов заявки."""

    __tablename__ = 'statuses'

    id = Column(Integer, primary_key=True)
    status = Column(
        Enum('открыта', 'в работе', 'закрыта', name='status_enum'),
        nullable=False,
    )
    applications = relationship('Application', back_populates='status')


class ApplicationCheckStatus(Base):

    """Модель логов изменений статусов заявок."""

    __tablename__ = 'check_status'
    id = Column(Integer, primary_key=True)
    application_id = Column(
        Integer,
        ForeignKey(
            'applications.id',
            name='fk_check_status_application_id_applications',
        ),
        nullable=False,
    )
    modified_by = Column(String, ForeignKey('users.id'))  # Кто изменил
    old_status = Column(String, nullable=False)
    new_status = Column(String, nullable=False)
    timestamp = Column(DateTime, default=func.now())


class Question(Base):

    """Модель вопросов."""

    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True)
    number = Column(Integer, nullable=False)  # Порядок вопросов
    question = Column(String, nullable=False)