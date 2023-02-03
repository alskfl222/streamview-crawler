from fastapi.websockets import WebSocket

async def play_video(sv, ws: WebSocket, data):
  print(f"START VIDEO: {data}")
  # await ws.send_json(data)

async def pause_video(sv, ws: WebSocket, data):
  print(f"PAUSE VIDEO: {data}")
  # await ws.send_json(data)

async def append_list(sv, ws: WebSocket, data):
  print(f"APPEND VIDEO: {data}")
  sv.queue.append(data)
  res = {
    "event": {
      "type": 'bgm',
      "name": "queue"
    },
    "data": {
      "queue": sv.queue
    }
  }
  await ws.send_json(res)

async def handler(sv, ws, ev_name, data):
  if ev_name == 'play': await play_video(sv, ws, data),
  if ev_name == 'pause': await pause_video(sv, ws, data),
  if ev_name == 'append': await append_list(sv, ws, data),
