import datetime
import requests
import sys

from get_fb_posts_fb_page import scrapeFacebookPageFeedStatus
from decouple import config

# Facebook Capture details
BABEL_API_URL = config('BABEL_API_URL', default='http://localhost:8000/api/v1/')
APP_ID = config('APP_ID', default='')
APP_SECRET = config('APP_SECRET', default='')
CHANNEL_ID = config('CHANNEL_ID', default='')
AUTH_TOKEN = config('AUTH_TOKEN', default='')
access_token = APP_ID + "|" + APP_SECRET


def process_statuses(profile, statuses):
    for status in statuses:
        data = {
            'manifestation_type_id': '1',  # Manifestation type "facebook posts"
            'profile_id': profile['id'],
            'id_in_channel': status['status_id'],
            'content': status['status_message'],
            'timestamp': status['status_published'],
            'url': status['status_link'],
            'attrs': [
                {'field': 'status_id', 'value': status['status_id']},
                {'field': 'link_name', 'value': status['link_name']},
                {'field': 'status_type', 'value': status['status_type']},
                {'field': 'status_link', 'value': status['status_link']},
                {'field': 'status_published',
                 'value': status['status_published']},
                {'field': 'num_reactions', 'value': status['num_reactions']},
                {'field': 'num_comments', 'value': status['num_comments']},
                {'field': 'num_shares', 'value': status['num_shares']},
                {'field': 'num_likes', 'value': status['num_likes']},
                {'field': 'num_loves', 'value': status['num_loves']},
                {'field': 'num_wows', 'value': status['num_wows']},
                {'field': 'num_hahas', 'value': status['num_hahas']},
                {'field': 'num_sads', 'value': status['num_sads']},
                {'field': 'num_angrys', 'value': status['num_angrys']},
                {'field': 'num_special', 'value': status['num_special']},
            ],
        }
        ret = requests.post(
            BABEL_API_URL + 'manifestations',
            json=data,
            headers={
                'Authorization': 'Token %s' % AUTH_TOKEN
            })
        if ret.status_code == 201:
            sys.stdout.write('.')
            sys.stdout.flush()
        else:
            print(data)
            print(ret.status_code, ret.content)


next_url = BABEL_API_URL + "profiles?channel__id=%s" % CHANNEL_ID
while next_url is not None:
    profiles = requests.get(next_url).json()
    for profile in profiles['results']:
        # input date formatted as YYYY-MM-DD
        since_date = (
            datetime.datetime.now() - datetime.timedelta(days=14)
        ).strftime("%Y-%m-%d")
        until_date = datetime.datetime.now().strftime("%Y-%m-%d")

        page_id = profile['id_in_channel']

        statuses = scrapeFacebookPageFeedStatus(
            page_id, access_token, since_date=since_date, until_date=until_date)

        if statuses is not False:
            process_statuses(profile, statuses)

    # Next page
    next_url = profiles.get('next', None)
