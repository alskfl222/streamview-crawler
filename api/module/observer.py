from fastapi.websockets import WebSocket


async def add_new_session(sv, ws: WebSocket, session_type):
    session_id = sv.sm.add_session(ws, session_type)
    res = {
        "session": {
            "type": 'all',
            "event": "bgm.session",
        },
        "data": {
            "session_id": session_id
        }
    }
    print(sv.sm.sessions)
    await ws.send_json(res)


async def manage_session(sv, ws: WebSocket, session):
    if session['id']:
        del sv.sm.sessions[session['id']]
    else:
        await add_new_session(sv, ws, session['type'])


async def handler(sv, ws: WebSocket, data):
    session = data['session']
    ws_data = data['data'] if 'data' in data else None
    print(f"SESSION TYPE : {session['type']}")
    if session['event'].endswith('session'):
        await manage_session(sv, ws, session)
