import click

from models import AdminUser, ApplicationStatus, Question

from . import app, db
from .constants import APP_STATUSES, QUESTIONS, messages


@app.cli.command('create_superuser')
@click.argument('login')
@click.argument('password')
def create_superuser(login: str, password: str) -> None:
    """Создает суперпользователя."""
    if db.session.execute(
        db.select(AdminUser).filter_by(login=login),
    ).scalars().first():
        click.echo(messages.SUPURUSER_EXISTS.format(login=login))
        return
    superuser = AdminUser(login=login, password=password)
    db.session.add(superuser)
    db.session.commit()
    click.echo(messages.SUPERUSER_CREATED.format(login=login))


@app.cli.command('create_questions')
def create_questions() -> None:
    """Создает записи в таблице вопросов'."""
    if db.session.execute(db.select(Question)).scalars().all():
        click.echo(messages.QUESTIONS_ALREADY_EXIST)
        return
    questions = [
        Question(number=key, question=value)
        for key, value in QUESTIONS.items()
    ]
    db.session.add_all(questions)
    db.session.commit()
    click.echo(messages.QUESTIONS_CREATED)


@app.cli.command('create_statuses')
def create_statuses() -> None:
    """Создает записи в таблице статусов."""
    if db.session.execute(db.select(ApplicationStatus)).scalars().all():
        click.echo(messages.STATUSES_ALREADY_EXIST)
        return
    statuses = [
        ApplicationStatus(status=status) for status in APP_STATUSES
    ]
    db.session.add_all(statuses)
    db.session.commit()
    click.echo(messages.STATUSES_CREATED)
