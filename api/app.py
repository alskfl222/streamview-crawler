#!/usr/bin/env python
# coding: utf-8

import os
import traceback
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocket
import uvicorn
from dotenv import load_dotenv
from util import *

class StreamviewServer():
  def __init__(self):
    load_dotenv()
    PORT = int(os.getenv('PORT'))

    app = FastAPI()
    app.mount("/static", StaticFiles(directory="static"), name="static")

    self.original = [
        { "name": "Elliot Hsu - Spiraling Gales", "id": 'HoSQqadfiag', "from": 'list' },
        { "name": "꿈의 도시 레헬른 (Lacheln, The City of Dreams) (Chill House Lounge Ver.) ｜메이플스토리 : 아케인리버 (크라우드펀딩)",
          "id": 'oKCQJ8w5e3E', "from": 'list' },
        { "name": "Galshi Revolution - Shot", "id": 'pnxYMsBdyxo', "from": 'list' },
        { "name": "Fairy Tale", "id": 'b12-WUgXAzg', "from": 'list' },
        { "name": "Ryoshi - Dawn", "id": "QWdwrfxspxo", "from": 'list' },
        { "name": "Xomu & Justin Klyvis - Setsuna (Kirara Magic Remix)", "id": "Qz-Fu7nVo3c", "from": 'list' },
        { "name": "두번째달(2nd Moon) - 얼음연못(Ice Pond) [OST of Goong]", "id": "BZYVj8P2D18", "from": 'list' },
      ]
    self.queue = [*self.original[:5]]
    self.finder = finder.Finder()

    @app.get("/")
    async def get_index():
      return "Hello World!"

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
      await websocket.accept()
      await self.init_list(websocket)

      while True:
        raw = await websocket.receive_json()
        ev_type = raw['event']['type']
        ev_name = raw['event']['name']
        data = raw['data']
        try:
          if ev_type == 'bgm': await bgm.handler(self, websocket, ev_name, data)
        except:
          traceback.print_exc()
          await websocket.send_json(f"error")

    app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
    )

    uvicorn.run(app=app, host='0.0.0.0', port=PORT)
  
  async def init_list(self, websocket: WebSocket):
    res = {
        "event": {
          "type": 'bgm',
          "name": "queue"
        },
        "data": {
          "queue": self.queue
        }
      }
    await websocket.send_json(res)

StreamviewServer()
