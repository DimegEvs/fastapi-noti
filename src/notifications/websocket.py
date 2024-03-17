import datetime
from typing import Dict
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from sqlalchemy import and_, insert, join, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

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
        connetion = manager.active_connections[recipient_id]
        user = await UserService.get_user(sender_id)
        print(user)
        await connetion.send_json({
            "sender_name": f"{user[0].name} {user[0].surname}"
        })