#!/usr/bin/env python
# coding: utf-8

import time
from playwright.async_api import async_playwright

class Finder():
  def __init__(self):
    self.video_base_url = 'https://www.youtube.com/watch?v='
    self.search_base_url = 'https://www.youtube.com/results?search_query='
    self.initiated = False

  async def init(self):
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch()
    context = await browser.new_context()
    await context.route('**/*', lambda route: route.continue_())
    page = await context.new_page()
    self.playwright = playwright
    self.page = page
    self.initiated = True

  async def find_song(self, query):
    if not self.page:
      print('init Finder first!')
      return
    try:
      print(f"{self.video_base_url}{query}")
      await self.page.goto(f"{self.video_base_url}{query}")

      retry = 0
      while retry < 3:
        time.sleep(1)
        title_el = self.page.locator('div#title h1 yt-formatted-string')
        title_count = await title_el.count()
        print(f"title count : {title_count}")
        if title_count:
          return await title_el.nth(0).text_content().split('/')[-1], query
        print(f'retry : {retry}')
        retry += 1
      await self.page.goto(f"{self.search_base_url}{query}")
      items_el = self.page.locator('div#contents > ytd-video-renderer')
      items_count = await items_el.count()
      if items_count:
        item_name = await items_el.nth(0).locator('a#video-title > yt-formatted-string').text_content()
        item_id = await items_el.nth(0).locator('a#video-title').get_attribute('href')
        return (item_name, item_id.split('=')[-1])
      else:
        return None, None
    except:
      print('check error!')
      return None, None

