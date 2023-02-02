#!/usr/bin/env python
# coding: utf-8

import os
import traceback
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocket
import uvicorn
from dotenv import load_dotenv

load_dotenv()
PORT = int(os.getenv('PORT'))

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get_index():
  return "Hello World!"

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
  await websocket.accept()
  while True:
    data = await websocket.receive_json()
    try:
      print(data["a"])
    except:
      traceback.print_exc()
      pass
    await websocket.send_json(f"Message text was: {data}")

if __name__ == "__main__":
  uvicorn.run(app=app, host='0.0.0.0', port=PORT)

