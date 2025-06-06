# main.py
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import List

from dotenv import load_dotenv
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    status,
    Request,
)  # <-- ДОБАВЛЕНО Request
from fastapi.security import OAuth2PasswordRequestForm

from app.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    Token,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    User,
)  # <-- Убедитесь, что User импортирован
from app.crud import create_post, delete_post, get_all_posts, get_post, update_post
from app.database import create_db_tables, database
from app.schemas import PostCreate, PostResponse, PostUpdate

# Для обработки ошибок валидации и общих ошибок
from fastapi.exceptions import RequestValidationError  # <-- ДОБАВЛЕНО
from fastapi.responses import JSONResponse  # <-- ДОБАВЛЕНО
import logging  # <-- ДОБАВЛЕНО для логирования ошибок

# Настройка логирования для main.py (полезно для отладки)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# Загружаем переменные окружения
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")  # <-- Изменено на logger.info
    create_db_tables()
    await database.connect()
    yield
    logger.info("Shutting down...")  # <-- Изменено на logger.info
    await database.disconnect()


app = FastAPI(
    title="Telegram Blog Bot API",
    description="API для управления постами блога для Telegram бота.",
    version="0.0.1",
    lifespan=lifespan,
)

# --- ГЛОБАЛЬНЫЕ ОБРАБОТЧИКИ ОШИБОК ---


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Обработчик ошибок валидации входных данных (например, Pydantic).
    Возвращает 422 Unprocessable Entity с деталями ошибки.
    """
    logger.error(f"Validation error: {exc.errors()} for URL: {request.url}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "message": "Некорректные входные данные"},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Обработчик HTTPException, который мы сами выбрасываем.
    Возвращает заданный статус и детали.
    """
    logger.warning(
        f"HTTP exception: {exc.status_code} - {exc.detail} for URL: {request.url}"
    )
    return JSONResponse(status_code=exc.status_code, content={"message": exc.detail})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Общий обработчик для всех непредвиденных исключений.
    Возвращает 500 Internal Server Error.
    """
    logger.exception(
        f"Unhandled exception at URL: {request.url}"
    )  # Логируем полную трассировку
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Произошла непредвиденная ошибка на сервере. Пожалуйста, попробуйте позже."
        },
    )


@app.get(
    "/", include_in_schema=False
)  # Скрываем этот эндпоинт из документации, он не является частью API
async def read_root():
    return {"message": "Welcome to the Telegram Blog Bot API!"}


@app.post("/token", response_model=Token, summary="Получить JWT токен")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Аутентифицирует пользователя и выдает Access Token.
    Используйте 'admin'/'securepassword' для входа.
    """
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post(
    "/posts/",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый пост (требуется аутентификация)",
)
async def create_new_post(
    post: PostCreate, current_user: User = Depends(get_current_active_user)
):
    """
    Создает новый пост в блоге.
    - **title**: Заголовок поста (обязательно)
    - **text**: Текст поста (обязательно)
    """
    post_id = await create_post(post)
    created_post = await get_post(post_id)
    if not created_post:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve created post.",
        )
    return created_post


@app.get("/posts/", response_model=List[PostResponse], summary="Получить все посты")
async def read_all_posts():
    """
    Возвращает список всех существующих постов, отсортированных по дате создания.
    """
    return await get_all_posts()


@app.get("/posts/{post_id}", response_model=PostResponse, summary="Получить пост по ID")
async def read_post_by_id(post_id: int):
    """
    Возвращает пост по его уникальному идентификатору.
    - **post_id**: ID поста
    """
    post = await get_post(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    return post


@app.put(
    "/posts/{post_id}",
    response_model=PostResponse,
    summary="Обновить существующий пост (требуется аутентификация)",
)
async def update_existing_post(
    post_id: int,
    post: PostUpdate,
    current_user: User = Depends(get_current_active_user),
):
    """
    Обновляет заголовок и/или текст существующего поста.
    - **post_id**: ID поста, который нужно обновить
    - **title**: Новый заголовок поста (необязательно)
    - **text**: Новый текст поста (необязательно)
    """
    existing_post = await get_post(post_id)
    if not existing_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    updated_successfully = await update_post(post_id, post)
    if not updated_successfully:
        return existing_post  # Возвращаем существующий пост, если не было изменений

    updated_post = await get_post(post_id)
    if not updated_post:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve updated post after update.",
        )
    return updated_post


@app.delete(
    "/posts/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить пост (требуется аутентификация)",
)
async def delete_existing_post(
    post_id: int, current_user: User = Depends(get_current_active_user)
):
    """
    Удаляет пост по его уникальному идентификатору.
    - **post_id**: ID поста, который нужно удалить
    """
    deleted_successfully = await delete_post(post_id)
    if not deleted_successfully:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    return


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
