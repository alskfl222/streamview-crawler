from datetime import datetime

def arrange_bgm(sv):
    sv.bgm = {
        **sv.bgm,
        "startTime": datetime.now(),
        "currentTime": 0,
        "duration": 0
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
            "bgm": sv.bgm
        }
    }
    await sv.sm.emit_all(res)