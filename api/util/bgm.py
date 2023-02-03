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
  if not sv.finder.initiated:
    await sv.finder.init()
  # await ws.send_json(data)

async def stop_video(sv, ws: WebSocket, data):
  print(f"STOP VIDEO: {data}")
  cand_list = [x for x in sv.original if x not in sv.queue]
  new_idx = randint(0, len(cand_list) - 1)
  print(new_idx)
  # TODO : 새로운 곡 추가
  sv.queue = [*sv.queue[1:], cand_list[new_idx]]
  await send_queue(sv, ws, 'stop')


async def pause_video(sv, ws: WebSocket, data):
  print(f"PAUSE VIDEO: {data}")
  # await ws.send_json(data)

async def append_list(sv, ws: WebSocket, data):
  print(f"APPEND VIDEO ID: {data['query']}")
  print(f"APPEND VIDEO FROM: {data['from']}")
  name, song_id = await sv.finder.find_song(data['query'])
  print(name, song_id)
  if song_id in [x['id'] for x in sv.queue]:
    await send_queue(sv, ws, 'duplicated')
  else:
    insert = { "name": name, "id": song_id, "from": data['from'] }
    sv.queue = [sv.queue[0], insert, *sv.queue[1:-1]]
    await send_queue(sv, ws, 'inserted')

async def handler(sv, ws, ev_name, data):
  if ev_name == 'play': await play_video(sv, ws, data),
  if ev_name == 'stop': await stop_video(sv, ws, data),
  if ev_name == 'pause': await pause_video(sv, ws, data),
  if ev_name == 'append': await append_list(sv, ws, data),
