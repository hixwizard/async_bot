from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)


def start_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает клавиатуру с кнопками 'Создать заявку' и 'Мои заявки'."""
    keyboard = [['Создать заявку', 'Мои заявки']]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)


def contact_keyboard() -> InlineKeyboardMarkup:
    """Создает кнопку для начала нового опроса."""
    keyboard = [[InlineKeyboardButton("Да",
                                      callback_data="start_survey")]]
    return InlineKeyboardMarkup(keyboard)
