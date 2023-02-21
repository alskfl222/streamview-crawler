#!/usr/bin/env python
# coding: utf-8

from multiprocessing import Queue, Process, active_children

import pytchat

from process import comsumer


STREAMING_ID = 'jG4UpblhrGk'
chat = pytchat.create(video_id=STREAMING_ID)
queue = Queue()
sub_process = Process(target=comsumer, args=(queue,), daemon=True)

command = {
    '신청곡': 'append',
    '다음곡': 'next'
}

def handle_message(queue: Queue, message):
    args = message.split(' ')
    command_key = args[0][1:]
    if args[0].startswith("!") and command_key in command.keys():
        queue.put((command[command_key], args[1:]))

def main():
    print('MAIN START')
    sub_process.start()
    while chat.is_alive():
        try:
            data = chat.get()
            items = data.items
            for item in items:
                print(
                    f"{item.datetime} : {item.author.name} [{item.author.isChatOwner}] - {item.message}")
                handle_message(queue, item.message)
        except:
            print("BREAK")
            chat.terminate()
            break


if __name__ == "__main__":
    main()

    for child in active_children():
        child.kill()

    print(active_children())
    print(sub_process.is_alive())

