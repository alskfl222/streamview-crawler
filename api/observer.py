#!/usr/bin/env python
# coding: utf-8

import os
import sys
import traceback
import json
import websocket
import pytchat
from dotenv import load_dotenv

load_dotenv()

os.environ["PYTHONUNBUFFERED"] = "1"
WS_SERVER = os.getenv('WS_SERVER_LOCAL')


class Observer():
    def __init__(self, stream_id):
        print(f"STREAM_ID : {stream_id}")
        print()
        self.chat = pytchat.create(video_id=stream_id)
        self.commands = {
            '신청곡': 'append',
            '다음곡': 'next'
        }

    def handle_message(self, message):
        args = message.split(' ')
        command = args[0][1:]
        if args[0].startswith("!") and command in self.commands.keys():
            return command, args[1:]
        return None, None

    def send_ws(self, command, args):
        ws = websocket.WebSocket()
        ws.connect(WS_SERVER)
        data = {
            "event": {
                "type": "obs",
                "name": f"obs.{self.commands[command]}"
            },
            "data": {
                "query": ' '.join(args),
                "from": 'chat'
            }
        }
        ws.send(json.dumps(data))
        ws.close()

    def run(self):
        print('OBSERVER START')
        while self.chat.is_alive():
            try:
                data = self.chat.get()
                items = data.items
                for item in items:
                    print(
                        f"{item.datetime} : {item.author.name} [{item.author.isChatOwner}] - {item.message}")
                    command, args = self.handle_message(item.message)
                    if command and args:
                        self.send_ws(command, args)
            except:
                traceback.print_exc()
                print("BREAK")
                self.chat.terminate()
                break


if __name__ == '__main__':
    stream_id = sys.argv[1]
    observer = Observer(stream_id)
    observer.run()
