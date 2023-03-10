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
from router.observer import observer_routing
from module import *

load_dotenv()

class StreamviewServer(FastAPI):
    def __init__(self):
        PORT = int(os.getenv('PORT'))

        super().__init__()
        self.mount("/static", StaticFiles(directory="static"), name="static")

        today = datetime.now()
        monthly_list_name = f'BGM {today.year} {today.month:0>2}'
        print(f"TODAY LIST : {monthly_list_name}")

        self.db = db.DB()
        self.original = self.db.get_monthly_list_active()
        self.queue = [self.original[0], *random.sample(self.original, k=9)]
        self.finder = finder.Finder()
        self.sm = session.SessionManager()
        self.sub_process = None
        self.bgm = {
            "active": False,
            "updateTime": datetime.now(),
            "currentTime": 0,
            "duration": 0
        }

        @self.get('')
        async def get_index():
            return "qwerty"
        
        observer_routing(self)

        @self.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            await self.finder.init()

            while True:
                raw = await websocket.receive()
                # print(f"RAW : {raw}")
                websocket_type = raw['type']
                if websocket_type == 'websocket.disconnect':
                    try:
                        self.sm.remove_session(websocket)
                    finally:
                        return

                data = json.loads(raw['text'])
                event_name = data['event']['name']
                if data['event']['from'] in ['controller', 'viewer', 'stream'] and event_name == 'session':
                    await common.init_list(self, websocket)
                    session_id = self.sm.add_session(
                        websocket, data['event']['from'])
                    await websocket.send_json({"event": {"to": data['event']['from'], "name": "session"}, "data": {
                        "sessionId": session_id}})
                    continue

                if event_name.startswith('bgm'):
                    await bgm.handler(self, websocket, data)
                if event_name.startswith('obs'):
                    await observer.handler(self, data)

        self.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        uvicorn.run(app=self, host='0.0.0.0', port=PORT)


if __name__ == '__main__':
    server = StreamviewServer()
