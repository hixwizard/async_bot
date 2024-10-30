from typing import Optional

import flask_admin as admin
import flask_login as login

from models import (
    AdminUser,
    Application,
    ApplicationCheckStatus,
    ApplicationComment,
    Question,
    User,
)

from . import app, db
from .admin_views import CustomAdminIndexView, CustomModelView, SuperModelView


def init_login() -> None:
    """Инициализирует менеджер входа в систему."""
    login_manager = login.LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: int) -> Optional[AdminUser]:
        """Загружает пользователя из базы данных."""
        return db.session.query(AdminUser).get(user_id)


# Инициализация системы работы с пользователями
init_login()

# Инициализация админки
admin = admin.Admin(
    app,
    name='Turutin Bot',
    template_mode='bootstrap4',
    index_view=CustomAdminIndexView(),
    base_template='my_master.html',
)

# Добавление моделей в админку
admin.add_view(SuperModelView(AdminUser, db.session,
                              name='Личный кабинет'))
admin.add_view(CustomModelView(User, db.session, name='Клиенты'))
admin.add_view(CustomModelView(Application, db.session, name='Заявки'))
admin.add_view(CustomModelView(ApplicationCheckStatus, db.session,
                               name='Статусы заявок'))
admin.add_view(CustomModelView(ApplicationComment, db.session,
                               name='Комментарии'))
admin.add_view(SuperModelView(Question, db.session, name='Вопросы'))
