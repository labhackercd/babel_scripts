# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from .items import SenatorItem, InterventionItem
from decouple import config
import requests
BABEL_API_URL = config('BABEL_API_URL',
                       default='http://localhost:8000/api/v1/')
CHANNEL_ID = config('CHANNEL_ID',
                    default=5)
MANIFESTATION_TYPE_ID = config('MANIFESTATION_TYPE_ID', default=3)
COLLECT_ID = config('COLLECT_ID', default=3)
AUTH_TOKEN = config('AUTH_TOKEN', default='')


class DiscursosChilePipeline(object):
    profiles = {}

    def process_item(self, item, spider):
        if isinstance(item, SenatorItem):
            author_data = {
                'name': item['name'],
                'author_type': 'Senador CL',
            }
            author = requests.post(BABEL_API_URL + 'authors/',
                                   json=author_data,
                                   headers={
                                       'Authorization': 'Token %s' % AUTH_TOKEN
                                   }).json()

            profile_data = {
                'channel_id': CHANNEL_ID,
                'author_id': author['id'],
                'url': item['url'],
                'id_in_channel': item['senator_id'],
                'is_reference': 'true',
                'attrs': [
                    {'field': 'name', 'value': item['name']},
                    {'field': 'party', 'value': item['party']},
                    {'field': 'phone', 'value': item['phone']},
                    {'field': 'email', 'value': item['email']},
                    {'field': 'region', 'value': item['region']},
                ]
            }
            profile = requests.post(BABEL_API_URL + 'profiles/',
                                    json=profile_data,
                                    headers={
                                        'Authorization': 'Token %s' % AUTH_TOKEN
                                    }).json()
            self.profiles[item['senator_id']] = profile['id']

        if isinstance(item, InterventionItem):
            intervention_data = {
                'manifestation_type_id': MANIFESTATION_TYPE_ID,
                'profile_id': self.profiles[item['senator_id']],
                'collect_id': COLLECT_ID,
                'id_in_channel': item['url'],
                'content': item['speech'],
                'timestamp': item['date'],
                'url': item['url'],
                'attrs': [],
            }
            requests.post(BABEL_API_URL + 'manifestations/',
                          json=intervention_data,
                          headers={'Authorization': 'Token %s' % AUTH_TOKEN})

        return item
