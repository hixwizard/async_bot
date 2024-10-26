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
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):

    """Модель пользователя."""

    __tablename__ = 'users'

    id = Column(String, primary_key=True, nullable=False)  # ID из Telegram
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    phone = Column(String, nullable=True)
    is_blocked = Column(Boolean, default=False)

    applications = relationship('Application', back_populates='user')


class AdminUser(Base):

    """Модель администратора."""

    __tablename__ = 'admin_users'

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    role = Column(
        Enum('admin', 'operator', name='admin_role_enum'),
        default='admin',
        nullable=False,
    )


class Application(Base):

    """Модель заявок клиента."""

    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True)
    user_id = Column(
        String,
        ForeignKey('users.id', name='fk_applications_user_id_users'),
        nullable=False,
    )
    status = Column(
        Enum('открыта', 'в работе', 'закрыта', name='status_enum'),
        nullable=False,
    )
    answers = Column(String, nullable=False)  # Ответы клиента на вопросы

    user = relationship('User', back_populates='applications')


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
