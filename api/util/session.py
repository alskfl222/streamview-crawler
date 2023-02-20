import traceback
import asyncio
import threading
import time
from datetime import datetime
from uuid import uuid4
from fastapi.websockets import WebSocket


class SessionManager():
    def __init__(self):
        self.sessions = {}
        self.timer = threading.Thread(target=self._ping_check, daemon=True)
        self.timer.start()

    async def ping_check(self):
        count = len(self.sessions)
        while True:
            time.sleep(5)
            if count != len(self.sessions):
                count = len(self.sessions)
                print(f'{datetime.now()} - {count} session')


    def _ping_check(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.ping_check())
        loop.close()

    def add_session(self, websocket: WebSocket, session_type: str):
        session_id = str(uuid4())
        session = {
            "type": session_type,
            "start_time": datetime.now(),
            "websocket": websocket
        }
        self.sessions[session_id] = session
        return session_id

    def remove_session(self, websocket: WebSocket):
        try:
            session_id = [x[0] for x in self.sessions.items() if x[1]["websocket"] == websocket][0]
            session = self.sessions[session_id]
        except:
            traceback.print_exc()
            return
        diff = datetime.now() - session['start_time']
        hour = str(diff).split(':')[0]
        minute = str(diff).split(':')[1]
        second = str(diff).split(':')[2].split('.')[0]
        print(f'{session_id} removed : {hour:0<2}:{minute}:{second}')
        del self.sessions[session_id]

    async def emit_all(self, data):
        for session_id in self.sessions:
            await self.sessions[session_id]["websocket"].send_json(data)

    async def emit_stream(self, data):
        websockets_stream = [x['websocket']
                             for x in self.sessions.values() if x['type'] == 'stream']
        for websocket in websockets_stream:
            await websocket.send_json(data)

    async def emit_viewer(self, data):
        websockets_viewer = [x['websocket']
                             for x in self.sessions.values() if x['type'] == 'viewer']
        for websocket in websockets_viewer:
            await websocket.send_json(data)
