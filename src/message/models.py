from ast import Dict
from datetime import datetime

from fastapi_users.db import BaseUserDatabase
from fastapi import Depends, WebSocket
from fastapi_users.db import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase
from sqlalchemy import (JSON, TIMESTAMP, Boolean, Column, DateTime, ForeignKey, Integer,
                        String, Table, and_, func, insert, join, or_, select, update)

from src.database import Base, async_session_maker
from src.user.models import User

class Message(Base):
    __tablename__ = "message"
    id = Column(Integer, primary_key=True)
    message = Column(String, nullable= False)
    sender_id = Column(Integer, ForeignKey("user.id"))
    recipient_id = Column(Integer, ForeignKey("user.id"))
    timestamp = Column(DateTime, default=func.now())
    is_read = Column(Boolean, default= False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'is_read': self.is_read
        }
        
    class Config:
        from_attributes = True
    


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, recipient_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[recipient_id] = websocket
        not_read_message = await self.get_not_read_message(self=self, recipient_id=recipient_id)
        for mes in not_read_message:
            print(mes)
            await self.send_notifications_message(recipient_id=recipient_id, data=mes)

    def disconnect(self, recipient_id: int, websocket: WebSocket):
        try:
            del self.active_connections[recipient_id]
        except KeyError:
            print(f"Неудачное отключение пользователя {recipient_id}")

    async def send_personal_message(self, websocket: WebSocket, data):
        await websocket.send_json(data)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)
    async def send_notifications_message(self, recipient_id: int, data):
        connection = self.active_connections[recipient_id]
        await connection.send_json(data=data)
    async def send_active_user_message(self, websocket: WebSocket, recipient_id: int, data):
        if recipient_id in self.active_connections:
            connection = self.active_connections[recipient_id]
            await connection.send_json(data=data)
            await websocket.send_json(data=data)
        else:
            print(data)
            await websocket.send_json(data=data)
    
            
    @staticmethod 
    async def get_not_read_message(self, recipient_id: int):
        async with async_session_maker() as session:
            query = (
                select(Message, User.name.label('nameSender'), User.surname.label('surnameSender'))
                .select_from(join(Message, User, onclause=Message.sender_id == User.id))
                .where(
                    and_(Message.recipient_id == recipient_id, Message.is_read == False))
                .order_by(Message.timestamp.desc())
            )
            result = await session.execute(query)
            messages_with_user_info = [
                {
                    'message': message[0].to_dict(),
                    'sender_name': f"{message.nameSender} {message.surnameSender}"
                }
                for message in result
            ]
            return messages_with_user_info
    


manager = ConnectionManager()
    