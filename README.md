# Шаблон для проектов со стилизатором Ruff

## Основное

1. Базовая версия Python - 3.11.
2. В файле `requirements_style.txt` находятся зависимости для стилистики.
3. В каталоге `src` находится базовая структура проекта
4. В файле `srd/requirements.txt` прописываются базовые зависимости.
5. В каталоге `infra` находятся настроечные файлы проекта. Здесь же размещать файлы для docker compose.

## Стилистика

Для стилизации кода используется пакеты `Ruff` и `Pre-commit`

Проверка стилистики кода осуществляется командой
```shell
ruff check
```

Если одновременно надо пофиксить то, что можно поиксить автоматически, то добавляем параметр `--fix`
```shell
ruff check --fix
```

Что бы стилистика автоматически проверялась и поправлялась при комитах надо добавить hook pre-commit к git

```shell
pre-commit install
```
## Запуск docker-compose на локальном порту 127.0.0.1
### Админ-зона: 127.0.0.1:5000/admin
### Бот заработает, если указать BOT_TOKEN в .env


```shell
docker compose up
```
Фоновый запуск
```shell
docker compose up -d
```

Обновить и поднять сеть после изменений:
```shell
docker compose up --build
```
Команда для удаления ВСЕХ компонентов Docker:
если надо почитсить систему быстро
(docker compose up будет работать как в первый раз)
```shell
docker system prune -a
```

