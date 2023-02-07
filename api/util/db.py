#!/usr/bin/env python
# coding: utf-8

import os
import json
import requests
import boto3
from boto3.dynamodb.conditions import Attr
from dotenv import load_dotenv

class DB():
  def __init__(self):
    load_dotenv()
    self.dynamodb = boto3.resource('dynamodb')
    self.table_total = self.dynamodb.Table('total')
    self.table_monthly = self.dynamodb.Table('monthly')
    self.API_KEY = os.getenv('YOUTUBE_API_KEY')
    print("DB init")
    print()
    print(f"TOTAL LISTS: {len(self.table_monthly.scan()['Items'])}")
    print(f"TOTAL SONGS: {len(self.table_total.scan()['Items'])}")


  def get_query_string(self, query):
    query = { **query, "key": self.API_KEY }
    container = []
    for i in query.items():
      container.append(f"{i[0]}={i[1]}")
    query_string = f"?{'&'.join(container)}"
    return query_string


  def get_lists_all(self, base_url, query):
    query_string = self.get_query_string(query)
    url = f"{base_url}{query_string}"
    res = requests.get(url)
    if not res.ok:
      print(res.status_code)
      return []
    data = json.loads(res.content)
    lists = [
      {
        "title": x['snippet']['title'],
        "id": x['id']
      } for x in data['items']
    ]
    if "nextPageToken" in data:
      next_query = { **query, 'pageToken': data["nextPageToken"] }
      return [*lists, *self.get_lists_all(base_url, next_query)]
    return lists


  def get_playlists(self):
    base_url = 'https://www.googleapis.com/youtube/v3/playlists'
    query = {
      "part": "snippet",
      "channelId": "UCU5LUUBNDzGOeAri5Wk8w5Q",
      "maxResults": 50
    }  
    lists = self.get_lists_all(base_url, query)
    lists = [x for x in lists if x['title'].startswith('BGM')]
    lists = sorted(lists, key=lambda x: x['title'])
    return lists


  def get_list_items_all(self, base_url, query):
    query_string = self.get_query_string(query)
    url = f"{base_url}{query_string}"
    res = requests.get(url)
    if not res.ok:
      print(res.status_code)
      return []
    data = json.loads(res.content)
    list_items = [
      {
        "title": x['snippet']['title'],
        "id": x['snippet']['resourceId']['videoId'],
        "channel": x['snippet']['videoOwnerChannelTitle'] if 'videoOwnerChannelTitle' in x['snippet'] else 'unavailable',
        "channel_id": x['snippet']['videoOwnerChannelId'] if 'videoOwnerChannelTitle' in x['snippet'] else 'unavailable',
        "from": "list",
        "active": True if 'videoOwnerChannelTitle' in x['snippet'] else False
      } for x in data['items']
    ]
    if "nextPageToken" in data:
      next_query = { **query, 'pageToken': data["nextPageToken"] }
      return [*list_items, *self.get_list_items_all(base_url, next_query)]
    return list_items


  def get_playlist_items(self, playlist_id):
    base_url = 'https://www.googleapis.com/youtube/v3/playlistItems'
    query = {
      "part": "snippet",
      "playlistId": playlist_id,
      "maxResults": 50
    }
    list_items = self.get_list_items_all(base_url, query)
    return list_items

  def input_table_init(self):
    playlists = self.get_playlists()
    lists_items = [self.get_playlist_items(x['id']) for x in playlists]
    flatten_items = sum(lists_items, [])
    total_items = [dict(t) for t in {tuple(d.items()) for d in flatten_items}]

    with self.table_total.batch_writer() as batch:
      for item in total_items:
        batch.put_item(
          Item=item
        )
    with self.table_monthly.batch_writer() as batch:
      for idx, items in enumerate(lists_items):  
        row = {
          **playlists[idx],
          "items": items
        }
        batch.put_item(
          Item=row
        )


  def get_item_index(self, id, items):
    for idx, item in enumerate(items):
      if item['id'] == id:
        return idx
    return -1


  def get_update_params(self, body):
    # https://stackoverflow.com/a/62030403/15280469
    update_expression = ["set "]
    update_values = dict()

    for key, val in body.items():
        update_expression.append(f" {key} = :{key},")
        update_values[f":{key}"] = val

    return "".join(update_expression)[:-1], update_values


  def update_song_in_monthly(self, monthly_id, song_id, update_values):
    res_monthly = self.table_monthly.scan(
      FilterExpression=Attr('id').eq(monthly_id)
    )['Items'][0]
    items = res_monthly['items']
    item_index = self.get_item_index(song_id, items)
    prev_item = items.pop(item_index)
    new_item = {
      **prev_item,
      **update_values
    }
    items.insert(item_index, new_item)
    self.table_monthly.put_item(
      Item={
        **res_monthly,
        'items': items
      }
    )


  def update_song_in_total(self, song_id, update_values):
    a, v = self.get_update_params(update_values)
    self.table_total.update_item(
      Key={ 'id': song_id },
      UpdateExpression=a,
      ExpressionAttributeValues=dict(v)
    )


  def update_song(self, monthly_id, song_id, update_values):
    self.update_song_in_monthly(monthly_id, song_id, update_values)
    self.update_song_in_total(song_id, update_values)


