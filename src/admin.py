import os

import click
from dotenv import load_dotenv
from flask import (
    Flask,
    Response,
    flash,
    redirect,
    render_template,
    session,
    url_for,
)
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.base import BaseView
from flask_admin.contrib.sqla import ModelView
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from forms import LoginForm
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
    if db.session.query(AdminUser).filter_by(username=username).first():
        click.echo(f'Суперпользователь {username} уже существует в БД')
        return
    superuser = AdminUser(username=username, password=password)
    db.session.add(superuser)
    db.session.commit()
    click.echo(f'Суперпользователь {username} успешно создан')


class CustomAdminIndexView(AdminIndexView):

    """Класс представления главной страницы админ-панели."""

    def is_visible(self) -> bool:
        """Cкрывает вкладку Home из меню."""
        return False

    @expose('/')
    def index(self) -> Response:
        """Проверяет авторизован ли пользователь."""
        if not session.get('logged_in', False):
            flash('Вы не авторизованы. Пожалуйста, войдите в систему.',
                  'warning')
            return redirect(url_for('login'))
        return super().index()


class CustomModelView(ModelView):

    """Класс представления вкладок админ-панели."""

    def is_accessible(self) -> Response:
        """Проверяет авторизован ли пользователь."""
        return session.get('logged_in', False) is True

    def inaccessible_callback(self) -> Response:
        """Перенаправляет пользователя на страницу входа."""
        flash('Вы не авторизованы. Пожалуйста, войдите в систему.', 'warning')
        return redirect(url_for('login'))


class LogoutView(BaseView):

    """Класс представления кнопки выхода из админ-зоны."""

    @expose('/')
    def index(self) -> Response:
        """Метод выхода пользователя из админ-зоны."""
        session.pop('logged_in', None)
        flash('Вы вышли из системы.', 'info')
        return redirect(url_for('login'))

    def is_accessible(self) -> Response:
        """Метод проверки авторизации."""
        return session.get('logged_in', False)


# Инициализация админки
admin = Admin(
    app,
    name='Админ-зона',
    template_mode='bootstrap4',
    index_view=CustomAdminIndexView(),
)

# Добавление моделей в админку
admin.add_view(CustomModelView(AdminUser, db.session))
admin.add_view(CustomModelView(User, db.session))
admin.add_view(CustomModelView(Application, db.session))
admin.add_view(CustomModelView(ApplicationCheckStatus, db.session))
admin.add_view(CustomModelView(ApplicationComment, db.session))
admin.add_view(CustomModelView(Question, db.session))
admin.add_view(LogoutView(name="Выйти", endpoint="logout"))


@app.route('/')
def index() -> Response:
    """Перенаправляет пользователя на страницу входа."""
    return redirect(url_for('admin.index'))


@app.route('/login', methods=['GET', 'POST'])
def login() -> Response:
    """Отвечает за сценарий авторизации пользователя."""
    form = LoginForm()
    if form.validate_on_submit():
        # После успешного входа добавляем в объект session
        # ключ 'logged_in' с значением True
        session['logged_in'] = True
        flash('Вы вошли в систему!', 'success')
        return redirect(url_for('admin.index'))
    return render_template('login.html', form=form)


@app.route('/logout', methods=['POST'])
def logout() -> Response:
    """Отвечает за выход из админ-зоны."""
    session.pop('logged_in', None)
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
