class BotFlow:

    """Класс констант."""

    # Логические константы
    FIRST_QUESTION: int = 0
    NEXT_QUESTION: int = 1
    NEXT_NUMBER: int = 1
    SELECTED_FIELD: int = 1

    # Информационные сообщения
    WELCOME: str = 'Добро пожаловать! Выберите нужное действие:'
    HAVENT_QUESTIONS: str = 'Вопросы для опроса отсутствуют.'
    DEFAULT_STATUS: str = 'открыта'
    SUCCESSFUL_SAVE: str = 'Заявка успешно сохранена!'
    ASK_FOR_CONTACTS: str = 'Пожалуйста, укажите контактные данные.\nВведите ваш номер телефона или email:'# noqa
    CHOOSE_EDIT_QUESTION: str = 'Пожалуйста, выберите вопрос для редактирования:' # noqa
    CHOOSE_EDIT_OR_OK: str = 'Пожалуйста, нажмите «Подтвердить» или «Редактировать» для продолжения.'# noqa
    TAP_TO_CONTINIUE: str = 'Нажмите "Создать заявку", чтобы начать опрос.'
    HAVENT_APPLICATION: str = 'У вас нет заявок.'
    HAVENT_ANSWERS: str = 'Нет ответов для подтверждения.'
    EMPTY: str = ''
    SUCCESSFUL_EDIT: str = 'Ваши ответы подтверждены.'
    NOTHING_TO_EDIT: str = 'Нет вопросов для редактирования.'
    QUESTION_NOT_FOUND: str = 'Вопрос не найден.'
    CHOOSE_TO_EDIT: str = 'Выберите, что вы хотите редактировать: '
    PROFILE_UPDATED: str = 'Ваш профиль успешно обновлен.'
    BLOCK_MESSAGE: str = 'Вы заблокированы. Обратитесь к администратору. '
    USER_NOT_FOUND: str = 'Пользователь не найден.'
    NOT_SPECIFIED: str = 'Не задано'
    INVALID_EMAIL_FORMAT: str = "Неправильный формат email. Попробуйте снова."
    INVALID_PHONE_FORMAT: str = "Неправильный формат номера телефона. Попробуйте снова."# noqa
    UNKNOWN_FIELD_FOR_EDIT: str = "Неизвестное поле для редактирования."
    INVALID_CONTACT_FORMAT_MSG: str = "Неверный формат контактной информации. Попробуйте снова."# noqa


bot_flow = BotFlow()
