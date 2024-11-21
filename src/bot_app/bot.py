import logging

from buttons import start_keyboard
from database import get_async_db_session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from telegram import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import CallbackContext, ContextTypes

from models import AdminUser, Application, ApplicationStatus, Question, User
from constants import (
    WELCOME, HAVENT_QUESTIONS, FIRST_QUESTION, MESSAGE_NOT_FOUND,
    NEXT_QUESTION, DEFAULT_STATUS, SUCCESSFUL_SAVE, NEXT_NUMBER,
    ASK_FOR_CONTACTS, CHOOSE_EDIT_QUESTION, CHOOSE_EDIT_OR_OK,
    TAP_TO_CONTINIUE, HAVENT_APPLICATION, HAVENT_ANSWERS, EMPTY,
    SUCCESSFUL_EDIT, NOTHING_TO_EDIT, QUESTION_NOT_FOUND,
    CHOOSE_TO_EDIT, SELECTED_FIELD, PROFILE_UPDATED, BLOCK_MASSAGE,
    USER_NOT_FOUND
)


async def get_questions() -> list[dict]:
    """Получает список вопросов из базы данных."""
    async with get_async_db_session() as session:
        result = await session.execute(select(Question)
                                       .order_by(Question.number))
        questions = result.scalars().all()
        return [{'number': q.number, 'question':
                 q.question} for q in questions]


async def save_user_to_db(
        user_id: str, first_name: str, username: str,
        context: CallbackContext) -> None:
    """Сохранение пользователя в базу данных, если его еще нет."""
    async with get_async_db_session() as session:
        result = await session.execute(select(User).filter_by(id=user_id))
        user = result.scalars().first()

        if not user:
            new_user = User(
                id=user_id, name=first_name, email=None,
                phone=None, is_blocked=False,
            )
            session.add(new_user)
            await session.commit()
            user = new_user

        context.user_data['is_blocked'] = user.is_blocked


async def start(update: Update, context: CallbackContext) -> None:
    """Отправка приветственного сообщения и сохранение пользователя."""
    user_id = str(update.message.from_user.id)
    first_name = update.message.from_user.first_name
    username = update.message.from_user.username
    await save_user_to_db(user_id, first_name, username, context)
    reply_markup = start_keyboard()
    await update.message.reply_text(
        WELCOME,
        reply_markup=reply_markup,
    )


def reset_application_data(context: CallbackContext) -> None:
    """Очищает данные текущей заявки из user_data."""
    context.user_data.pop('answers', None)
    context.user_data.pop('current_question', None)
    context.user_data.pop('questions', None)
    context.user_data.pop('started', None)
    context.user_data.pop('awaiting_contact', None)
    context.user_data.pop('awaiting_confirmation', None)
    context.user_data.pop('editing_question', None)
    context.user_data.pop('answers_str', None)
    context.user_data.pop('survey_completed', None)


async def handle_start_button(
        update: Update, context: CallbackContext) -> None:
    """Обработка нажатия кнопки 'Создать заявку' и запуск первого вопроса."""
    context.user_data["is_editing_profile"] = False

    reset_application_data(context)
    user_id = str(update.message.from_user.id)

    if await check_user_blocked(user_id, context):
        message = await generate_message_for_blocked_user()
        await update.message.reply_text(message)
        return

    questions = await get_questions()
    if questions:
        context.user_data['answers'] = []
        context.user_data['current_question'] = FIRST_QUESTION
        context.user_data['questions'] = questions
        context.user_data['started'] = True
        await update.message.reply_text(questions[FIRST_QUESTION]['question'])
    else:
        await update.message.reply_text(HAVENT_QUESTIONS)


async def process_application(
        update: Update, context: CallbackContext) -> None:
    """Сохраняет ответ пользователя и переходит к следующему вопросу."""
    if 'answers' not in context.user_data:
        context.user_data['answers'] = []
    if update.message:
        context.user_data['answers'].append(update.message.text)
    else:
        await update.message.reply_text(MESSAGE_NOT_FOUND)
        return

    context.user_data['current_question'] += NEXT_QUESTION
    await ask_next_question(update, context)


async def save_application_to_db(query: CallbackQuery,
                                 context: CallbackContext,
                                 answers: str) -> None:
    """Финальное сохранение заявки в базе данных."""
    user_id = str(query.from_user.id)

    async with get_async_db_session() as session:
        result = await session.execute(
            select(ApplicationStatus).filter_by(status=DEFAULT_STATUS),
        )
        status = result.scalars().first() or ApplicationStatus(
            status=DEFAULT_STATUS)
        if not status.id:
            session.add(status)
            await session.commit()

        application = Application(
            user_id=user_id,
            status_id=status.id,
            answers=answers,
        )
        session.add(application)
        await session.commit()

    await query.message.reply_text(SUCCESSFUL_SAVE)


async def handle_contact_info(
        update: Update, context: CallbackContext) -> None:
    """Обработка контактной информации пользователя и завершение заявки."""
    user_id = str(update.message.from_user.id)
    if await check_user_blocked(user_id, context):
        message = await generate_message_for_blocked_user()
        await update.message.reply_text(message)
        return

    if not context.user_data.get('awaiting_contact'):
        return

    contact_info = update.message.text

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

    await finalize_application(update, context)


async def finalize_application(
        update: Update, context: CallbackContext) -> None:
    """Сохраняет заявку после получения контактной информации."""
    user_id = str(update.effective_user.id)
    answers_str = context.user_data.get('answers_str', '')

    async with get_async_db_session() as session:
        result = await session.execute(
            select(ApplicationStatus).filter_by(status=DEFAULT_STATUS),
        )
        status = result.scalars().first() or ApplicationStatus(
            status=DEFAULT_STATUS)
        if not status.id:
            session.add(status)
            await session.commit()

        result = await session.execute(
            select(Application).filter_by(user_id=user_id),
        )
        total_applications = result.scalars().all()
        application_number = len(total_applications) + NEXT_QUESTION

        application = Application(
            user_id=user_id,
            status_id=status.id,
            answers=answers_str,
        )
        session.add(application)
        await session.commit()

    await update.effective_chat.send_message(
        f"{SUCCESSFUL_SAVE} Номер вашей заявки:{application_number}",
    )
    context.user_data['survey_completed'] = True
    context.user_data['awaiting_contact'] = False


async def ask_for_contact_info(
        update: Update, context: CallbackContext) -> None:
    """Запрашивает у пользователя номер тел. или email после подтверждения."""
    user_id = str(update.effective_user.id)

    async with get_async_db_session() as session:
        result = await session.execute(select(User).filter_by(id=user_id))
        user_record = result.scalars().first()

        if user_record and (user_record.email or user_record.phone):
            await finalize_application(update, context)
        else:
            await update.effective_chat.send_message(ASK_FOR_CONTACTS,)
            context.user_data['awaiting_contact'] = True


async def handle_question_response(
        update: Update, context: CallbackContext) -> None:
    """Обрабатывает ответ пользователя на вопрос."""
    user_id = str(update.message.from_user.id)
    if context.user_data.get('survey_completed', False):
        return

    if await check_user_blocked(user_id, context):
        message = await generate_message_for_blocked_user()
        await update.message.reply_text(message)
        return

    if context.user_data.get('awaiting_edit_selection', False):
        await update.message.reply_text(CHOOSE_EDIT_QUESTION,)
        return

    if context.user_data.get('awaiting_confirmation', False):
        await update.message.reply_text(CHOOSE_EDIT_OR_OK,)
        return

    if 'editing_question' in context.user_data:
        question_number = context.user_data.pop('editing_question')
        answers = context.user_data.get('answers', [])
        answers[question_number - NEXT_NUMBER] = update.message.text
        context.user_data['answers'] = answers

        await summarize_answers(update, context)
        return

    if context.user_data.get('awaiting_contact', False):
        await handle_contact_info(update, context)
        return

    if 'current_question' in context.user_data:
        question_index = context.user_data['current_question']
        questions = context.user_data['questions']
        if question_index < len(questions):
            await process_application(update, context)
        else:
            await ask_for_contact_info(update, context)
    else:
        await update.message.reply_text(TAP_TO_CONTINIUE,)


async def error_handler(update: Update, context: CallbackContext) -> None:
    """Обрабатывает ошибки, возникающие при обработке обновлений Telegram."""
    logging.error(f"Обновление {update} вызвало исключение {context.error}")


async def handle_my_applications(
        update: Update, context: CallbackContext) -> None:
    """Обрабатывает запрос на просмотр заявок пользователя."""
    user_id = str(update.message.from_user.id)

    if await check_user_blocked(user_id, context):
        message = await generate_message_for_blocked_user()
        await update.message.reply_text(message)
        return

    applications_text = "Ваши заявки:\n"

    async with get_async_db_session() as session:
        result = await session.execute(
            select(Application)
            .filter_by(user_id=user_id)
            .options(selectinload(Application.status)),
        )
        applications = result.scalars().all()

        if not applications:
            await update.message.reply_text(HAVENT_APPLICATION)
            return

        for index, app in enumerate(applications, start=1):
            applications_text += (f"Номер: {index}\n"
                                  f"Статус: {app.status.status}\n\n")

        await update.message.reply_text(applications_text)


async def summarize_answers(update: Update, context: CallbackContext) -> None:
    """Показывает сводку ответов пользователя и запрашивает подтверждение."""
    questions = context.user_data.get('questions', [])
    answers = context.user_data.get('answers', [])

    if not questions or not answers:
        await update.message.reply_text(HAVENT_ANSWERS)
        return

    summary_text = "Проверьте свои ответы:\n\n"
    for idx, question in enumerate(questions):
        answer = answers[idx] if idx < len(answers) else ''
        summary_text += (f"{question['number']}. {question['question']}\n"
                         f"Ответ: {answer}\n\n")

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "✅ Подтвердить", callback_data="confirm_answers")],
        [InlineKeyboardButton(
            "✏️ Редактировать", callback_data="edit_answers")],
    ])

    await update.message.reply_text(summary_text, reply_markup=reply_markup)

    context.user_data['awaiting_confirmation'] = True


async def confirm_answers(update: Update, context: CallbackContext) -> None:
    """Подтверждает ответы, запрашивает контактные данные."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(SUCCESSFUL_EDIT)

    questions = context.user_data.get('questions', [])
    answers = context.user_data.get('answers', [])
    answers_str = "\n".join(
        f"{q['number']}. {q['question']}\nОтвет: {a}\n"
        for q, a in zip(questions, answers)
    )

    context.user_data['awaiting_confirmation'] = False
    context.user_data['awaiting_contact'] = True
    context.user_data['answers_str'] = answers_str
    await ask_for_contact_info(update, context)


async def edit_answers(update: Update, context: CallbackContext) -> None:
    """Отображает список вопросов для редактирования."""
    query = update.callback_query
    await query.answer()

    context.user_data['awaiting_edit_selection'] = True
    context.user_data['awaiting_confirmation'] = False

    questions = context.user_data.get('questions', [])
    if not questions:
        await query.edit_message_text(NOTHING_TO_EDIT)
        return

    buttons = [
        [InlineKeyboardButton(f"{q['number']}. {q['question']}",
                              callback_data=f"edit_{q['number']}")]
        for q in questions
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    await query.edit_message_text(CHOOSE_EDIT_QUESTION,
                                  reply_markup=reply_markup)


async def ask_next_question(update: Update, context: CallbackContext) -> None:
    """Выдаёт следующий вопрос из списка или показывает сводку."""
    current_question_index = context.user_data.get(
        'current_question', FIRST_QUESTION
    )
    questions = context.user_data.get('questions', [])

    if current_question_index < len(questions):
        question_text = questions[current_question_index]['question']
        chat_id = update.effective_chat.id

        await context.bot.send_message(chat_id=chat_id, text=question_text)
    else:
        await summarize_answers(update, context)


async def handle_edit_choice(update: Update, context: CallbackContext) -> None:
    """Управляет выбором пользователем того, какой вопрос редактировать."""
    query = update.callback_query
    await query.answer()

    question_number = int(query.data.split('_')[SELECTED_FIELD])
    questions = context.user_data.get('questions', [])
    question = next((q for q in questions if q['number'] ==
                     question_number), None)

    if question:
        context.user_data['awaiting_edit_selection'] = False
        context.user_data['editing_question'] = question_number
        await query.edit_message_text(f"Редактируйте ответ на вопрос: "
                                      f"{question['question']}")
    else:
        await query.edit_message_text(QUESTION_NOT_FOUND)


async def check_user_blocked(user_id: str, context: CallbackContext) -> bool:
    """Проверяет, заблокирован ли пользователь."""
    async with get_async_db_session() as session:
        result = await session.execute(select(User).filter_by(id=user_id))
        user = result.scalars().first()
        context.user_data['is_blocked'] = user.is_blocked
    return context.user_data['is_blocked']


async def handle_my_profile(update: Update, context: CallbackContext) -> None:
    """Отображает профиль пользователя с кнопкой для редактирования."""
    user_id = str(update.message.from_user.id)
    if await check_user_blocked(user_id, context):
        message = await generate_message_for_blocked_user()
        await update.message.reply_text(message)
        return
    async with get_async_db_session() as session:
        result = await session.execute(select(User).filter_by(id=user_id))
        user = result.scalars().first()

        if not user:
            await update.message.reply_text(USER_NOT_FOUND)
            return

        profile_text = (f"Ваш профиль:\n\n"
                        f"Имя: {user.name}\n"
                        f"Email: {user.email or EMPTY}\n"
                        f"Телефон: {user.phone or EMPTY}\n\n")

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ Редактировать",
                                  callback_data="edit_profile")],
        ])

        await update.message.reply_text(profile_text,
                                        reply_markup=reply_markup)


async def handle_edit_profile(update: Update,
                              context: CallbackContext) -> None:
    """Отображает кнопки для выбора поля редактирования профиля."""
    query = update.callback_query
    await query.answer()

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Имя", callback_data="edit_name")],
        [InlineKeyboardButton("Email", callback_data="edit_email")],
        [InlineKeyboardButton("Телефон", callback_data="edit_phone")],
    ])

    await query.edit_message_text(CHOOSE_TO_EDIT,
                                  reply_markup=reply_markup)


async def handle_profile_edit_choice(update: Update,
                                     context: CallbackContext) -> None:
    """Обрабатывает выбор редактирования профиля."""
    query = update.callback_query
    await query.answer()
    edit_choice = query.data.split('_')[SELECTED_FIELD]
    context.user_data['edit_choice'] = edit_choice

    if edit_choice == 'name':
        await query.edit_message_text("Введите Имя:")
    elif edit_choice == 'email':
        await query.edit_message_text("Введите email:")
    elif edit_choice == 'phone':
        await query.edit_message_text("Введите телефон:")


async def handle_profile_update(update: Update,
                                context: CallbackContext) -> None:
    """Обрабатывает обновление контактной информации пользователя."""
    if 'edit_choice' not in context.user_data:
        return

    user_id = str(update.message.from_user.id)
    new_value = update.message.text
    edit_choice = context.user_data.get('edit_choice')

    async with get_async_db_session() as session:
        result = await session.execute(select(User).filter_by(id=user_id))
        user = result.scalars().first()

        if not user:
            await update.message.reply_text(USER_NOT_FOUND)
            return

        if edit_choice == 'name':
            user.name = new_value
        elif edit_choice == 'email':
            user.email = new_value
        elif edit_choice == 'phone':
            user.phone = new_value

        await session.commit()

    await update.message.reply_text(PROFILE_UPDATED)
    context.user_data.pop('edit_choice', None)


async def route_message_based_on_state(update: Update,
                                       context: ContextTypes.DEFAULT_TYPE,
                                       ) -> None:
    """Вызывается обработчик в зависимости от состояния пользователя."""
    user_data = context.user_data

    if user_data.get("edit_choice"):
        await handle_profile_update(update, context)
    else:
        await handle_question_response(update, context)


async def generate_message_for_blocked_user() -> str:
    """Генерирует сообщение для заблокированного пользователя."""
    admin_email = None
    try:
        async with get_async_db_session() as session:
            result = await session.execute(
                select(AdminUser.email).where(AdminUser.role == 'admin'),
            )
            admin_email = result.scalars().first()
        if admin_email:
            return (f'{BLOCK_MASSAGE} {admin_email}')
        return BLOCK_MASSAGE

    except SQLAlchemyError as e:
        logging.error(f'Ошибка при выполнении запроса к БД: {e}')
        return BLOCK_MASSAGE
