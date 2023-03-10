from datetime import datetime

async def init_list(sv, websocket):
    res = {
        "event": {
            "to": 'all',
            "name": "bgm.queue",
            "message": "init"
        },
        "data": {
            "queue": sv.queue,
            "listTitle": sv.db.latest_list['title'],
            "bgm": {
                **sv.bgm,
                "updateTime": f"{sv.bgm['updateTime']}",
                "currentTime": get_current_time(sv),
            },
        }
    }
    await websocket.send_json(res)

def get_current_time(sv):
    current_time = sv.bgm['currentTime']
    past_time = round(float((datetime.now() - sv.bgm['updateTime']).total_seconds()), 3)
    if (sv.bgm['active']):
        current_time += past_time
    return current_time


def update_bgm(sv, data):
    sv.bgm = {
        **sv.bgm,
        "updateTime": datetime.now(),
        "currentTime": float(data['current']) if 'current' in data else sv.bgm['currentTime'],
        "duration": float(data['duration']) if 'current' in data else sv.bgm['duration']
    }


async def send_res(sv, message):
    res = {
        "event": {
            "to": 'all',
            "name": "bgm.queue",
            "message": message
        },
        "data": {
            "queue": sv.queue,
            "listTitle": sv.db.latest_list['title'],
            "bgm": {
                **sv.bgm,
                "updateTime": f"{sv.bgm['updateTime']}"}
        }
    }
    await sv.sm.emit_all(res)
