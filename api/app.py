#!/usr/bin/env python
# coding: utf-8

import os
from datetime import datetime
import random
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocket
import uvicorn
from dotenv import load_dotenv
from module import *


class StreamviewServer():
    def __init__(self):
        load_dotenv()
        PORT = int(os.getenv('PORT'))

        app = FastAPI()
        app.mount("/static", StaticFiles(directory="static"), name="static")

        today = datetime.now()
        monthly_list_name = f'BGM {today.year} {today.month:0>2}'
        print(f"TODAY LIST : {monthly_list_name}")

        self.db = db.DB()
        self.original = self.db.get_monthly_list_active()
        self.queue = [self.original[0], *random.choices(self.original, k=9)]
        self.finder = finder.Finder()
        self.sm = session.SessionManager()
        self.bgm_active = True

        @app.get("/")
        async def get_index():
            return "qwerty"

        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            await self.finder.init()

            while True:
                raw = await websocket.receive()
                print(f"RAW : {raw}")
                websocket_type = raw['type']
                if websocket_type == 'websocket.disconnect':
                    try:
                        self.sm.remove_session(websocket)
                    finally:
                        return

                data = json.loads(raw['text'])
                event_name = data['event']['name']
                if data['event']['type'] in ['controller', 'viewer', 'stream'] and event_name == 'bgm.session':
                    await self.init_list(websocket)

                if event_name.startswith('bgm'):
                    await bgm.handler(self, websocket, data)
                if event_name.startswith('obs'):
                    await observer.handler(self, data)

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
                "type": 'all',
                "name": "bgm.queue",
                "message": "init"
            },
            "data": {
                "queue": self.queue,
                "list_title": self.db.latest_list['title'],
                "state": "pause",
                "current_time": "0",
                "duration": "0"
            }
        }
        await websocket.send_json(res)


StreamviewServer()
