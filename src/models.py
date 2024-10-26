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
    role = Column(
        Enum('user', 'admin', 'operator', name='role_enum'),
        default='user',
    )
    is_blocked = Column(Boolean, default=False)

    applications = relationship('Application', back_populates='user')

    def __repr__(self) -> str:
        return f"{self.name}"


class Application(Base):

    """Модель заявок клиента."""

    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True, autoincrement=True)
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

    user = relationship('User', back_populates='applications')
    status = relationship('ApplicationStatus', back_populates='applications')

    def __repr__(self) -> str:
        # Отображаем имя пользователя и статус вместо объектов
        user_name = self.user.name if self.user else 'Unknown User'
        status_text = self.status.status if self.status else 'Unknown Status'
        return (f"Application(user='{user_name}', status='{status_text}', "
                f"answers='{self.answers}')")


class ApplicationStatus(Base):

    """Модель статусов заявки."""

    __tablename__ = 'statuses'

    id = Column(Integer, primary_key=True)
    status = Column(
        Enum('открыта', 'в работе', 'закрыта', name='status_enum'),
        nullable=False,
    )

    applications = relationship('Application', back_populates='status')

    def __repr__(self) -> str:
        return f"{self.status}"


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
    old_status = Column(String, nullable=False)
    new_status = Column(String, nullable=False)
    timestamp = Column(DateTime, default=func.now())


class Question(Base):

    """Модель вопросов."""

    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True)
    number = Column(Integer, nullable=False)  # Порядок вопросов
    question = Column(String, nullable=False)
