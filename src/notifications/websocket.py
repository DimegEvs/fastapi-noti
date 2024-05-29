import base64
import datetime
from typing import Dict

import httpx
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from sqlalchemy import and_, insert, join, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import URL_LOGGER, SECRET_KEY, URL_MIDDLEWARE
from src.message.models import Message, manager
from src.user.models import User, UserService
from src.database import async_session_maker, get_async_session

# Создание роутера для WebSocket с тегом "WS"
router = APIRouter(
    prefix="",
    tags=["WS"]
)

# Обработчик для WebSocket соединения
@router.websocket("/ws/{recipient_id}")
async def websocket_endpoint(websocket: WebSocket, recipient_id: int):
    if recipient_id in manager.active_connections:
        manager.disconnect(recipient_id=recipient_id, websocket=websocket)  # Отключение предыдущего соединения
    await manager.connect(recipient_id, websocket)  # Подключение нового соединения
    params = {
        "message": f"Websocket accepted: {websocket.url} IP: {websocket.client.host} HEADERS: {websocket.headers} COOKIES: {websocket.cookies}"
    }
    # Логирование подключения через HTTP запрос
    async with httpx.AsyncClient() as client:
        try:
            await client.get(URL_MIDDLEWARE, params=params)
        except httpx.HTTPError as e:
            print(f"HTTP error occurred: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    try:
        while True:
            message = await websocket.receive_json()  # Получение сообщения от WebSocket клиента
    except WebSocketDisconnect:
        params = {
            "message": f"Websocket disconnected: {websocket.url} IP: {websocket.client.host} HEADERS: {websocket.headers} COOKIES: {websocket.cookies}"
        }
        # Логирование отключения через HTTP запрос
        async with httpx.AsyncClient() as client:
            try:
                await client.get(URL_MIDDLEWARE, params=params)
            except httpx.HTTPError as e:
                print(f"HTTP error occurred: {e}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
        manager.disconnect(recipient_id, websocket)  # Отключение пользователя от WebSocket

# Эндпоинт для пересылки WebSocket сообщения
@router.get("/ws_forward/{recipient_id}/{sender_id}")
async def websocket_forward(recipient_id: int, sender_id: int):
    if recipient_id in manager.active_connections:
        connection = manager.active_connections[recipient_id]  # Получение соединения получателя
        user = await UserService.get_user(sender_id)  # Получение информации о пользователе
        print(user)
        await connection.send_json({
            "sender_name": f"{user[0].name} {user[0].surname}"
        })
        params = {
            "type": "INFO",
            "user_id": recipient_id,
            "message": f"User ID: {recipient_id} get notification from ID: {sender_id}."
        }
        # Логирование через HTTP запрос
        async with httpx.AsyncClient() as client:
            await client.get(URL_LOGGER, params=params)
