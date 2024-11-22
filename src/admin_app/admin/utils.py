from datetime import datetime, timedelta

import pytz
from sqlalchemy import func

from models import Application, ApplicationStatus

from . import db
from .constants import DEFAULT_APP_STATUS, TIME_ZONE


def get_amount_opened_apps() -> int:
    """Получает из БД количество заявок в статусе 'открыта'."""
    return db.session.execute(
        db.select(func.count()).select_from(Application)
        .join(ApplicationStatus, Application.status_id == ApplicationStatus.id)
        .filter(ApplicationStatus.status == DEFAULT_APP_STATUS),
    ).scalar()


def get_amount_new_apps() -> int:
    """Получает из БД количество новых заявок за последние 10 секунд."""
    moscow_tz = pytz.timezone(TIME_ZONE)
    last_check = datetime.now(moscow_tz) - timedelta(seconds=10)
    return db.session.execute(
        db.select(func.count(Application.id))
        .where(Application.timestamp > last_check),
    ).scalar()
