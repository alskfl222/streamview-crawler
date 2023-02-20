#!/usr/bin/env python
# coding: utf-8

import traceback
import os
import datetime
import random
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

        today = datetime.datetime.now()
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
            await self.init_list(websocket)
            await self.finder.init()

            try:
                while True:
                    raw = await websocket.receive_json()
                    session_type = raw['session']['type']
                    event = raw['session']['event'].split('.')
                    ev_type = event[0]
                    ev_name = event[1]
                    try:
                        data = raw['data']
                    except:
                        data = None
                    try:
                        if ev_type == 'bgm':
                            await bgm.handler(self, websocket, session_type, ev_name, data)
                    except:
                        print("ERROR!")
                        traceback.print_exc()
            except:
                print("CLOSE", raw)
                self.sm.remove_session(raw['session']['id'])
                return

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
