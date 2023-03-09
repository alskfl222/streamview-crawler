from random import randint
from fastapi.websockets import WebSocket

from .common import send_res


async def play_video(sv, data):
    print(f"START VIDEO: {data}")
    if not sv.bgm_active:
        print("정지 후 재생")
        sv.bgm_active = True
    else:
        print("스트림 목록 업데이트")
        sv.db.append_streamed(data)
    await send_res(sv, data, 'start')


async def stop_video(sv, data):
    print(f"STOP VIDEO: {data}")
    cand_list = [x for x in sv.original if x not in sv.queue]
    new_idx = randint(0, len(cand_list) - 1)
    print(f"NEW ITEM: {cand_list[new_idx]}")
    sv.queue = [*sv.queue[1:], cand_list[new_idx]]
    await send_res(sv, data, 'stop')


async def pause_video(sv, data):
    print(f"PAUSE VIDEO: {data}")
    sv.bgm_active = False
    await send_res(sv, data, 'pause')


async def buffering_video(sv, data):
    print(f"BUFFERING VIDEO: {data}")
    await send_res(sv, data, 'buffering')


async def append_list(sv, data):
    print(f"QUERY: {data['query']}")
    print(f"FROM: {data['from']}")
    insert_item = await sv.finder.find_song(data['query'])
    requested_queue = [x for x in sv.queue[1:] if x['from'] != "list"]
    rest_queue = [x for x in sv.queue[1:] if x['from'] == "list"]
    if not insert_item:
        print("CANNOT FOUND")
        await send_res(sv, data, 'not found')
    elif insert_item['id'] in [x['id'] for x in requested_queue]:
        print("DUPLICATED")
        await send_res(sv, data, 'duplicated')
    else:
        insert_item = {**insert_item, "from": data["from"]}
        sv.queue = [sv.queue[0], *requested_queue,
                    insert_item, *rest_queue][:10]
        print(f"APPEND VIDEO: {insert_item}")
        await send_res(sv, data, 'inserted')


async def delete_queue(sv, data):
    print(f"DELETE VIDEO: {sv.queue[data['idx']]}")
    cand_list = [x for x in sv.original if x not in sv.queue]
    new_idx = randint(0, len(cand_list) - 1)
    print(f"NEW ITEM: {cand_list[new_idx]}")
    sv.queue = [*sv.queue[0:data['idx']], *
                sv.queue[data['idx']+1:], cand_list[new_idx]]
    await send_res(sv, data, 'deleted')


async def update_monthly_list(sv):
    print("UPDATE CHECK START")
    sv.db.check_update_monthly()
    sv.original = sv.db.get_monthly_list_active()
    await sv.sm.emit_all({'message': 'update list'})


async def song_inactive(sv, ws: WebSocket, data):
    print(data)


async def handler(sv, ws: WebSocket, data):
    event = data['event']
    ws_data = data['data'] if 'data' in data else None
    print(f"event FROM : {event['from']}")
    if event['name'].endswith('play'):
        await play_video(sv, ws_data),
    if event['name'].endswith('stop'):
        await stop_video(sv, ws_data),
    if event['name'].endswith('pause'):
        await pause_video(sv, ws_data),
    if event['name'].endswith('buffering'):
        await buffering_video(sv, ws_data),
    if event['name'].endswith('append'):
        await append_list(sv, ws_data),
    if event['name'].endswith('delete'):
        await delete_queue(sv, ws_data)
    if event['name'].endswith('update'):
        await update_monthly_list(sv),
    if event['name'].endswith('inactive'):
        await song_inactive(sv, ws, ws_data),
    # if event['name'].endswith('session'):
    #     await manage_session(sv, ws, event)
