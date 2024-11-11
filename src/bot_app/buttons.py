from telegram import (
    ReplyKeyboardMarkup,
)


def start_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает клавиатуру с кнопками."""
    return ReplyKeyboardMarkup(
        [['Создать заявку', 'Мои заявки', 'Мой профиль']],
        one_time_keyboard=True,
        resize_keyboard=True,
    )


# def contact_keyboard() -> InlineKeyboardMarkup:
#     """Создает кнопку для начала нового опроса."""
#     return InlineKeyboardMarkup(
#         [[InlineKeyboardButton("Да", callback_data="start_survey")]],
#     )
