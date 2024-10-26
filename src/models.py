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


class AdminUser(Base):

    """Модель администратора."""

    __tablename__ = 'admin_users'

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    role = Column(
        Enum('admin', 'operator', name='admin_role_enum'),
        default='admin',
    )


class User(Base):

    """Модель пользователя."""

    __tablename__ = 'users'

    id = Column(String, primary_key=True, nullable=False)  # ID из Telegram
    name = Column(String, nullable=False)
    email = Column(String, unique=True)
    phone = Column(String)
    is_blocked = Column(Boolean, default=False)

    applications = relationship('Application', back_populates='user')

    def __repr__(self) -> str:
        return f"{self.name}"


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
    operator_comments = relationship(
        'ApplicationComment',
        back_populates='operator',
    )
    comments = relationship('ApplicationComment', back_populates='application')

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


class ApplicationComment(Base):

    """Модель комментариев оператора к заявке."""

    __tablename__ = 'application_comments'

    id = Column(Integer, primary_key=True)
    application_id = Column(
        Integer,
        ForeignKey(
            'applications.id',
            name='fk_application_comments_application_id',
        ),
        nullable=False,
    )
    operator_id = Column(
        String,
        ForeignKey(
            'users.id',
            name='fk_application_comments_operator_id',
        ),
        nullable=False,
    )  # ID оператора, который оставил комментарий
    comment = Column(String, nullable=True)  # Может быть пустым
    timestamp = Column(DateTime, default=func.now())  # Время создания

    application = relationship('Application', back_populates='comments')
    operator = relationship('User', back_populates='operator_comments')


class Question(Base):

    """Модель вопросов."""

    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True)
    number = Column(Integer, nullable=False)  # Порядок вопросов
    question = Column(String, nullable=False)
