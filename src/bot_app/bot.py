import asyncio
import re

from buttons import start_keyboard
from constants import bot_flow
from database import get_async_db_session
from logger import bot_logger
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

logger = bot_logger()


class UserManager:

    """Класс для управления пользователями."""

    @staticmethod
    async def save_user_to_db(
            user_id: str, first_name: str, username: str,
            context: CallbackContext) -> None:
        """Сохраняет пользователя в базу данных."""
        try:
            async with get_async_db_session() as session:
                result = await session.execute(select(User).filter_by(
                    id=user_id))
                user = result.scalars().first()

                if not user:
                    new_user = User(id=user_id, name=first_name, email=None,
                                    phone=None, is_blocked=False)
                    session.add(new_user)
                    await session.commit()
                    user = new_user

                context.user_data['is_blocked'] = user.is_blocked

        except (SQLAlchemyError, ValueError, asyncio.TimeoutError) as e:
            logger.error(f"{bot_flow.SAVE_USER_ERROR}: {e}")
            raise

    @staticmethod
    async def check_user_blocked(
            user_id: str, context: CallbackContext) -> bool:
        """Проверяет, заблокирован ли пользователь."""
        async with get_async_db_session() as session:
            result = await session.execute(select(User).filter_by(id=user_id))
            user = result.scalars().first()
            context.user_data['is_blocked'] = user.is_blocked
        return context.user_data['is_blocked']

    @staticmethod
    async def handle_profile_update(
            update: Update, context: CallbackContext) -> None:
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
                await update.message.reply_text(
                    bot_flow.USER_NOT_FOUND)
                return

            match edit_choice:
                case 'name':
                    user.name = new_value
                case 'email':
                    if not Validator.is_valid_email(new_value):
                        await update.message.reply_text(
                            bot_flow.INVALID_EMAIL_FORMAT)
                        return
                    user.email = new_value
                case 'phone':
                    if not Validator.is_valid_phone(new_value):
                        await update.message.reply_text(
                            bot_flow.INVALID_PHONE_FORMAT)
                        return
                    user.phone = new_value
                case _:
                    await update.message.reply_text(
                        bot_flow.UNKNOWN_FIELD_FOR_EDIT)
                    return

            await session.commit()

        await update.message.reply_text(bot_flow.PROFILE_UPDATED)
        context.user_data.pop('edit_choice', None)


class ApplicationManager:

    """Класс для управления заявками."""

    @staticmethod
    async def get_questions() -> list[dict]:
        """Получает список вопросов из базы данных."""
        async with get_async_db_session() as session:
            result = await session.execute(select(Question).order_by(
                Question.number))
            questions = result.scalars().all()
            return [{'number': q.number, 'question': q.question} for q
                    in questions]

    @staticmethod
    def reset_application_data(context: CallbackContext) -> None:
        """Сбрасывает данные заявки в контексте пользователя."""
        keys_to_delete = [
            'answers', 'current_question', 'questions', 'started',
            'awaiting_contact', 'awaiting_confirmation',
            'editing_question', 'answers_str', 'survey_completed',
        ]
        for key in keys_to_delete:
            context.user_data.pop(key, None)

    @staticmethod
    async def save_application_to_db(
            query: CallbackQuery, context: CallbackContext,
            answers: str) -> None:
        """Сохраняет заявку в базу данных."""
        user_id = str(query.from_user.id)
        try:
            async with get_async_db_session() as session:
                result = await session.execute(select(
                    ApplicationStatus).filter_by(
                    status=bot_flow.DEFAULT_STATUS))
                status = result.scalars().first() or ApplicationStatus(
                    status=bot_flow.DEFAULT_STATUS)
                if not status.id:
                    session.add(status)
                    await session.commit()

                application = Application(user_id=user_id,
                                          status_id=status.id, answers=answers)
                session.add(application)
                await session.commit()

            await query.message.reply_text(bot_flow.SUCCESSFUL_SAVE)

        except (SQLAlchemyError, ValueError, asyncio.TimeoutError,
                AttributeError) as e:
            logger.error(f"{bot_flow.SAVE_APPLICATION_ERROR}: {e}")
            raise

    @staticmethod
    async def handle_contact_info(
            update: Update, context: CallbackContext) -> None:
        """Обрабатывает контактную информацию пользователя."""
        user_id = str(update.message.from_user.id)
        if await UserManager.check_user_blocked(user_id, context):
            message = await BotHandler.generate_message_for_blocked_user()
            await update.message.reply_text(message)
            return

        if not context.user_data.get('awaiting_contact'):
            return

        contact_info = update.message.text

        async with get_async_db_session() as session:
            result = await session.execute(select(User).filter_by(id=user_id))
            user_record = result.scalars().first()

            if user_record:
                match contact_info:
                    case email if Validator.is_valid_email(email):
                        user_record.email = email
                    case phone if Validator.is_valid_phone(phone):
                        user_record.phone = phone
                    case _:
                        await update.message.reply_text(
                            bot_flow.INVALID_CONTACT_FORMAT_MSG)
                        return

                await session.commit()

        context.user_data['awaiting_contact'] = False
        await ApplicationManager.finalize_application(update, context)

    @staticmethod
    async def finalize_application(
            update: Update, context: CallbackContext) -> None:
        """Завершает заявку и сохраняет её в базу данных."""
        user_id = str(update.effective_user.id)
        answers_str = context.user_data.get('answers_str', '')
        try:
            async with get_async_db_session() as session:
                result = await session.execute(select(
                    ApplicationStatus).filter_by(
                    status=bot_flow.DEFAULT_STATUS))
                status = result.scalars().first() or ApplicationStatus(
                    status=bot_flow.DEFAULT_STATUS)
                if not status.id:
                    session.add(status)
                    await session.commit()

                result = await session.execute(select(Application).filter_by(
                    user_id=user_id))
                total_applications = result.scalars().all()
                application_number = len(
                    total_applications) + bot_flow.NEXT_QUESTION

                application = Application(user_id=user_id, status_id=status.id,
                                          answers=answers_str)
                session.add(application)
                await session.commit()

            await update.effective_chat.send_message(
                f"{bot_flow.SUCCESSFUL_SAVE} "
                f"{bot_flow.APPLICATION_NUMBER_TEXT} {application_number}",
            )
            context.user_data['survey_completed'] = True
            context.user_data['awaiting_contact'] = False

        except (SQLAlchemyError, ValueError, asyncio.TimeoutError,
                AttributeError) as e:
            logger.error(f"{bot_flow.SAVE_APPLICATION_ERROR_MESSAGE}: {e}")
            raise

    @staticmethod
    async def summarize_answers(
            update: Update, context: CallbackContext) -> None:
        """Суммирует ответы пользователя и отображает их для подтверждения."""
        questions = context.user_data.get('questions', [])
        answers = context.user_data.get('answers', [])

        if not questions or not answers:
            await update.message.reply_text(bot_flow.HAVENT_ANSWERS)
            return

        summary_text = f"{bot_flow.CHECK_ANSWERS_HEADER}\n\n"
        for idx, question in enumerate(questions):
            answer = answers[idx] if idx < len(answers) else bot_flow.EMPTY
            summary_text += (f"{question['number']}. "
                             f"{question['question']}\n"
                             f"{bot_flow.ANSWER_LABEL}: {answer}\n\n")

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(bot_flow.CONFIRM_BUTTON_TEXT,
                                  callback_data="confirm_answers")],
            [InlineKeyboardButton(bot_flow.EDIT_BUTTON_TEXT,
                                  callback_data="edit_answers")],
        ])

        await update.message.reply_text(summary_text,
                                        reply_markup=reply_markup)
        context.user_data['awaiting_confirmation'] = True

    @staticmethod
    async def ask_next_question(
            update: Update, context: CallbackContext) -> None:
        """Задает следующий вопрос пользователю."""
        current_question_index = context.user_data.get('current_question',
                                                       bot_flow.FIRST_QUESTION)
        questions = context.user_data.get('questions', [])

        if current_question_index < len(questions):
            question_text = questions[current_question_index]['question']
            chat_id = update.effective_chat.id
            await context.bot.send_message(chat_id=chat_id, text=question_text)
        else:
            await ApplicationManager.summarize_answers(update, context)


class BotHandler:

    """Класс для обработки взаимодействий с ботом."""

    @staticmethod
    async def start(update: Update, context: CallbackContext) -> None:
        """Обрабатывает команду /start."""
        user_id = str(update.message.from_user.id)
        first_name = update.message.from_user.first_name
        username = update.message.from_user.username
        await UserManager.save_user_to_db(user_id, first_name, username,
                                          context)
        reply_markup = start_keyboard()
        await update.message.reply_text(bot_flow.WELCOME,
                                        reply_markup=reply_markup)

    @staticmethod
    def reset_profile_editing(context: CallbackContext) -> None:
        """Сбрасывает состояние редактирования профиля."""
        context.user_data.pop('edit_choice', None)

    @staticmethod
    async def handle_start_button(
            update: Update, context: CallbackContext) -> None:
        """Обрабатывает нажатие кнопки "Начать"."""
        BotHandler.reset_profile_editing(context)
        context.user_data["is_editing_profile"] = False
        ApplicationManager.reset_application_data(context)
        user_id = str(update.message.from_user.id)

        if await UserManager.check_user_blocked(user_id, context):
            message = await BotHandler.generate_message_for_blocked_user()
            await update.message.reply_text(message)
            return

        questions = await ApplicationManager.get_questions()
        if questions:
            context.user_data['answers'] = []
            context.user_data['current_question'] = bot_flow.FIRST_QUESTION
            context.user_data['questions'] = questions
            context.user_data['started'] = True
            await update.message.reply_text(
                questions[bot_flow.FIRST_QUESTION]['question'])
        else:
            await update.message.reply_text(bot_flow.HAVENT_QUESTIONS)

    @staticmethod
    async def handle_my_applications(
            update: Update, context: CallbackContext) -> None:
        """Обрабатывает запрос на просмотр заявок пользователя."""
        BotHandler.reset_profile_editing(context)
        user_id = str(update.message.from_user.id)

        if await UserManager.check_user_blocked(user_id, context):
            message = await BotHandler.generate_message_for_blocked_user()
            await update.message.reply_text(message)
            return

        async with get_async_db_session() as session:
            result = await session.execute(
                select(Application)
                .filter_by(user_id=user_id)
                .options(selectinload(Application.status)),
            )
            applications = result.scalars().all()

        match applications:
            case []:
                await update.message.reply_text(bot_flow.HAVENT_APPLICATION)
            case _:
                applications_text = bot_flow.APPLICATIONS_HEADER
                for index, app in enumerate(applications,
                                            start=bot_flow.NEXT_QUESTION):
                    applications_text += (f"{bot_flow.APPLICATION_NUMBER}: "
                                          f"{index}\n"
                                          f"{bot_flow.APPLICATION_STATUS}: "
                                          f"{app.status.status}\n\n")
                await update.message.reply_text(applications_text)

    @staticmethod
    async def handle_my_profile(
            update: Update, context: CallbackContext) -> None:
        """Отображает профиль пользователя с кнопкой для редактирования."""
        BotHandler.reset_profile_editing(context)
        user_id = str(update.message.from_user.id)
        if await UserManager.check_user_blocked(user_id, context):
            message = await BotHandler.generate_message_for_blocked_user()
            await update.message.reply_text(message)
            return
        async with get_async_db_session() as session:
            result = await session.execute(select(User).filter_by(id=user_id))
            user = result.scalars().first()

            if not user:
                await update.message.reply_text(bot_flow.USER_NOT_FOUND)
                return

            profile_text = (f"{bot_flow.PROFILE_HEADER}:\n\n"
                            f"{bot_flow.NAME}: {user.name}\n"
                            f"{bot_flow.EMAIL}: "
                            f"{user.email or bot_flow.NOT_SPECIFIED}\n"
                            f"{bot_flow.PHONE}: "
                            f"{user.phone or bot_flow.NOT_SPECIFIED}\n\n")

            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(bot_flow.EDIT_BUTTON_TEXT,
                                      callback_data="edit_profile")],
            ])

            await update.message.reply_text(profile_text,
                                            reply_markup=reply_markup)

    @staticmethod
    async def ask_for_contact_info(
            update: Update, context: CallbackContext) -> None:
        """Запрашивает номер телефона или email после подтверждения."""
        user_id = str(update.effective_user.id)

        async with get_async_db_session() as session:
            result = await session.execute(select(User).filter_by(id=user_id))
            user_record = result.scalars().first()

            match user_record:
                case None:
                    await update.effective_chat.send_message(
                        bot_flow.USER_NOT_FOUND)
                    return
                case _ if user_record.email or user_record.phone:
                    await ApplicationManager.finalize_application(
                        update, context)
                case _:
                    await update.effective_chat.send_message(
                        bot_flow.ASK_FOR_CONTACTS)
                    context.user_data['awaiting_contact'] = True

    @staticmethod
    async def confirm_answers(
            update: Update, context: CallbackContext) -> None:
        """Подтверждает ответы, запрашивает контактные данные."""
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(bot_flow.SUCCESSFUL_EDIT)

        questions = context.user_data.get('questions', [])
        answers = context.user_data.get('answers', [])
        answers_str = "\n".join(
            f"{q['number']}. {q['question']}\n{bot_flow.ANSWER_LABEL}: {a}\n"
            for q, a in zip(questions, answers)
        )

        context.user_data['awaiting_confirmation'] = False
        context.user_data['awaiting_contact'] = True
        context.user_data['answers_str'] = answers_str
        await BotHandler.ask_for_contact_info(update, context)

    @staticmethod
    async def edit_answers(update: Update, context: CallbackContext) -> None:
        """Отображает список вопросов для редактирования."""
        query = update.callback_query
        await query.answer()

        context.user_data['awaiting_edit_selection'] = True
        context.user_data['awaiting_confirmation'] = False

        questions = context.user_data.get('questions', [])
        if not questions:
            await query.edit_message_text(bot_flow.NOTHING_TO_EDIT)
            return

        buttons = [
            [InlineKeyboardButton(f"{q['number']}. {q['question']}",
                                  callback_data=f"edit_{q['number']}")]
            for q in questions
        ]
        reply_markup = InlineKeyboardMarkup(buttons)

        await query.edit_message_text(
            bot_flow.CHOOSE_EDIT_QUESTION, reply_markup=reply_markup)

    @staticmethod
    async def handle_edit_choice(
            update: Update, context: CallbackContext) -> None:
        """Управляет выбором пользователем того, какой вопрос редактировать."""
        query = update.callback_query
        await query.answer()

        question_number = int(query.data.split('_')[bot_flow.SELECTED_FIELD])
        questions = context.user_data.get('questions', [])
        question = next((q for q in questions
                         if q['number'] == question_number), None)

        if question:
            context.user_data['awaiting_edit_selection'] = False
            context.user_data['editing_question'] = question_number
            await query.edit_message_text(
                f"{bot_flow.EDIT_RESPONSE}{question['question']}")
        else:
            await query.edit_message_text(bot_flow.QUESTION_NOT_FOUND)

    @staticmethod
    async def handle_profile_edit_choice(
            update: Update, context: CallbackContext) -> None:
        """Обрабатывает выбор редактирования профиля."""
        query = update.callback_query
        await query.answer()
        edit_choice = query.data.split('_')[bot_flow.SELECTED_FIELD]
        context.user_data['edit_choice'] = edit_choice

        match edit_choice:
            case 'name':
                await query.edit_message_text(bot_flow.INPUT_NAME)
            case 'email':
                await query.edit_message_text(bot_flow.INPUT_EMAIL)
            case 'phone':
                await query.edit_message_text(bot_flow.INPUT_PHONE)

    @staticmethod
    async def handle_edit_profile(
            update: Update, context: CallbackContext) -> None:
        """Отображает кнопки для выбора поля редактирования профиля."""
        query = update.callback_query
        await query.answer()

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(bot_flow.NAME, callback_data="edit_name")],
            [InlineKeyboardButton(bot_flow.EMAIL, callback_data="edit_email")],
            [InlineKeyboardButton(bot_flow.PHONE, callback_data="edit_phone")],
        ])

        await query.edit_message_text(
            bot_flow.CHOOSE_TO_EDIT, reply_markup=reply_markup)

    @staticmethod
    async def error_handler(update: Update, context: CallbackContext) -> None:
        """Обрабатывает ошибки, возникающие при обработке обновлений."""
        logger.error(bot_flow.ERROR_HANDLER_MESSAGE.format(
            update=update, error=context.error))

    @staticmethod
    async def process_application(
            update: Update, context: CallbackContext) -> None:
        """Обрабатывает ответы пользователя на вопросы анкеты."""
        if 'answers' not in context.user_data:
            context.user_data['answers'] = []

        context.user_data['answers'].append(update.message.text)
        context.user_data['current_question'] += bot_flow.NEXT_QUESTION
        await ApplicationManager.ask_next_question(update, context)

    @staticmethod
    async def handle_question_response(
            update: Update, context: CallbackContext) -> None:
        """Обрабатывает ответ пользователя на вопрос."""
        user_id = str(update.message.from_user.id)

        if context.user_data.get('survey_completed', False):
            return

        if await UserManager.check_user_blocked(user_id, context):
            message = await BotHandler.generate_message_for_blocked_user()
            await update.message.reply_text(message)
            return

        text = update.message.text

        match context.user_data:
            case data if data.get('awaiting_edit_selection', False):
                await update.message.reply_text(bot_flow.CHOOSE_EDIT_QUESTION)
                return

            case data if data.get('awaiting_confirmation', False):
                await update.message.reply_text(bot_flow.CHOOSE_EDIT_OR_OK)
                return

            case data if 'editing_question' in data:
                question_number = context.user_data.pop('editing_question')
                answers = context.user_data.get('answers', [])
                answers[question_number - bot_flow.NEXT_NUMBER] = text
                context.user_data['answers'] = answers
                await ApplicationManager.summarize_answers(update, context)
                return

            case data if data.get('awaiting_contact', False):
                await ApplicationManager.handle_contact_info(update, context)
                return

            case data if 'current_question' in data:
                if not Validator.is_valid_text(text):
                    await update.message.reply_text(
                        bot_flow.INVALID_RESPONSE_MESSAGE)
                    return

                question_index = data['current_question']
                questions = data['questions']
                if question_index < len(questions):
                    await BotHandler.process_application(update, context)
                else:
                    await BotHandler.ask_for_contact_info(update, context)
                return

            case _:
                await update.message.reply_text(bot_flow.TAP_TO_CONTINIUE)

    @staticmethod
    async def route_message_based_on_state(
            update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Маршрутизирует сообщение на основе состояния пользователя."""
        user_data = context.user_data

        if user_data.get("edit_choice"):
            await UserManager.handle_profile_update(update, context)
        else:
            await BotHandler.handle_question_response(update, context)

    @staticmethod
    async def generate_message_for_blocked_user() -> str:
        """Генерирует сообщение для заблокированного пользователя."""
        admin_email = None
        try:
            async with get_async_db_session() as session:
                result = await session.execute(select(AdminUser.email).where(
                    AdminUser.role == 'admin'))
                admin_email = result.scalars().first()
            if admin_email:
                return f'{bot_flow.BLOCK_MESSAGE} {admin_email}'
            return bot_flow.BLOCK_MESSAGE

        except SQLAlchemyError as e:
            logger.error(f"{bot_flow.DB_QUERY_ERROR_MESSAGE}: {e}")
            return bot_flow.BLOCK_MESSAGE


class Validator:

    """Класс для проверки валидности данных."""

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Проверяет, является ли строка допустимым email."""
        return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        """Проверяет, является ли строка допустимым номером телефона."""
        return re.match(r"^\+?\d{10,15}$", phone) is not None

    @staticmethod
    def is_valid_text(text: str) -> bool:
        """Проверяет, что текст содержит хотя бы 5 слов и не только цифры."""
        words = text.split()
        non_numeric_words = [word for word in words if not word.isdigit()]
        return len(words) >= 5 and len(non_numeric_words) >= 5
