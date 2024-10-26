import os

import click
from dotenv import load_dotenv
from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

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


class UserAdminView(ModelView):

    """Панель администратора для модели пользователей."""

    column_filters = ['is_blocked']


admin = Admin(app, name='Админ-зона', template_mode='bootstrap4')
admin.add_view(UserAdminView(User, db.session))
admin.add_view(ModelView(AdminUser, db.session))
admin.add_view(ModelView(Application, db.session))
admin.add_view(ModelView(ApplicationCheckStatus, db.session))
admin.add_view(ModelView(ApplicationComment, db.session))
admin.add_view(ModelView(Question, db.session))


if __name__ == '__main__':
    app.run(debug=True)
