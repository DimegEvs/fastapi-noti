import base64
import datetime
from typing import Dict

import httpx
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from sqlalchemy import and_, insert, join, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import URL_LOGGER, SECRET_KEY
from src.message.models import Message, manager
from src.user.models import User, UserService
from src.database import async_session_maker, get_async_session


router = APIRouter(
    prefix="",
    tags=["WS"]
)


@router.websocket("/ws/{recipient_id}")
async def websocket_endpoint(websocket: WebSocket, recipient_id: int):
    if recipient_id in manager.active_connections:
        manager.disconnect(recipient_id=recipient_id, websocket=websocket)
    await manager.connect(recipient_id, websocket)
    try:
        while True:
            message = await websocket.receive_json()
    except WebSocketDisconnect:
        manager.disconnect(recipient_id, websocket)
        

@router.get("/ws_forward/{recipient_id}/{sender_id}")
async def websocket_forward(recipient_id: int, sender_id: int):
    if recipient_id in manager.active_connections:
        connection = manager.active_connections[recipient_id]
        user = await UserService.get_user(sender_id)
        print(user)
        await connection.send_json({
            "sender_name": f"{user[0].name} {user[0].surname}"
        })
        params = {
            "type": "INFO",
            "user_id": recipient_id,
            "message": f"User ID: {recipient_id} get notification from ID: {sender_id}."
        }
        async with httpx.AsyncClient() as client:
            await client.get(URL_LOGGER, params=params)