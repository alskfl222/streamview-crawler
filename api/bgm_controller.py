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

bgm_controller = {
  'play': play_video,
  'pause': pause_video,
  'append': append_list,
}