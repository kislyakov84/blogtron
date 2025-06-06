from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Telegram Blog Bot API!"}

if __name__ == "__main__":
    import uvicorn
    # Запускаем Uvicorn сервер
    # Вместо прямого объекта 'app', передаем строку "module_name:app_object_name"
    # Это позволяет Uvicorn правильно использовать reload=True
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) # <--- Теперь так