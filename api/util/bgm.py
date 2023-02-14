from random import randint
from fastapi.websockets import WebSocket


async def send_queue(sv, ws: WebSocket, message):
    res = {
        "event": {
            "type": 'bgm',
            "name": "queue",
            "message": message
        },
        "data": {
            "queue": sv.queue
        }
    }
    await ws.send_json(res)


async def play_video(sv, ws: WebSocket, data):
    print(f"START VIDEO: {data}")
    if not sv.bgm_active:
        print("정지 후 재생")
        sv.bgm_active = True
    else:
        print("스트림 목록 업데이트")
        sv.db.append_streamed(data)
    # await ws.send_json(data)


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
    # await ws.send_json(data)


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


async def handler(sv, ws: WebSocket, ev_name, data):
    if ev_name == 'play':
        await play_video(sv, ws, data),
    if ev_name == 'stop':
        await stop_video(sv, ws, data),
    if ev_name == 'pause':
        await pause_video(sv, ws, data),
    if ev_name == 'append':
        await append_list(sv, ws, data),
    if ev_name == 'inactive':
        await update_inactive(sv, ws, data),
