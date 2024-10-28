import os
from typing import Any, Dict, Optional

import click
import flask_admin as admin
import flask_login as login
from dotenv import load_dotenv
from flask import (
    Flask,
    Response,
    flash,
    redirect,
    request,
    url_for,
)
from flask_admin import expose, helpers
from flask_admin.contrib.sqla import ModelView
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from wtforms import Field, fields, form, validators

from models import (
    AdminUser,
    Application,
    ApplicationCheckStatus,
    ApplicationComment,
    Question,
    User,
)

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_FLASK')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


@app.cli.command('createsuperuser')
@click.argument('username')
@click.argument('password')
def create_superuser(username: str, password: str) -> None:
    """Создание суперпользователя."""
    if db.session.query(AdminUser).filter_by(login=username).first():
        click.echo(f'Суперпользователь {username} уже существует в БД')
        return
    superuser = AdminUser(login=username, password=password)
    db.session.add(superuser)
    db.session.commit()
    click.echo(f'Суперпользователь {username} успешно создан')


class LoginForm(form.Form):

    """Форма входа в систему."""

    login = fields.StringField(validators=[validators.InputRequired()])
    password = fields.PasswordField(validators=[validators.InputRequired()])

    def validate_login(self, field: Field) -> None:
        """Выполняет валидацию имени пользователя и пароля."""
        user = self.get_user()
        if user is None:
            raise validators.ValidationError(
                'Такой пользователь не зарегистрирован',
            )
        if user.password != self.password.data:
            raise validators.ValidationError(
                'Неверный пароль, повторите попытку',
            )

    def get_user(self) -> Optional[AdminUser]:
        """Получает пользователя из БД по полю 'username'."""
        return db.session.query(AdminUser).filter_by(
            login=self.login.data,
        ).first()


def init_login() -> None:
    """Инициализирует менеджер входа в систему."""
    login_manager = login.LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: int) -> Optional[AdminUser]:
        """Загружает пользователя из базы данных."""
        return db.session.query(AdminUser).get(user_id)


class CustomAdminIndexView(admin.AdminIndexView):

    """Класс представления главной страницы админ-панели."""

    def is_visible(self) -> bool:
        """Cкрывает вкладку Home из меню."""
        return False

    @expose("/")
    def index(self) -> Response:
        """Проверяет, авторизован ли пользователь."""
        if not login.current_user.is_authenticated:
            return redirect(url_for(".login_view"))
        return super().index()

    @expose("/login/", methods=("GET", "POST"))
    def login_view(self) -> Response:
        """Определяет логику входа пользователя в систему."""
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            login.login_user(user)
        if login.current_user.is_authenticated:
            flash('Вы вошли в систему!', 'success')
            return redirect(url_for(".index"))
        self._template_args["form"] = form
        return super().index()

    @expose("/logout/")
    def logout_view(self) -> Response:
        """Определяет логику выхода пользователя из системы."""
        login.logout_user()
        flash('Вы вышли из системы.', 'info')
        return redirect(url_for(".index"))


class CustomModelView(ModelView):

    """Класс представления вкладок админ-панели."""

    def is_accessible(self) -> Response:
        """Проверяет авторизован ли пользователь."""
        return login.current_user.is_authenticated

    def inaccessible_callback(
            self, name: str, **kwargs: Dict[str, Any],
    ) -> Response:
        """Перенаправляет пользователя на страницу входа."""
        flash('Вы не авторизованы. Пожалуйста, войдите в систему.', 'warning')
        return redirect(url_for('admin.index'))


@app.route('/')
def index() -> Response:
    """Перенаправляет пользователя на страницу '/admin'."""
    return redirect(url_for('admin.index'))


# Инициализация системы работы с пользователями
init_login()

# Инициализация админки
admin = admin.Admin(
    app,
    name='Админ-зона',
    template_mode='bootstrap4',
    index_view=CustomAdminIndexView(),
    base_template='my_master.html',
)

# Добавление моделей в админку
admin.add_view(CustomModelView(AdminUser, db.session, name='Личный кабинет'))
admin.add_view(CustomModelView(User, db.session, name='Клиенты'))
admin.add_view(CustomModelView(Application, db.session, name='Заявки'))
admin.add_view(CustomModelView(ApplicationCheckStatus, db.session,
                               name='Статусы заявок'))
admin.add_view(CustomModelView(ApplicationComment, db.session,
                               name='Комментарии'))
admin.add_view(CustomModelView(Question, db.session, name='Вопросы'))


if __name__ == '__main__':
    app.run(debug=True)
