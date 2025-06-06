# Telegram Blog Bot (Тестовое Задание)

Telegram-бот для отображения постов блога, управляемых через API-админку.

## Описание

Проект состоит из двух компонентов:
1. **API-сервер (FastAPI)** - RESTful API для управления постами блога
2. **Telegram-бот (python-telegram-bot)** - отображает посты пользователям в Telegram

## Функционал

### API (Админка)
- **CRUD-операции для постов:**
  - `POST /posts/` - Создать пост
  - `GET /posts/` - Получить все посты
  - `GET /posts/{post_id}` - Получить пост по ID
  - `PUT /posts/{post_id}` - Обновить пост
  - `DELETE /posts/{post_id}` - Удалить пост
- **Модель поста:**
  - Заголовок (`title`)
  - Текст (`text`)
  - Дата создания (`created_at`)
- **Документация:**
  - Swagger UI: `http://localhost:8000/docs`
  - ReDoc: `http://localhost:8000/redoc`

### Telegram-бот
- `/posts` - Показывает список постов с интерактивными кнопками
- Просмотр поста - Отображает полный текст и дату создания при выборе

## Технологии

- **Python:** 3.9+
- **Web Framework:** FastAPI
- **Telegram Library:** `python-telegram-bot`
- **База данных:** SQLite (`blog.db`)
- **ORM:** SQLAlchemy
- **HTTP Client:** httpx
- **Конфигурация:** `.env`

## Запуск проекта

### 1. Клонирование репозитория
```bash
git clone https://github.com/kislyakov84/blogtron.git
cd blogtron
2. Настройка окружения и установка зависимостей
bash
# Создание виртуального окружения
python -m venv .venv

# Активация окружения
# Windows:
.\.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
3. Настройка переменных окружения
Создайте файл .env из шаблона:

bash
cp .env.template .env  # macOS/Linux
# Для Windows: скопируйте содержимое .env.template в новый файл .env
Замените в .env:

ini
BOT_TOKEN=ВАШ_ТОКЕН_ОТ_BOTFATHER
DATABASE_URL=sqlite:///./blog.db
4. Запуск API-сервера
bash
python main.py
Сервер запустится на http://localhost:8000

5. Запуск Telegram-бота
bash
python bot/main.py
6. Проверка работы
Создайте пост через Swagger UI: http://localhost:8000/docs (эндпоинт POST /posts/)

Найдите бота в Telegram по имени

Используйте команды:

/start - Приветствие

/posts - Список постов

Нажмите на заголовок поста для просмотра содержимого

Важные примечания
Для Windows используйте PowerShell вместо CMD

При изменении кода API перезапустите сервер

Токен бота можно получить через @BotFather

Первый запуск создаст файл БД blog.db