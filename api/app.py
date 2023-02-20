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
from util import *


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
        self.bgm_start_time = datetime.now()

        @app.get("/")
        async def get_index():
            return "qwerty"

        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            await self.init_list(websocket)
            await self.finder.init()

            while True:
                raw = await websocket.receive()
                websocket_type = raw['type']
                if websocket_type == 'websocket.disconnect':
                    self.sm.remove_session(websocket)
                    return
                
                data = json.loads(raw['text'])
                session = data['session']
                event = data['session']['event'].split('.')
                ev_type = event[0]
                ev_name = event[1]

                try:
                    ws_data = data['data']
                except:
                    ws_data = None

                if ev_type == 'bgm':
                    await bgm.handler(self, websocket, session, ev_name, ws_data)

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
            "session": {
                "type": 'all',
                "event": "bgm.queue"
            },
            "data": {
                "queue": self.queue
            }
        }
        await websocket.send_json(res)


StreamviewServer()
