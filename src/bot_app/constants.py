class BotFlow:

    """Класс констант."""

    # Логические константы
    FIRST_QUESTION: int = 0
    NEXT_NUMBER: int = 1
    NEXT_QUESTION: int = 1
    SELECTED_FIELD: int = 1

    # Информационные сообщения
    ANSWER_LABEL: str = "Ответ"
    APPLICATION_NUMBER: str = "Номер"
    APPLICATION_NUMBER_TEXT: str = "Номер вашей заявки:"
    APPLICATION_STATUS: str = "Статус"
    APPLICATIONS_HEADER: str = "Ваши заявки:\n"
    ASK_FOR_CONTACTS: str = 'Пожалуйста, укажите контактные данные.\nВведите ваш номер телефона или email:'# noqa
    BLOCK_MESSAGE: str = 'Вы заблокированы. Обратитесь к администратору. '
    CHECK_ANSWERS_HEADER: str = "Проверьте свои ответы:"
    CHOOSE_EDIT_OR_OK: str = 'Пожалуйста, нажмите «Подтвердить» или «Редактировать» для продолжения.'# noqa
    CHOOSE_EDIT_QUESTION: str = 'Пожалуйста, выберите вопрос для редактирования:' # noqa
    CHOOSE_TO_EDIT: str = 'Выберите, что вы хотите редактировать: '
    CONFIRM_BUTTON_TEXT: str = "✅ Подтвердить"
    DEFAULT_STATUS: str = 'открыта'
    EDIT_BUTTON_TEXT: str = "✏️ Редактировать"
    EDIT_RESPONSE: str = "Редактируйте ответ на вопрос: "
    EMAIL: str = "Email"
    EMPTY: str = ''
    HAVENT_ANSWERS: str = 'Нет ответов для подтверждения.'
    HAVENT_APPLICATION: str = 'У вас нет заявок.'
    HAVENT_QUESTIONS: str = 'Вопросы для опроса отсутствуют.'
    INPUT_EMAIL: str = "Введите email:"
    INPUT_NAME: str = "Введите Имя:"
    INPUT_PHONE: str = "Введите телефон:"
    INVALID_CONTACT_FORMAT_MSG: str = "Неверный формат контактной информации. Попробуйте снова."# noqa
    INVALID_EMAIL_FORMAT: str = "Неправильный формат email. Попробуйте снова."
    INVALID_PHONE_FORMAT: str = "Неправильный формат номера телефона. Попробуйте снова."# noqa
    INVALID_RESPONSE_MESSAGE: str = "Ответ должен содержать хотя бы 5 слов!"# noqa
    NAME: str = "Имя"
    NOTHING_TO_EDIT: str = 'Нет вопросов для редактирования.'
    NOT_SPECIFIED: str = 'Не задано'
    PHONE: str = "Телефон"
    PROFILE_HEADER: str = "Ваш профиль"
    PROFILE_UPDATED: str = 'Ваш профиль успешно обновлен.'
    QUESTION_NOT_FOUND: str = 'Вопрос не найден.'
    SUCCESSFUL_EDIT: str = 'Ваши ответы подтверждены.'
    SUCCESSFUL_SAVE: str = 'Заявка успешно сохранена!'
    TAP_TO_CONTINIUE: str = 'Нажмите "Создать заявку", чтобы начать опрос.'
    UNKNOWN_FIELD_FOR_EDIT: str = "Неизвестное поле для редактирования."
    USER_NOT_FOUND: str = 'Пользователь не найден.'
    WELCOME: str = 'Добро пожаловать! Выберите нужное действие:'

    # Ошибки
    DB_QUERY_ERROR_MESSAGE: str = "Ошибка при выполнении запроса к БД"
    ERROR_HANDLER_MESSAGE: str = "Обновление {update} вызвало исключение {error}"# noqa
    SAVE_APPLICATION_ERROR: str = "Ошибка при сохранении заявки в базу данных"
    SAVE_APPLICATION_ERROR_MESSAGE: str = "Ошибка при сохранении заявки в базу данных"# noqa
    SAVE_USER_ERROR: str = "Ошибка при сохранении пользователя в базу данных"


bot_flow = BotFlow()
