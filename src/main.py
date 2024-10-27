import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, List

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import Application as TelegramApplication
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from models import Application, ApplicationStatus, Question, User

load_dotenv()


ADMIN_CHAT_ID = '123'  # стоит убрать и отправлять сообщения role - operator
BOT_TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_ASYNC_URL')


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


engine = create_async_engine(DATABASE_URL, echo=True)


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
    user_id = str(update.message.from_user.id)
    first_name = update.message.from_user.first_name
    username = update.message.from_user.username
    await save_user_to_db(user_id, first_name, username)
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
    user_id = str(update.message.from_user.id)
    if 'answers' not in context.user_data:
        context.user_data['answers'] = []
    context.user_data['answers'].append(update.message.text)

    await update.message.reply_text(
        f'{update.message.from_user.first_name}, ваш ответ принят.',
    )

    current_question_index = context.user_data.get('current_question', 0)
    questions = context.user_data.get('questions', [])
    context.user_data['current_question'] = current_question_index + 1

    if context.user_data['current_question'] < len(questions):
        await update.message.reply_text(
            questions[context.user_data['current_question']]['question'],
        )
    else:
        # Завершение опроса и запрос контактной информации
        await update.message.reply_text(
            'Спасибо за ответы. Как с вами удобнее связаться, '
            'по электронной почте или телефону:',
        )
        context.user_data['awaiting_contact'] = True  # Флаг ожидания контакта

        # Сохранение заявки в базе данных
        async with get_async_db_session() as session:
            result = await session.execute(
                select(ApplicationStatus).filter_by(status='открыта'),
            )
            status = result.scalars().first() or ApplicationStatus(
                status='открыта')
            if not status.id:
                session.add(status)
                await session.commit()

            application = Application(
                user_id=user_id,
                status_id=status.id,
                answers="; ".join(context.user_data['answers']),
            )
            session.add(application)
            await session.commit()

            logger.info(
                f'Заявка от пользователя '
                f'{update.message.from_user.first_name} '
                f'со статусом "{status.status}" сохранена.',
            )


async def handle_contact_info(
        update: Update, context: CallbackContext,
) -> None:
    """Обработка контактной информации пользователя."""
    user_id = str(update.message.from_user.id)
    contact_info = update.message.contact.phone_number if (
        update.message.contact) else update.message.text

    async with get_async_db_session() as session:
        result = await session.execute(select(User).filter_by(id=user_id))
        user_record = result.scalars().first()

        if user_record:
            if "@" in contact_info:
                user_record.email = contact_info
            else:
                user_record.phone = contact_info
            await session.commit()

            context.user_data['awaiting_contact'] = False

            # Сброс данных для нового опроса
            context.user_data['answers'] = []
            context.user_data['current_question'] = 0

    keyboard = [[InlineKeyboardButton("Да", callback_data="start_survey")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        'Спасибо! Ваша контактная информация сохранена.\n'
        'Хотите начать новый опрос? Нажмите "Да" для подтверждения.',
        reply_markup=reply_markup,
    )


async def start_new_survey(update: Update, context: CallbackContext) -> None:
    """Функция для начала нового опроса после нажатия кнопки."""
    query = update.callback_query
    await query.answer()

    # Сброс ответов и параметров для нового опроса
    context.user_data['answers'] = []
    context.user_data['current_question'] = 0

    # Начинаем с первого вопроса
    questions = context.user_data.get('questions', [])
    if questions:
        await query.message.reply_text(questions[0]['question'])


async def request_contact(update: Update, context: CallbackContext) -> None:
    """Запросить у пользователя его контакт."""
    keyboard = [[
        KeyboardButton("Поделиться номером", request_contact=True),
    ], [
        KeyboardButton("Введите ваш email"),
    ]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text(
        'Пожалуйста, поделитесь своим номером телефона или введите ваш email:',
        reply_markup=reply_markup,
    )


async def handle_question_response(
        update: Update, context: CallbackContext,
) -> None:
    """Обработка ответов пользователя на вопросы."""
    if context.user_data.get('awaiting_contact', False):
        await handle_contact_info(update, context)
        return
    user = update.message.from_user
    answer = update.message.text
    logger.info(f"Ответ пользователя {user.first_name}: {answer}")
    if 'current_question' in context.user_data:
        question_index = context.user_data['current_question']
        questions = context.user_data['questions']
        if question_index < len(questions):
            await process_application(update, context)
        else:
            await update.message.reply_text(
                'Все вопросы завершены. Спасибо за участие!',
            )
    else:
        await update.message.reply_text(
            'Нажмите "Начать", чтобы начать опрос.',
        )


async def handle_message(update: Update, context: CallbackContext) -> None:
    """Обработка произвольных сообщений от пользователей."""
    message = update.message.text
    logger.info(f"Получено сообщение: {message}")
    await update.message.reply_text("Ваше сообщение получено!")


async def error_handler(update: Update, context: CallbackContext) -> None:
    """Логирование ошибок, возникших во время обработки обновлений."""
    logger.error(f"Update {update} caused error {context.error}")


def init_bot() -> TelegramApplication:
    """Инициализация Telegram бота."""
    application = TelegramApplication.builder().token(BOT_TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.Regex('^Начать$'), handle_start_button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
                                           handle_question_response))
    application.add_handler(MessageHandler(filters.ALL, handle_message))
    application.add_handler(
        CallbackQueryHandler(start_new_survey, pattern="start_survey"))

    application.add_error_handler(error_handler)
    return application


if __name__ == '__main__':
    logging.info("Запуск Telegram бота.")
    bot = init_bot()
    bot.run_polling()