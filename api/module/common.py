from datetime import datetime


def get_current_time(sv):
    print(sv.bgm['currentTime'])
    return sv.bgm['currentTime'] if sv.bgm['currentTime'] != 0 else round(float((datetime.now() - sv.bgm['startTime']).total_seconds()), 3)


def update_bgm(sv, data):
    sv.bgm = {
        **sv.bgm,
        "currentTime": float(data['current']) if 'current' in data else 0,
        "duration": float(data['duration']) if 'current' in data else 0
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
                "startTime": f"{sv.bgm['startTime']}"}
        }
    }
    await sv.sm.emit_all(res)
