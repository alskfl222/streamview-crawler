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
