import os
import queue
import json
import websocket

from dotenv import load_dotenv

load_dotenv()

WS_SERVER = os.getenv('WS_SERVER_LOCAL')


def comsumer(q):
    print("CONSUMER START")
    while True:
        try:
            command = q.get(block=False)
            ws = websocket.WebSocket()
            ws.connect(WS_SERVER)
            data = {
                "session": {
                    "type": "obs",
                    "event": f"obs.{command[0]}"
                },
                "data": {
                    "query": command[1],
                    "from": 'chat'
                }
            }
            ws.send(json.dumps(data))
            ws.close()
        except queue.Empty:
            pass
        except:
            print("QWER")
            break