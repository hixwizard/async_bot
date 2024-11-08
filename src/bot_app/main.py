from bot import (
    confirm_answers,
    edit_answers,
    error_handler,
    handle_contact_info,
    handle_edit_choice,
    handle_my_applications,
    handle_question_response,
    handle_start_button,
    start,
    start_new_survey,
)
from config import BOT_TOKEN
from telegram.ext import (
    Application as TelegramApplication,
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from telegram import Update


def init_bot() -> TelegramApplication:
    """Инициализирует и настраивает Telegram-бота."""
    application = TelegramApplication.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("my_applications",
                                           handle_my_applications))
    application.add_handler(MessageHandler(filters.Regex('^Создать заявку$'),
                                           handle_start_button))
    application.add_handler(MessageHandler(filters.Regex('^Мои заявки$'),
                                           handle_my_applications))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
                                           handle_question_response))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
                                           handle_contact_info))
    application.add_handler(CallbackQueryHandler(start_new_survey,
                                                 pattern="start_survey"))
    application.add_handler(CallbackQueryHandler(confirm_answers,
                                                 pattern="confirm_answers"))
    application.add_handler(CallbackQueryHandler(edit_answers,
                                                 pattern="edit_answers"))
    application.add_handler(CallbackQueryHandler(handle_edit_choice,
                                                 pattern=r"edit_\d+"))
    application.add_error_handler(error_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    init_bot()
