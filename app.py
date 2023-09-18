from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import queue
import threading
import asyncio
import time

app = FastAPI()

request_queue = queue.Queue()
response_delay = [2, 1]

def worker(worker_num):
    while True:
        websocket, data = request_queue.get()  # 큐에서 웹소켓 및 데이터를 가져옵니다.
        if websocket is None:
            break
        delay = response_delay[worker_num]
        time.sleep(delay)
        response = f"Worker {worker_num + 1}: response after {delay} seconds: {data}"
        asyncio.run(websocket.send_text(response))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            request_queue.put((websocket, data))  # 웹소켓 및 데이터를 큐에 넣습니다.
        except WebSocketDisconnect:
            break

if __name__ == "__main__":
    for i in range(2):  # 2개의 워커 스레드를 시작합니다.
        threading.Thread(target=worker, args=(i,), daemon=True).start()
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)