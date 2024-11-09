![Build Status](https://github.com/Studio-Yandex-Practicum/Turutin_bot_team_2/actions/workflows/main.yml/badge.svg)

[Развёрнутый проект](https://turutin-team2.rsateam.ru)

Чат-бот: `@AsyncDevBot`

## Проект Turutin_bot

**Это чат-бот, который проводит вводную часть опроса клиентов, формирует заявки и ведет журнал заявок. В проекте также присутствует административный интерфейс, где операторы и администраторы могут управлять заявками.**

### Описание проекта

Цель проекта — создание бота для предоставления клиентам услуг финансового консалтинга. Бот собирает информацию через опрос и формирует заявку для дальнейшего трекинга и обработки операторами и администраторами.

### Технологии и требования

* Язык программирования: Python 3.11+
* СУБД: PostgreSQL
* Архитектура: Асинхронный код (для повышения производительности)
* ORM: SQLAlchemy, Flask-Admin
* Контейнеризация: Docker
* Стилистика: Ruff и Pre-commit

### Структура проекта

Проект включает несколько ключевых папок и файлов:

```
github/
├── workflows/
│   └── style_check.yml
infra/
├── .env.example
├── docker-compose.yml
└── docker-compose.production.yml
src/
├── admin_app/
│   ├── admin/
│   │   ├── templates/
│   │   │   └── admin/
│   │   │       ├── index.html
│   │   │       └── my_master.html
│   ├── admin.py
│   ├── admin_views.py
│   ├── cli_commands.py
│   ├── forms.py
│   ├── utils.py
│   ├── start.sh
│   └── views.py
└── bot_app/
│   ├── bot.py
│   ├── buttons.py
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   └── requirements.txt
└── init.py
├── models.py
├── .gitignore
├── .pre-commit-config.yaml
└── README.md
├── requirements_style.txt
└── ruff.toml
```

### Описание директорий

#### admin_app/

Модуль для административного интерфейса, предоставляющего функционал для операторов и администраторов:

* `admin/` — Шаблоны и базовая логика административной панели.
* `templates/admin/index.html` — Главная страница админки.
* `templates/admin/my_master.html` — Пользовательский шаблон.
* `admin.py` — Основная логика для админки.
* `admin_views.py` — Вьюхи для обработки запросов.
* `cli_commands.py` — Команды CLI для административных задач.
* `forms.py` — Формы для работы с данными.
* `utils.py` — Утилиты для вспомогательных операций.
* `views.py` — Отображения данных в админке.

##### start.sh
Этот скрипт изпользуется для старта административной зоны на Gunicorn,
используя 4 дочерних процесса. 4 человека могут параллельно работать в административной панели, расходует ресурсы сервера. (можно убрать)
Скрипт устанавливает связь с моделями приложения для миграций Alebmic.

* При первом запуске инициализарует, проводит и применяет миграции, наполняет базу данными для работы, запускает контейнер.

* При последующих запусках обновляет базу и запускает контейнер.

#### bot_app/

Модуль для функциональности бота, который обрабатывает взаимодействие с клиентами:

* `bot.py` — Основная логика работы с ботом.
* `buttons.py` — Определение кнопок для интерфейса бота.
* `config.py` — Конфигурация для бота.
* `database.py` — Модуль работы с базой данных.
* `main.py` — Запуск бота и основной функционал.
* `requirements.txt` — Зависимости для работы бота.

#### infra/

Директория для настройки окружения и развертывания проекта:

* `docker-compose.yml` — Локальная конфигурация для запуска контейнеров.
* `docker-compose.production.yml` — Конфигурация для запуска проекта в продакшн через CI/CD.
* `.env.example` — Пример переменных окружения для настройки .env.

### Запуск проекта

#### CI/CD

Для развертывания проекта через CI/CD, используйте файл `docker-compose.production.yml` в директории `infra/`. Это позволит вам автоматизировать процесс развертывания и управления проектом в облачной инфраструктуре.

#### Локальный запуск с Docker Compose

1. Скопируйте файл `.env.example` в `.env` и настройте переменные окружения.
2. Убедитесь, что в переменной `BOT_TOKEN` указан токен вашего бота.
3. Запустите проект с помощью команды: `docker compose up`
4. Для фоновго запуска используйте: `docker compose up -d`
5. Для обновления и перезапуска сети после изменений в коде: `docker compose up --build`

#### Создание суперпользователя

Для создания суперпользователя используйте команду: `docker exec -it infra-admin-1 flask create_superuser user password`

#### Запуск с Docker Compose на сервере в ручном режиме

На вашем серевере должны быть установлены Docker и Docker-compose.
При ручном запуске необходимо смотреть логи, названия компонентов docker в сети, чтобы правильно включить сеть.

1. Создайте файл `.env` в корне и настройте переменные окружения(`.env.example`).
2. Убедитесь, что в переменной `BOT_TOKEN` указан токен вашего бота.
3. Находясь в директории с файлом `.env` создайте файл `docker-compose.yml`.
4. Скопируйте содержимое `docker-compose.production.yml` в `docker-compose.yml`.
5. `docker compose up -d` - для запуска.

В `docker-compose.production.yml` прописаны все инструкции для запуска сети.
Чтобы создать администратора, необходимо выполнить комнду:
```shell
docker exec -it <имя контейнера администрирования> flask create_superuser <имя пользователя> <пароль пользователя>
```
Также можно зайти в работающий контейнер с администированием и там выполнить команду
```shell
flask create_superuser <имя пользователя> <пароль пользователя>
```

### Стилистика

Для стилизации кода используются инструменты Ruff и Pre-commit.

#### Проверка и исправление стиля

* Для проверки стилистики кода используйте команду: `ruff check`
* Для автоматического исправления ошибок: `ruff check --fix`
* Для установки pre-commit hook: `pre-commit install`

### Рекомендации

* **Миграции базы данных:** Убедитесь, что все миграции выполнены. Используйте Alembic для управления миграциями.
* **Тестирование:** Рекомендуется проводить тестирование каждого модуля перед сборкой и запуском.
* **Логирование:** Настройте логирование для диагностики и отладки.

## Состав команды
* [Данил Тищенко](https://github.com/tttriggered)
* [Александр Талбутдинов](https://github.com/Aleksandr-Talbutdinov)
* [Артем Абрамов](https://github.com/the-world-at-large)
* [Роман Кириллов](https://github.com/RoMario-aii)
* [Ильхам Кашапов](https://github.com/Ilx-k)
* [Баринов Станислав](https://github.com/hixwizard) (тимлид)
