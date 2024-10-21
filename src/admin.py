import os

from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from models import (
    Application,
    ApplicationCheckStatus,
    ApplicationStatus,
    Question,
    User,
)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_FLASK', 'mysecretkey')
# Получаем URL базы данных из переменной окружения
DB_URL = os.getenv(
    'DATABASE_URL', 'postgresql://user:password@localhost:5432/mydatabase',
)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Создание объектов SQLAlchemy и Migrate
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class UserAdminView(ModelView):

    """Панель администратора для модели пользователей."""

    column_filters = ['is_blocked']


admin = Admin(app, name='Админ-зона', template_mode='bootstrap3')
admin.add_view(UserAdminView(User, db.session))
admin.add_view(ModelView(Application, db.session))
admin.add_view(ModelView(ApplicationStatus, db.session))
admin.add_view(ModelView(ApplicationCheckStatus, db.session))
admin.add_view(ModelView(Question, db.session))

if __name__ == '__main__':
    app.run()
