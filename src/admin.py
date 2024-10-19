import os

from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import User

app = Flask(__name__)

DB_URL = os.getenv(
    'DATABASE_URL', 'postgresql://user:password@localhost:5432/mydatabase',
)
engine = create_engine(DB_URL, echo=True)
Session = sessionmaker(bind=engine)
session = Session()


class UserAdminView(ModelView):

    """Панель администратора для модели пользователей."""

    can_edit = True
    can_delete = True
    can_create = True
    column_filters = ['is_blocked']


admin = Admin(app, name='Админ-зона', template_mode='bootstrap3')
admin.add_view(UserAdminView(User, session))


if __name__ == '__main__':
    app.run()
