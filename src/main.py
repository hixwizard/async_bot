from database import get_async_db_session
from flask import Response, jsonify
from sqlalchemy.future import select
from telegram import Update
from telegram.ext import CallbackContext

from models import Application, Question

ADMIN_CHAT_ID = '123'


async def get_questions()-> Response:
    """Json в качестве списка вопросов."""
    async with get_async_db_session() as session:
        result = await session.execute(
            select(Question).order_by(Question.number),
        )
        questions = result.scalars().all()
        return jsonify(
            [{'number': q.number, 'question': q.question} for q in questions],
        )


async def start(update: Update, context: CallbackContext) -> None:
    """Отправляет приветственное сообщение и первый вопрос."""
    questions = await get_questions()

    await update.message.reply_text(
        'Добро пожаловать! Мы начнем с нескольких вопросов.',
    )

    await update.message.reply_text(questions[0]['question'])

    context.user_data['questions'] = questions
    context.user_data['current_question'] = 0


async def process_application(update: Update, context: CallbackContext)-> None:
    """Обрабатывает ответы пользователя и отправляет следующий вопрос."""
    user = update.message.from_user
    # Сохраняем ответ пользователя в контексте
    if 'answers' not in context.user_data:
        context.user_data['answers'] = []
    context.user_data['answers'].append(update.message.text)

    # Уведомляем пользователя о получении ответа
    await update.message.reply_text(
        f'{user.name}, ваш ответ принят')

    # Получаем текущий индекс вопроса
    current_question_index = context.user_data.get('current_question', 0)
    questions = context.user_data.get('questions', [])

    # Переходим к следующему вопросу
    context.user_data['current_question'] = current_question_index + 1
    next_question_index = context.user_data['current_question']

    # Если есть следующий вопрос, отправляем его
    if next_question_index < len(questions):
        await update.message.reply_text(
            questions[next_question_index]['question'],
        )
    else:
        await update.message.reply_text(
            f'Спасибо за ваши ответы, {user.name}. '
            'Мы начали обработку вашей заявки.',
        )

        async with get_async_db_session() as session:
            application = Application(
                user_id=user.id,
                status_id=1,
                answers="; ".join(context.user_data['answers']),
            )
            session.add(application)
            await session.commit()

        # Отправляем уведомление админу
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID, text="Новая заявка получена",
        )
