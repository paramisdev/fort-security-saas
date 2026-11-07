# Fort Security SaaS

Backend мультитенантной SaaS-платформы **«Форт»** для управления безопасностью объектов
недвижимости. Компании-арендаторы (тенанты) ведут свои охраняемые объекты, оборудование
(датчики, камеры, замки) и подписки на тарифы. Данные каждого тенанта изолированы.

## Возможности

- Регистрация компании вместе с администратором тенанта.
- JWT-аутентификация (access/refresh) и ролевая модель доступа (RBAC).
- Управление охраняемыми объектами и оборудованием.
- Каталог тарифов и смена тарифа с записью платежа (заглушка оплаты для MVP).
- Проверка лимитов тарифа по количеству объектов и устройств.
- Строгая изоляция данных по `tenant_id`.
- Автоматические миграции Alembic и идемпотентный сидинг тарифов и суперадмина.

## Стек технологий

| Слой | Технология |
| --- | --- |
| Язык | Python 3.11+ |
| Web-фреймворк | FastAPI 0.115 |
| ASGI-сервер | Uvicorn |
| ORM | SQLAlchemy 2.0 (async) |
| БД | PostgreSQL 16 (в тестах — SQLite через aiosqlite) |
| Миграции | Alembic |
| Валидация/настройки | Pydantic 2, pydantic-settings |
| Аутентификация | PyJWT, bcrypt |
| Контейнеризация | Docker, Docker Compose, uv |
| Качество кода | ruff, mypy, pytest |

## Архитектура

```
app/
├── main.py          # Фабрика FastAPI-приложения
├── core/            # Настройки, безопасность, подключение к БД
├── api/             # HTTP-слой: роутеры и зависимости
├── services/        # Бизнес-логика (без импортов FastAPI)
├── repositories/    # Доступ к данным (SQLAlchemy)
├── models/          # SQLAlchemy-модели
├── schemas/         # Pydantic-схемы
└── utils/           # Вспомогательные функции
```

Поток обработки запроса: `Router → Service → Repository → Model`.

## Быстрый запуск через Docker

Требуются Docker и Docker Compose v2.

```bash
# 1. Создайте файл окружения и при необходимости замените секреты.
cp .env.example .env

# 2. Соберите образ и запустите приложение с PostgreSQL.
docker compose up --build
```

При старте контейнер `app`:

1. ждёт готовности PostgreSQL (healthcheck `pg_isready`);
2. применяет миграции `alembic upgrade head`;
3. идемпотентно создаёт тарифы и суперадмина;
4. запускает Uvicorn на порту `8000`.

После запуска доступны:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- Health-check: <http://localhost:8000/health>

Остановить сервисы:

```bash
docker compose down
```

Удалить контейнеры вместе с данными PostgreSQL:

```bash
docker compose down -v
```

## Локальный запуск без Docker

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

pip install -r requirements-dev.txt
cp .env.example .env

# PostgreSQL должен быть запущен, DATABASE_URL — указывать на него.
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload
```

## Переменные окружения

Все настройки читаются через `pydantic-settings` из `.env` или переменных окружения.

| Переменная | Назначение | По умолчанию |
| --- | --- | --- |
| `APP_NAME` | Название приложения | `Fort Security SaaS` |
| `DEBUG` | Режим отладки и SQL-логов | `false` |
| `APP_PORT` | Внешний порт приложения в Docker | `8000` |
| `DATABASE_URL` | DSN PostgreSQL для async-драйвера | `postgresql+asyncpg://fort:fort@localhost:5432/fort` |
| `POSTGRES_USER` | Пользователь БД в Docker | `fort` |
| `POSTGRES_PASSWORD` | Пароль БД в Docker | `fort` |
| `POSTGRES_DB` | Имя БД в Docker | `fort` |
| `POSTGRES_PORT` | Внешний порт PostgreSQL | `5432` |
| `JWT_SECRET_KEY` | Секрет подписи JWT | `change-me-in-production` |
| `JWT_ALGORITHM` | Алгоритм подписи JWT | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни access-токена, минуты | `30` |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Время жизни refresh-токена, дни | `14` |
| `SUPERADMIN_EMAIL` | Email суперадмина для сидинга | `admin@fort.local` |
| `SUPERADMIN_PASSWORD` | Пароль суперадмина для сидинга | `change-me-too` |

> В production обязательно замените `JWT_SECRET_KEY`, `POSTGRES_PASSWORD` и пароль
> суперадмина. Файл `.env` исключён из Git и Docker-образа.

## Тесты и quality gates

```bash
pip install -r requirements-dev.txt

ruff check .      # линтинг
ruff format .     # форматирование
mypy app          # статическая типизация
pytest -q         # тесты
```

Тесты используют SQLite в памяти и не требуют запущенного PostgreSQL.

## Роли

| Роль | Доступ |
| --- | --- |
| `superadmin` | Управление глобальным каталогом тарифов; не привязан к тенанту |
| `tenant_admin` | Управление объектами, устройствами и подпиской своего тенанта |
| `client` | Просмотр объектов и устройств своего тенанта |

## API

Базовый префикс: `/api/v1`. Все защищённые эндпоинты ожидают заголовок
`Authorization: Bearer <access_token>`.

### Системные

| Метод | Путь | Описание |
| --- | --- | --- |
| `GET` | `/health` | Проверка работоспособности |

### Аутентификация

| Метод | Путь | Доступ | Описание |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/register` | публично | Регистрация тенанта и его администратора |
| `POST` | `/api/v1/auth/login` | публично | Получение пары access/refresh токенов |
| `POST` | `/api/v1/auth/refresh` | публично | Новый access-токен по refresh-токену |

### Пользователи

| Метод | Путь | Доступ | Описание |
| --- | --- | --- | --- |
| `GET` | `/api/v1/users/me` | авторизован | Профиль текущего пользователя |

### Тарифы

| Метод | Путь | Доступ | Описание |
| --- | --- | --- | --- |
| `GET` | `/api/v1/tariffs` | публично | Каталог активных тарифов |
| `GET` | `/api/v1/tariffs/{tariff_id}` | публично | Тариф по идентификатору |
| `POST` | `/api/v1/tariffs` | `superadmin` | Создание тарифа |
| `PATCH` | `/api/v1/tariffs/{tariff_id}` | `superadmin` | Обновление тарифа |

### Охраняемые объекты

| Метод | Путь | Доступ | Описание |
| --- | --- | --- | --- |
| `GET` | `/api/v1/objects` | `tenant_admin`, `client` | Список объектов тенанта |
| `POST` | `/api/v1/objects` | `tenant_admin` | Создание объекта (с проверкой лимита) |
| `GET` | `/api/v1/objects/{object_id}` | `tenant_admin`, `client` | Объект по id |
| `PATCH` | `/api/v1/objects/{object_id}` | `tenant_admin` | Частичное обновление |
| `DELETE` | `/api/v1/objects/{object_id}` | `tenant_admin` | Удаление объекта |

### Оборудование

| Метод | Путь | Доступ | Описание |
| --- | --- | --- | --- |
| `GET` | `/api/v1/devices` | `tenant_admin`, `client` | Список устройств; фильтры `object_id`, `type`, `status` |
| `POST` | `/api/v1/devices` | `tenant_admin` | Регистрация устройства (с проверкой лимита) |
| `GET` | `/api/v1/devices/{device_id}` | `tenant_admin`, `client` | Устройство по id |
| `PATCH` | `/api/v1/devices/{device_id}` | `tenant_admin` | Частичное обновление |
| `PATCH` | `/api/v1/devices/{device_id}/status` | `tenant_admin` | Смена статуса online/offline |
| `DELETE` | `/api/v1/devices/{device_id}` | `tenant_admin` | Удаление устройства |

### Подписки

| Метод | Путь | Доступ | Описание |
| --- | --- | --- | --- |
| `GET` | `/api/v1/subscriptions/current` | `tenant_admin` | Текущая активная подписка |
| `POST` | `/api/v1/subscriptions/change` | `tenant_admin` | Смена тарифа с записью платежа |

### Пример регистрации и входа

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_name": "ООО Ромашка",
    "admin": {
      "email": "admin@romashka.ru",
      "password": "strong-password",
      "full_name": "Иван Петров"
    }
  }'

curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@romashka.ru", "password": "strong-password"}'
```

## Схема базы данных

| Таблица | Назначение |
| --- | --- |
| `tenants` | Компании-арендаторы; корень изоляции данных |
| `users` | Пользователи платформы (`superadmin`, `tenant_admin`, `client`) |
| `tariffs` | Глобальный каталог тарифов и лимитов |
| `subscriptions` | Подписки тенантов на тарифы (не более одной активной) |
| `payments` | Платежи по подпискам (MVP-заглушка) |
| `objects` | Охраняемые объекты тенанта |
| `devices` | Оборудование тенанта, привязанное к объекту |
| `alembic_version` | Служебная таблица версий миграций |

Связи: `tenants 1—N users`, `tenants 1—N objects`, `tenants 1—N devices`,
`objects 1—N devices`, `tenants 1—N subscriptions`, `subscriptions 1—N payments`,
`tariffs 1—N subscriptions`.

## Миграции и сидинг

```bash
alembic upgrade head                  # применить миграции
alembic revision --autogenerate -m "..."  # новая миграция
python -m scripts.seed                # тарифы + суперадмин (идемпотентно)
```

## Лицензия

Проект распространяется в рамках внутренней разработки. Все права защищены.
