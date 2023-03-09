async def send_res(sv, data, message):
    res = {
        "event": {
            "to": 'all',
            "name": "bgm.queue",
            "message": message
        },
        "data": {
            "queue": sv.queue,
            "list_title": sv.db.latest_list['title'],
            "state": "start",
            "currentTime": data['current'] if 'current' in data else '0',
            "duration": data['duration'] if 'duration' in data else '0'
        }
    }
    await sv.sm.emit_all(res)