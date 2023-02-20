from fastapi.websockets import WebSocket
from uuid import uuid4


class SessionManager():
    def __init__(self):
        self.sessions = {}

    def add_session(self, websocket: WebSocket, session_type: str):
        session_id = str(uuid4())
        session = {
            "type": session_type,
            "websocket": websocket
        }
        self.sessions[session_id] = session
        return session_id

    def remove_session(self, session_id: str):
        del self.sessions[session_id]

    async def emit_all(self, data):
        for session_id in self.sessions:
            await self.sessions[session_id]["websocket"].send_json(data)

    async def emit_stream(self, data):
        websockets_stream = [x['websocket']
                             for x in self.sessions.values() if x['type'] == 'stream']
        for websocket in websockets_stream:
            await websocket.send_json(data)
