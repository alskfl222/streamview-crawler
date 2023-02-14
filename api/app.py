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
        self.bgm_active = True

        @app.get("/")
        async def get_index():
            return "Hello World!"

        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            await self.init_list(websocket)
            await self.finder.init()

            while True:
                try:
                    raw = await websocket.receive_json()
                except:
                    print("WEBSOCKET CLOSED?")
                    await self.finder.playwright.stop()
                    return
                ev_type = raw['event']['type']
                ev_name = raw['event']['name']
                data = raw['data']
                try:
                    if ev_type == 'bgm':
                        await bgm.handler(self, websocket, ev_name, data)
                except:
                    print("ERROR!")
                    traceback.print_exc()

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
