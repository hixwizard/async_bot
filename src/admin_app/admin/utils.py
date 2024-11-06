from sqlalchemy import func

from models import Application, ApplicationStatus

from . import db


def get_amount_opened_apps() -> int:
    """Получает из БД количество заявок в статусе 'открыта'."""
    return db.session.execute(
        db.select(func.count()).select_from(Application)
        .join(ApplicationStatus, Application.status_id == ApplicationStatus.id)
        .filter(ApplicationStatus.status == 'открыта'),
    ).scalar()
