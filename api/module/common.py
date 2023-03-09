from datetime import datetime


def get_current_time(sv):
    print(sv.bgm['currentTime'])
    return round(float((datetime.now() - sv.bgm['updateTime']).total_seconds()), 3) + sv.bgm['currentTime']


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
