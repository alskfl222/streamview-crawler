from fastapi.websockets import WebSocket

async def send_queue(sv, message):
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

async def next_song(sv):
    res = {
        "session": {
            "type": 'all',
            "event": "obs.next",
        },
        "data": {
            "song": sv.queue[1]
        }
    }
    await sv.sm.emit_all(res)

async def append_list(sv, data):
    print(f"QUERY: {data['query']}")
    print(f"FROM: {data['from']}")
    insert_item = await sv.finder.find_song(data['query'])
    requested_queue = [x for x in sv.queue[1:] if x['from'] != "list"]
    rest_queue = [x for x in sv.queue[1:] if x['from'] == "list"]
    if not insert_item:
        print("CANNOT FOUND")
        await send_queue(sv, 'not found')
    elif insert_item['id'] in [x['id'] for x in requested_queue]:
        print("DUPLICATED")
        await send_queue(sv, 'duplicated')
    else:
        insert_item = {**insert_item, "from": data["from"]}
        sv.queue = [sv.queue[0], *requested_queue,
                    insert_item, *rest_queue][:10]
        print(f"APPEND VIDEO: {insert_item}")
        await send_queue(sv, 'inserted')

async def handler(sv, data):
    session = data['session']
    ws_data = data['data'] if 'data' in data else None
    print(f"SESSION TYPE : {session['type']}")
    print(f"DATA : {ws_data}")
    if session['event'].endswith('next'):
        await next_song(sv),
    if session['event'].endswith('append'):
        await append_list(sv, ws_data),
