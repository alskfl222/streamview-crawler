from .common import send_res

async def append_list(sv, data):
    print(f"QUERY: {data['query']}")
    print(f"FROM: {data['from']}")
    insert_item = await sv.finder.find_song(data['query'])
    requested_queue = [x for x in sv.queue[1:] if x['from'] != "list"]
    rest_queue = [x for x in sv.queue[1:] if x['from'] == "list"]
    if not insert_item:
        print("CANNOT FOUND")
        await send_res(sv)
    elif insert_item['id'] in [x['id'] for x in requested_queue]:
        print("DUPLICATED")
        await send_res(sv)
    else:
        insert_item = {**insert_item, "from": data["from"]}
        sv.queue = [sv.queue[0], *requested_queue,
                    insert_item, *rest_queue][:10]
        print(f"APPEND VIDEO: {insert_item}")
        await send_res(sv)

async def next_song(sv):
    res = {
        "event": {
            "to": 'stream',
            "name": "obs.next",
        },
        "data": {
            "song": sv.queue[1]
        }
    }
    await sv.sm.emit_stream(res)

async def handler(sv, data):
    event = data['event']
    ws_data = data['data'] if 'data' in data else None
    print(f"EVENT : {event}")
    print(f"DATA : {ws_data}")
    if event['name'].endswith('append'):
        await append_list(sv, ws_data)
    if event['name'].endswith('next'):
        await next_song(sv)
