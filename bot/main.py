# bot/main.py
import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import httpx
from datetime import datetime

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем токен бота и URL API из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
# FastAPI API URL (поскольку бот будет запускаться отдельно, он должен знать, куда обращаться)
# Если вы запускаете бота на той же машине, что и FastAPI, можно использовать localhost.
# Если FastAPI запущен в Docker или на другом IP, используйте соответствующий IP.
# Для тестового задания 'http://localhost:8000' (или 'http://127.0.0.1:8000') подойдет,
# так как FastAPI запущен на 0.0.0.0:8000.
API_BASE_URL = "http://localhost:8000"


# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение при команде /start."""
    assert update.message is not None # <-- ДОБАВЛЕНО
    await update.message.reply_text('Привет! Я бот для показа постов из блога. Используй команду /posts, чтобы увидеть список.')

# Обработчик команды /posts
async def show_posts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает кнопки с заголовками постов."""
    assert update.message is not None # <-- ДОБАВЛЕНО
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/posts/")
            response.raise_for_status()
            posts_data = response.json()

        if not posts_data:
            await update.message.reply_text("Постов пока нет. Добавьте их через API-админку!")
            return

        keyboard = []
        for post in posts_data:
            keyboard.append([InlineKeyboardButton(post["title"], callback_data=f"post_{post['id']}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Выберите пост:', reply_markup=reply_markup)

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching posts: {e.response.status_code} - {e.response.text}")
        await update.message.reply_text(f"Произошла ошибка при получении постов: HTTP {e.response.status_code}. Пожалуйста, попробуйте позже.")
    except httpx.RequestError as e:
        logger.error(f"Network error fetching posts: {e}")
        await update.message.reply_text("Не удалось подключиться к серверу API. Пожалуйста, проверьте его работу.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        await update.message.reply_text("Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже.")

# Обработчик нажатия на кнопку (callback query)
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает детали поста при нажатии на кнопку."""
    assert update.callback_query is not None
    query = update.callback_query
    assert query.data is not None # <-- ДОБАВЛЕНО: последнее утверждение для Pylance
    await query.answer()

    # Разбираем callback_data: "post_ID"
    callback_data_parts = query.data.split('_') # <-- Теперь Pylance точно не ругается!
    if len(callback_data_parts) == 2 and callback_data_parts[0] == "post":
        post_id = int(callback_data_parts[1])
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_BASE_URL}/posts/{post_id}")
                response.raise_for_status()
                post = response.json()

            # Форматируем дату
            created_at_dt = datetime.fromisoformat(post["created_at"])
            formatted_date = created_at_dt.strftime("%d.%m.%Y %H:%M")

            message_text = (
                f"<b>{post['title']}</b>\n\n"
                f"{post['text']}\n\n"
                f"<i>Дата создания: {formatted_date}</i>"
            )
            await query.edit_message_text(message_text, parse_mode="HTML")
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                await query.edit_message_text("Пост не найден или был удален.")
            else:
                logger.error(f"HTTP error fetching post details: {e.response.status_code} - {e.response.text}")
                await query.edit_message_text(f"Ошибка при получении деталей поста: HTTP {e.response.status_code}.")
        except httpx.RequestError as e:
            logger.error(f"Network error fetching post details: {e}")
            await query.edit_message_text("Не удалось подключиться к серверу API для получения деталей поста.")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            await query.edit_message_text("Произошла непредвиденная ошибка при показе поста.")
    else:
        await query.edit_message_text("Неизвестный запрос.")


def main() -> None:
    """Запускает бота."""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не установлен в .env файле.")
        print("Ошибка: BOT_TOKEN не установлен. Пожалуйста, добавьте его в файл .env")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики команд и колбеков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("posts", show_posts))
    application.add_handler(CallbackQueryHandler(button_callback, pattern=r'^post_\d+$')) # Обработка кнопок типа "post_ID"

    logger.info("Бот запущен. Ожидание обновлений...")
    print("Бот запущен. Отправьте /start или /posts в Telegram.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()