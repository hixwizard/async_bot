from bot import BotHandler
from config import BOT_TOKEN
from telegram import Update
from telegram.ext import (
    Application as TelegramApplication,
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)


def init_bot() -> TelegramApplication:
    """Инициализирует и настраивает Telegram-бота."""
    application = TelegramApplication.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler(
        "start", BotHandler.start))
    application.add_handler(
        CommandHandler(
            "my_applications", BotHandler.handle_my_applications))
    application.add_handler(
        MessageHandler(filters.Regex(
            '^Создать заявку$'), BotHandler.handle_start_button))
    application.add_handler(
        MessageHandler(filters.Regex(
            '^Мои заявки$'), BotHandler.handle_my_applications))
    application.add_handler(
        MessageHandler(filters.Regex(
            '^Мой профиль$'), BotHandler.handle_my_profile))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        BotHandler.route_message_based_on_state))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        BotHandler.process_application))
    application.add_handler(
        CallbackQueryHandler(BotHandler.confirm_answers,
                             pattern="confirm_answers"))
    application.add_handler(
        CallbackQueryHandler(BotHandler.edit_answers, pattern="edit_answers"))
    application.add_handler(
        CallbackQueryHandler(BotHandler.handle_edit_choice,
                             pattern=r"edit_\d+"))
    application.add_handler(CallbackQueryHandler(
        BotHandler.handle_profile_edit_choice,
        pattern=r"edit_(name|email|phone)"))
    application.add_handler(
        CallbackQueryHandler(BotHandler.handle_edit_profile,
                             pattern="edit_profile"))

    application.add_error_handler(BotHandler.error_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    init_bot()
