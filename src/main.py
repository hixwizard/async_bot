import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, List

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application as TelegramApplication
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    MessageHandler,
    filters,
)

from models import Application, Question, User

# Загрузка переменных окружения из .env файла
load_dotenv()


ADMIN_CHAT_ID = '123'  # стоит убрать и отправлять сообщения role - operator
BOT_TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_ASYNC_URL')

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Создание асинхронного движка базы данных
engine = create_async_engine(DATABASE_URL, echo=True)

# Создание фабрики сессий
async_session_factory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_async_db_session() -> AsyncIterator[AsyncSession]:
    """Создание асинхронной сессии базы данных."""
    async with async_session_factory() as session:
        yield session


async def get_questions() -> List[dict]:
    """Получение вопросов из базы данных в виде списка словарей."""
    async with get_async_db_session() as session:
        result = await session.execute(
            select(Question).order_by(Question.number),
        )
        questions = result.scalars().all()
        return [
            {'number': q.number, 'question': q.question} for q in questions
        ]


async def save_user_to_db(
        user_id: str, first_name: str, username: str,
) -> None:
    """Сохранение пользователя в базу данных, если его еще нет."""
    async with get_async_db_session() as session:
        result = await session.execute(select(User).filter_by(id=user_id))
        user = result.scalars().first()

        if not user:
            # Если пользователя нет, создаем новую запись
            new_user = User(
                id=user_id, name=first_name, email=None,
                phone=None, role='user', is_blocked=False,
            )
            session.add(new_user)
            await session.commit()
            logger.info(
                f"Сохранен новый пользователь {first_name} с ID {user_id}.",
            )


async def start(update: Update, context: CallbackContext) -> None:
    """Отправка сообщения и сохранение информации о пользователе."""
    # Извлечение информации о пользователе из обновления
    user_id = str(update.message.from_user.id)
    first_name = update.message.from_user.first_name
    username = update.message.from_user.username

    # Сохранение пользователя в базу данных
    await save_user_to_db(user_id, first_name, username)

    # Отправка приветственного сообщения
    keyboard = [['Начать']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text(
        'Добро пожаловать! Нажмите "Начать", чтобы начать опрос.',
        reply_markup=reply_markup)
    context.user_data['started'] = False


async def handle_start_button(
        update: Update, context: CallbackContext,
) -> None:
    """Обработка нажатия кнопки 'Начать' и запуск первого вопроса."""
    if not context.user_data.get('started', False):
        questions = await get_questions()
        if questions:
            await update.message.reply_text(questions[0]['question'])
            context.user_data['questions'] = questions
            context.user_data['current_question'] = 0
            context.user_data['started'] = True
    else:
        await update.message.reply_text('Опрос уже начат!')


async def process_application(
        update: Update, context: CallbackContext,
) -> None:
    """Обработка ответов пользователя и отправка следующего вопроса."""
    user = update.message.from_user
    if 'answers' not in context.user_data:
        context.user_data['answers'] = []
    context.user_data['answers'].append(update.message.text)
    await update.message.reply_text(f'{user.first_name}, ваш ответ принят.')

    current_question_index = context.user_data.get('current_question', 0)
    questions = context.user_data.get('questions', [])
    context.user_data['current_question'] = current_question_index + 1
    next_question_index = context.user_data['current_question']

    if next_question_index < len(questions):
        await update.message.reply_text(
            questions[next_question_index]['question'],
        )
    else:
        await update.message.reply_text(
            f'Спасибо за ваши ответы, {user.first_name}.'
            'Мы начали обработку вашей заявки.',
        )
        async with get_async_db_session() as session:
            application = Application(
                user_id=user.id, status_id=1,
                answers="; ".join(context.user_data['answers']),
            )
            session.add(application)
            await session.commit()
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text='Новая заявка получена',
        )


async def error_handler(update: Update, context: CallbackContext) -> None:
    """Логирование ошибок, возникших во время обработки обновлений."""
    logger.error(f"Update {update} caused error {context.error}")


def init_bot() -> TelegramApplication:
    """Инициализация Telegram бота."""
    application = TelegramApplication.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(
        filters.Regex('^Начать$'), handle_start_button),
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, process_application),
    )
    application.add_error_handler(error_handler)  # Обработчик ошибок
    return application


if __name__ == '__main__':
    logging.info("Запуск Telegram бота.")
    bot = init_bot()
    bot.run_polling()
