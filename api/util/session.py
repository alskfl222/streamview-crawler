from fastapi.websockets import WebSocket
from uuid import uuid4

class SessionManager():
    def __init__(self) -> None:
        self.sessions = {}

    def add_session(self, websocket: WebSocket, session_type: str):
        session_id = uuid4()
        session = {
            "type": session_type,
            "websocket": websocket
        }
        self.sessions[session_id] = session
        return session_id

    def remove_session(self, session_id: str):
        del self.sessions[session_id]