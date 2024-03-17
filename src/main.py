from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List

from src.notifications.websocket import router as router_noti



app = FastAPI()


app.include_router(router=router_noti)