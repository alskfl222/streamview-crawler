#!/usr/bin/env python
# coding: utf-8

import asyncio
import os
import traceback
import threading
import queue
import time
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
from router.observer import observer_routing

load_dotenv()
print(f"ENV : {os.getenv('PY_ENV')}")


async def consumer(q: queue.SimpleQueue):
    while True:
        try:
            args = q.get_nowait()
            sv, websocket, data = args
            if data['event']['name'].startswith('bgm'):
                await bgm.handler(sv, websocket, data)
            if data['event']['name'].startswith('obs'):
                await observer.handler(sv, data)
        except queue.Empty:
            time.sleep(3)
            continue
        except:
            traceback.print_exc()
            break


def _consumer(q: queue.SimpleQueue):
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(consumer(q))
    except:
        traceback.print_exc()


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
        self.sm = session.SessionManager()
        self.observer = None
        self.bgm = {
            "active": False,
            "updateTime": datetime.now(),
            "currentTime": 0,
            "duration": 0
        }
        self.tasks = queue.SimpleQueue()
        self.consumers = [threading.Thread(target=_consumer, args=(
            self.tasks,), daemon=True)]

        for p in self.consumers:
            p.start()

        @self.get('')
        async def get_index():
            return "qwerty"

        observer_routing(self)

        @self.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()

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
                if data['event']['from'] in ['controller', 'viewer', 'stream'] and data['event']['name'] == 'session':
                    await common.init_list(self, websocket)
                    session_id = self.sm.add_session(
                        websocket, data['event']['from'])
                    await websocket.send_json({"event": {"to": data['event']['from'], "name": "session"}, "data": {
                        "sessionId": session_id}})
                    continue

                self.tasks.put((self, websocket, data))

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
