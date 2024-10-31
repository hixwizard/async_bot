import click

from models import AdminUser, ApplicationStatus, Question

from . import app, db

QUESTIONS = {
    1: 'Вид бизнеса: чем и как долго занимаешься?',
    2: ('Какие ограничения испытываешь в настоящий момент, '
        'что хочешь изменить или улучшить?'),
    3: 'Как справляешься, какие методы и инструменты используешь?',
    4: 'Какую цель преследуешь именно сейчас?',
    5: 'Как именно поймешь, что цель достигнута?',
}

APP_STATUSES = ['открыта', 'в работе', 'закрыта']


@app.cli.command('create_superuser')
@click.argument('login')
@click.argument('password')
def create_superuser(login: str, password: str) -> None:
    """Создает суперпользователя."""
    if db.session.execute(
        db.select(AdminUser).filter_by(login=login),
    ).scalars().first():
        click.echo(f'Суперпользователь {login} уже существует в БД')
        return
    superuser = AdminUser(login=login, password=password)
    db.session.add(superuser)
    db.session.commit()
    click.echo(f'Суперпользователь {login} успешно создан')


@app.cli.command('create_questions')
def create_questions() -> None:
    """Создает записи в таблице вопросов'."""
    if db.session.execute(db.select(Question)).scalars().all():
        click.echo('Таблица вопросов уже заполнена')
        return
    questions = [
        Question(number=key, question=value)
        for key, value in QUESTIONS.items()
    ]
    db.session.add_all(questions)
    db.session.commit()
    click.echo('Таблица вопросов заполнена')


@app.cli.command('create_statuses')
def create_statuses() -> None:
    """Создает записи в таблице статусов."""
    if db.session.execute(db.select(ApplicationStatus)).scalars().all():
        click.echo('Таблица статусов уже заполнена')
        return
    statuses = [
        ApplicationStatus(status=status) for status in APP_STATUSES
    ]
    db.session.add_all(statuses)
    db.session.commit()
    click.echo('Таблица статусов заполнена')
