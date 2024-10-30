import os

import click
from dotenv import load_dotenv
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from models import AdminUser

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_FLASK')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


@app.cli.command('createsuperuser')
@click.argument('login')
@click.argument('password')
def create_superuser(login: str, password: str) -> None:
    """Создание суперпользователя."""
    if db.session.query(AdminUser).filter_by(login=login).first():
        click.echo(f'Суперпользователь {login} уже существует в БД')
        return
    superuser = AdminUser(login=login, password=password)
    db.session.add(superuser)
    db.session.commit()
    click.echo(f'Суперпользователь {login} успешно создан')


from . import admin, admin_views, forms, views # noqa
