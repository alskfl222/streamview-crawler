import math
from datetime import datetime, timedelta
from random import randint
from fastapi.websockets import WebSocket


async def send_queue(sv, ws: WebSocket, message):
    res = {
        "session": {
            "type": 'all',
            "event": "bgm.queue",
            "message": message
        },
        "data": {
            "queue": sv.queue
        }
    }
    await sv.sm.emit_all(res)


async def play_video(sv, ws: WebSocket, data):
    print(f"START VIDEO: {data}")
    if not sv.bgm_active:
        print("정지 후 재생")
        sv.bgm_start_time = datetime.now(
        ) - timedelta(seconds=float(data['current']))
        sv.bgm_active = True
    else:
        print("스트림 목록 업데이트")
        sv.bgm_start_time = datetime.now()
        sv.db.append_streamed(data)
    res = {
        "session": {
            "type": 'viewer',
            "event": "bgm.current_time",
        },
        "data": {
            "state": "start",
            "current_time": data['current']
        }
    }
    await sv.sm.emit_viewer(res)


async def stop_video(sv, ws: WebSocket, data):
    print(f"STOP VIDEO: {data}")
    cand_list = [x for x in sv.original if x not in sv.queue]
    new_idx = randint(0, len(cand_list) - 1)
    print(f"NEW ITEM: {cand_list[new_idx]}")
    # TODO : 새로운 곡 추가
    sv.queue = [*sv.queue[1:], cand_list[new_idx]]
    await send_queue(sv, ws, 'stop')


async def pause_video(sv, ws: WebSocket, data):
    print(f"PAUSE VIDEO: {data}")
    sv.bgm_active = False
    res = {
        "session": {
            "type": 'viewer',
            "event": "bgm.current_time",
        },
        "data": {
            "state": "pause",
            "current_time": data['current']
        }
    }
    await sv.sm.emit_viewer(res)


async def buffering_video(sv, ws: WebSocket, data):
    print(f"BUFFERING VIDEO: {data}")
    res = {
        "session": {
            "type": 'viewer',
            "event": "bgm.current_time",
        },
        "data": {
            "state": "pause",
            "current_time": data['current']
        }
    }
    await sv.sm.emit_viewer(res)


async def append_list(sv, ws: WebSocket, data):
    print(f"QUERY: {data['query']}")
    print(f"FROM: {data['from']}")
    insert_item = await sv.finder.find_song(data['query'])
    requested_queue = [x for x in sv.queue[1:] if x['from'] != "list"]
    rest_queue = [x for x in sv.queue[1:] if x['from'] == "list"]
    if not insert_item:
        print("CANNOT FOUND")
        await send_queue(sv, ws, 'not found')
    elif insert_item['id'] in [x['id'] for x in requested_queue]:
        print("DUPLICATED")
        await send_queue(sv, ws, 'duplicated')
    else:
        insert_item = {**insert_item, "from": data["from"]}
        sv.queue = [sv.queue[0], *requested_queue,
                    insert_item, *rest_queue][:10]
        print(f"APPEND VIDEO: {insert_item}")
        await send_queue(sv, ws, 'inserted')


async def update_inactive(sv, ws: WebSocket, data):
    print(data)


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
    if session['event'].endswith('play'):
        await play_video(sv, ws, ws_data),
    if session['event'].endswith('stop'):
        await stop_video(sv, ws, ws_data),
    if session['event'].endswith('pause'):
        await pause_video(sv, ws, ws_data),
    if session['event'].endswith('buffering'):
        await buffering_video(sv, ws, ws_data),
    if session['event'].endswith('append'):
        await append_list(sv, ws, ws_data),
    if session['event'].endswith('inactive'):
        await update_inactive(sv, ws, ws_data),
    if session['event'].endswith('session'):
        await manage_session(sv, ws, session)
