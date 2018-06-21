import datetime
import json
import requests
import sys
import time
from decouple import config

# Facebook Capture details
BABEL_API_URL = config('BABEL_API_URL', default='http://localhost:8000/api/v1/')
APP_ID = config('APP_ID', default='')
APP_SECRET = config('APP_SECRET', default='')
CHANNEL_ID = config('CHANNEL_ID', default='')
AUTH_TOKEN = config('AUTH_TOKEN', default='')
access_token = APP_ID + "|" + APP_SECRET


def request_until_succeed(url):
    is_done = False
    while is_done is False:
        try:
            ret = requests.get(url)
            if ret.status_code == 200 or ret.status_code == 400:
                is_done = True
        except Exception as e:
            print(e)
            time.sleep(5)

            print("Error for URL {}: {}".format(url, datetime.datetime.now()))
            print("Retrying.")

    return ret


# Needed to write tricky unicode correctly to csv
def unicode_decode(text):
    try:
        return text.encode('utf-8').decode()
    except UnicodeDecodeError:
        return text.encode('utf-8')


def scrapeFacebookPage(page_id, access_token):
    base = "https://graph.facebook.com/v2.11"
    node = "/{}".format(page_id)

    parameters = ("/?fields=about,best_page,can_post,category,category_list," +
                  "description,description_html,general_info,personal_info," +
                  "personal_interests,username,website,fan_count&" +
                  "access_token={}".format(access_token))

    url = base + node + parameters

    ret = request_until_succeed(url)
    if ret.status_code == 200:
        page_data = json.loads(ret.content)
        return page_data
    else:
        print("\n", ret.status_code, ret.url, ret.content, "\n")
        return False


def process_page(profile, page_data):
    author_id = profile['author'].rsplit('/', 1)[-1]
    channel_id = profile['channel'].rsplit('/', 1)[-1]
    data = {
        'id': profile['id'],
        'author_id': author_id,
        'channel_id': channel_id,
        'url': profile['url'],
        'id_in_channel': profile['id_in_channel'],
        'is_reference': profile['is_reference'],
        'attrs': [
            {'field': 'about', 'value': page_data.get("about", "")},
            {'field': 'best_page', 'value': page_data.get("best_page", "")},
            {'field': 'can_post', 'value': str(page_data.get("can_post", ""))},
            {'field': 'category', 'value': page_data.get("category", "")},
            {'field': 'category_list',
             'value': str(page_data.get("category_list", ""))},
            {'field': 'description',
             'value': page_data.get("description", "")},
            {'field': 'description_html',
             'value': page_data.get("description_html", "")},
            {'field': 'fan_count',
             'value': page_data.get("fan_count", "")},
            {'field': 'general_info',
             'value': page_data.get("general_info", "")},
            {'field': 'personal_info',
             'value': page_data.get("personal_info", "")},
            {'field': 'personal_interests',
             'value': page_data.get("personal_interests", "")},
            {'field': 'username', 'value': page_data.get("username", "")},
            {'field': 'website', 'value': page_data.get("website", "")},
        ],
    }
    ret = requests.put(
        BABEL_API_URL + 'profiles/%s' % (profile['id'],),
        json=data,
        headers={
            'Authorization': 'Token %s' % AUTH_TOKEN
        })
    if ret.status_code == 200:
        sys.stdout.write('.')
        sys.stdout.flush()
    else:
        print("\n", data)
        print(ret.status_code, ret.content, "\n")


next_url = BABEL_API_URL + "profiles?channel__id=%s" % CHANNEL_ID

while next_url is not None:
    profiles = requests.get(next_url).json()
    for profile in profiles['results']:
        page_id = profile['id_in_channel']

        page_data = scrapeFacebookPage(page_id, access_token)

        if page_data:
            process_page(profile, page_data)

    # Next page
    next_url = profiles.get('next', None)
