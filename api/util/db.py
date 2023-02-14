#!/usr/bin/env python
# coding: utf-8

import datetime
import os
import json
import requests
import boto3
from boto3.dynamodb.conditions import Key, Attr
from dotenv import load_dotenv


class DB():
    def __init__(self):
        load_dotenv()
        print()
        print("DB init")
        self.stream_time = f"{datetime.datetime.now():%Y-%m-%d_%H:%M:%S}"
        self.API_KEY = os.getenv('YOUTUBE_API_KEY')
        print(f"INIT TIME : {self.stream_time}")
        print()
        self.dynamodb = boto3.resource('dynamodb')
        self.total = self.dynamodb.Table('total')
        self.monthly = self.dynamodb.Table('monthly')
        self.streamed = self.dynamodb.Table('streamed')

        self.total_list = self.get_total_list()
        lists_count, new_total_list = self.check_update_monthly()
        if new_total_list:
            self.total_list = new_total_list

        self.stream_list = []

        print()
        print(f"TOTAL LISTS: {lists_count}")
        print(f"TOTAL SONGS: {len(self.total.scan()['Items'])}")
        print()

    def get_total_list(self):
        return self.total.scan()['Items']

    def get_query_string(self, query):
        query = {**query, "key": self.API_KEY}
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
            next_query = {**query, 'pageToken': data["nextPageToken"]}
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
            next_query = {**query, 'pageToken': data["nextPageToken"]}
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

    def input_init(self):
        playlists = self.get_playlists()
        lists_items = [self.get_playlist_items(x['id']) for x in playlists]
        flatten_items = sum(lists_items, [])
        total_items = [dict(t)
                       for t in {tuple(d.items()) for d in flatten_items}]

        with self.total.batch_writer() as batch:
            for item in total_items:
                batch.put_item(
                    Item=item
                )
        with self.monthly.batch_writer() as batch:
            for idx, items in enumerate(lists_items):
                row = {
                    **playlists[idx],
                    "items": items
                }
                batch.put_item(
                    Item=row
                )

    def check_update_monthly(self):
        playlists = self.get_playlists()
        exist_list = [x['title'] for x in self.monthly.scan()['Items']]
        new_list = [x for x in playlists if x['title'] not in exist_list]
        if new_list:
            print(f"FOUND new {len(new_list)} LIST")

            new_lists_items = []
            for each_list in new_list:
                print(f"UPDATE {each_list['title']}")
                list_items = self.get_playlist_items(each_list['id'])

                row = {
                    **each_list,
                    "items": list_items
                }
                self.monthly.put_item(
                    Item=row
                )
                print(f"DB MONTHLY UPDATED : {each_list['title']}")
                new_list_items = [
                    x for x in list_items if not self.check_exist(x)]
                new_lists_items.extend(new_list_items)

            if new_lists_items:
                with self.total.batch_writer() as batch:
                    for item in new_list_items:
                        batch.put_item(
                            Item=item
                        )
                print(f"DB TOTAL UPDATED : {len(new_lists_items)}")
                return len(exist_list) + len(new_list), new_lists_items
            return len(exist_list) + len(new_list), None
        else:
            print("NO new MONTHLY LIST")
            return len(exist_list), None

    def get_last_streamed_song(self):
        try:
            last_streamed_list = self.streamed.scan(Limit=1)
            last_streamed_song = last_streamed_list['Items'][-1]['items'][-1]
            return last_streamed_song
        except:
            return None

    def get_monthly_list_active(self):
        res = self.monthly.scan(Limit=1)
        item = res['Items'][0]
        monthly_list = item['items']
        monthly_list_active = [x for x in monthly_list if x["active"]]
        last_streamed_song = self.get_last_streamed_song()
        if last_streamed_song:
            return [last_streamed_song, *monthly_list_active]
        else:
            return monthly_list_active

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
        res_monthly = self.monthly.scan(
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
        self.monthly.put_item(
            Item={
                **res_monthly,
                'items': items
            }
        )

    def update_song_in_total(self, song_id, update_values):
        a, v = self.get_update_params(update_values)
        self.total.update_item(
            Key={'id': song_id},
            UpdateExpression=a,
            ExpressionAttributeValues=dict(v)
        )

    def update_song(self, monthly_id, song_id, update_values):
        self.update_song_in_monthly(monthly_id, song_id, update_values)
        self.update_song_in_total(song_id, update_values)

    def check_exist(self, item):
        return item['id'] in [x['id'] for x in self.total_list]

    def append_streamed(self, item):
        row = {**item, "time": f"{datetime.datetime.now():%Y-%m-%d_%H:%M:%S}"}
        del row['current']
        self.stream_list = [*self.stream_list, row]
        new_item = {
            "datetime": self.stream_time,
            "items": self.stream_list
        }
        self.streamed.put_item(
            Item=new_item
        )
        if not self.check_exist(item):
            print("ADDED NEW IN TOTAL TABLE")
            self.total_list = [*self.total_list, item]
            self.total.put_item(
                Item=item
            )
