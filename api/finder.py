#!/usr/bin/env python
# coding: utf-8

import sys
import os
import traceback
import time
import json
import websocket
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

WS_SERVER = os.getenv("WS_SERVER_CLOUD") if os.getenv(
    "PY_ENV") == "production" else os.getenv("WS_SERVER_LOCAL")

video_base_url = 'https://www.youtube.com/watch?v='
search_base_url = 'https://www.youtube.com/results?search_query='
initiated = False

def send_ws(song_item, req_from):
    ws = websocket.WebSocket()
    ws.connect(WS_SERVER)
    data = {
        "event": {
            "from": "finder",
            "name": "bgm.append"
        },
        "data": {
            "song": song_item,
            "from": req_from
        }
    }
    ws.send(json.dumps(data))
    ws.close()


playwright = sync_playwright().start()
browser = playwright.chromium.launch()
context = browser.new_context()
context.route('**/*', lambda route: route.continue_())
page = context.new_page()
playwright = playwright
page = page


def find_song(query):
    print("TRY ID URI")
    try:
        page.goto(f"{video_base_url}{query}")

        retry = 0
        while retry < 3:
            time.sleep(1)
            title_el = page.locator(
                'div#title h1 yt-formatted-string')
            title_count = title_el.count()
            if title_count:
                item_title_raw = title_el.nth(0).text_content()
                item_title = item_title_raw.split('/')[-1]
                item_id = query
                channel_info = page.locator(
                    "div#owner div#text-container.ytd-channel-name a")
                channel = channel_info.nth(0).text_content()
                channel_id_raw = channel_info.nth(0).get_attribute('href')
                channel_id = channel_id_raw[1:] if channel_id_raw[0] == "@" else channel_id_raw.split(
                    '/')[-1]
                item = {
                    "title": item_title,
                    "id": item_id,
                    "channel": channel,
                    "channel_id": channel_id,
                    "available": True,
                }
                return item
            retry += 1
            print("CANNOT FOUND BY VIDEO ID")
            print("TRY SEARCH QUERY")
            page.goto(f"{search_base_url}{query}")
            items_el = page.locator('div#contents > ytd-video-renderer')
            items_count = items_el.count()

            if items_count:
                target_item = items_el.nth(0)
                item_title = target_item.locator('a#video-title > yt-formatted-string').text_content()
                item_id_raw = target_item.locator('a#video-title').get_attribute('href')
                item_id = item_id_raw.split("=")[-1]
                channel = target_item.locator('div#channel-info div.ytd-channel-name a').text_content()
                channel_id_raw = target_item.locator('div#channel-info div.ytd-channel-name a').get_attribute('href')
                channel_id = channel_id_raw[1:] if channel_id_raw[0] == "@" else channel_id_raw.split(
                    '/')[-1]
                item = {
                    "title": item_title,
                    "id": item_id,
                    "channel": channel,
                    "channel_id": channel_id,
                    "available": True,
                }
                return item
            else:
                print('error?')
                traceback.print_exc()
                return None
    except:
        print('check error!')
        traceback.print_exc()
        return None


if __name__ == '__main__':
    req_from = sys.argv[1]
    query = " ".join(sys.argv[2:])
    try:
        song = find_song(query)
        send_ws(song, req_from)
    except:
        traceback.print_exc()
        sys.exit(0)
