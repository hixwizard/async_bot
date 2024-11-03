from typing import Optional

from wtforms import Field, fields, form, validators

from models import AdminUser

from . import db


class LoginForm(form.Form):

    """Форма входа в систему."""

    login = fields.StringField(
        'Логин',
        validators=[validators.InputRequired()],
    )
    password = fields.PasswordField(
        'Пароль',
        validators=[validators.InputRequired()],
    )

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
        """Получает пользователя из БД по полю 'login'."""
        return db.session.query(AdminUser).filter_by(
            login=self.login.data,
        ).first()
