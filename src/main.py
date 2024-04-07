import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from typing import List

from src.notifications.websocket import router as router_noti
from src.config import URL_MIDDLEWARE


app = FastAPI()


app.include_router(router=router_noti)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Логирование информации о запросе
    params = {
        "message": f"Request: {request.method} {request.url} IP: {request.client.host} HEADERS: {request.headers} COOKIES: {request.cookies}"
    }
    async with httpx.AsyncClient() as client:
        try:
            await client.get(URL_MIDDLEWARE, params=params)
        except httpx.HTTPError as e:
            print(f"HTTP error occurred: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    response = await call_next(request)
    return response



