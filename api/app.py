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
from util import bgm

class StreamviewServer():
  def __init__(self):
    load_dotenv()
    PORT = int(os.getenv('PORT'))

    app = FastAPI()
    app.mount("/static", StaticFiles(directory="static"), name="static")

    self.queue = [
        { "id": 'HoSQqadfiag', "from": 'streamer' },
        { "id": 'oKCQJ8w5e3E', "from": 'streamer' },
        { "id": 'pnxYMsBdyxo', "from": 'streamer' },
        { "id": 'b12-WUgXAzg', "from": 'streamer' },
      ]

    @app.get("/")
    async def get_index():
      return "Hello World!"

    @app.get("/list")
    async def get_list():
      queue = [
        { "id": 'HoSQqadfiag', "from": 'streamer' },
        { "id": 'oKCQJ8w5e3E', "from": 'streamer' },
        { "id": 'pnxYMsBdyxo', "from": 'streamer' },
        { "id": 'b12-WUgXAzg', "from": 'streamer' },
      ]
      return { "event": { 'type': 'bgm', 'name': 'queue' },
               "data": { "queue": queue } }

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
      await websocket.accept()
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

StreamviewServer()