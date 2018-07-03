from decouple import config
import requests
import sys


BABEL_API_URL = config('BABEL_API_URL', default='http://localhost:8000/api/v1/')
EDEMOCRACIA_URL = config('EDEMOCRACIA_URL', default='https://edemocracia.camara.leg.br')
AUTH_TOKEN = config('AUTH_TOKEN', default='')
CHANNEL_ID = config('CHANNEL_ID', default='')
POSTS_TYPE_ID = config('POSTS_TYPE_ID', default='')


def get_categories():
    data = requests.get(EDEMOCRACIA_URL + '/expressao/categories.json').json()
    return data['category_list']['categories']


def get_topics():
    categories = get_categories()
    topics = []
    for category in categories:
        url = EDEMOCRACIA_URL + '/expressao/c/%s.json' % category['slug']
        data = requests.get(url).json()
        print("Getting topics from category: %s" % category['name'])

        topics += data['topic_list']['topics']
        try:
            while(data['topic_list']['more_topics_url']):
                params = data['topic_list']['more_topics_url'].split('?')[-1]
                data = requests.get(url + '?' + params).json()
                topics += data['topic_list']['topics']
                print(data['topic_list']['more_topics_url'])
        except KeyError:
            print('Get all topics.')
    return topics


def get_all_posts():
    topics = get_topics()

    for topic in topics:
        url = EDEMOCRACIA_URL + '/expressao/t/%s/posts.json' % topic['id']
        data = requests.get(url).json()
        posts = data['post_stream']['posts']

        for post in posts:
            profile_data = {
                'channel_id': CHANNEL_ID,
                'url': EDEMOCRACIA_URL + '/expressao/users/%s.json' % post['username'],
                'id_in_channel': 'expressao-' + str(post['user_id']),
                'is_reference': 'false',
                'attrs': [
                    {'field': 'name',
                     'value': post['name']},
                    {'field': 'avatar_template',
                     'value': post['avatar_template']},
                    {'field': 'username',
                     'value': post['username']},
                    {'field': 'display_username',
                     'value': post['display_username']},
                    {'field': 'user_title',
                     'value': post['user_title']},
                ]
            }

            profile = requests.post(BABEL_API_URL + 'profiles',
                                    json=profile_data,
                                    headers={
                                        'Authorization': 'Token %s' % AUTH_TOKEN
                                    })

            if profile.status_code == 201:
                print("Profile '%s' saved" % post['username'])

                post_data = {
                    'manifestation_type_id': POSTS_TYPE_ID,
                    'profile_id': profile.json()['id'],
                    'url': EDEMOCRACIA_URL + '/expressao/posts/%s.json' % post['id'],
                    'id_in_channel': 'expressao-' + str(post['id']),
                    'content': post['cooked'],
                    'timestamp': post['created_at'],
                    'attrs': [
                        {'field': 'post_number',
                         'value': str(post['post_number'])},
                        {'field': 'updated_at', 'value': post['updated_at']},
                        {'field': 'reply_count',
                         'value': str(post['reply_count'])},
                        {'field': 'reads', 'value': str(post['reads'])},
                        {'field': 'topic', 'value': topic['title']},
                        {'field': 'topic_slug', 'value': topic['slug']},
                    ]
                }

                post_response = requests.post(BABEL_API_URL + 'manifestations',
                                              json=post_data,
                                              headers={
                                                  'Authorization': 'Token %s' % (
                                                      AUTH_TOKEN)
                                              })

                if post_response.status_code == 201:
                    print("Post from '%s' saved" % post['name'])
                else:
                    print("Error: %s" % post_response.content)

            else:
                print("Error: %s" % profile.content)


def get_latest_posts():
    url = EDEMOCRACIA_URL + '/expressao/posts.json'
    data = requests.get(url).json()
    posts = data['latest_posts']

    for post in posts:
        profile_data = {
            'channel_id': CHANNEL_ID,
            'url': EDEMOCRACIA_URL + '/expressao/users/%s.json' % post['username'],
            'id_in_channel': 'expressao-' + str(post['user_id']),
            'is_reference': 'false',
            'attrs': [
                {'field': 'name',
                 'value': post['name']},
                {'field': 'avatar_template',
                 'value': post['avatar_template']},
                {'field': 'username',
                 'value': post['username']},
                {'field': 'display_username',
                 'value': post['display_username']},
                {'field': 'user_title',
                 'value': post['user_title']},
            ]
        }

        profile = requests.post(BABEL_API_URL + 'profiles',
                                json=profile_data,
                                headers={
                                    'Authorization': 'Token %s' % AUTH_TOKEN
                                })

        if profile.status_code == 201:
            print("Profile '%s' saved" % post['username'])

            post_data = {
                'manifestation_type_id': POSTS_TYPE_ID,
                'profile_id': profile.json()['id'],
                'url': EDEMOCRACIA_URL + '/expressao/posts/%s.json' % post['id'],
                'id_in_channel': 'expressao-' + str(post['id']),
                'content': post['raw'],
                'timestamp': post['created_at'],
                'attrs': [
                    {'field': 'post_number',
                     'value': str(post['post_number'])},
                    {'field': 'updated_at', 'value': post['updated_at']},
                    {'field': 'reply_count',
                     'value': str(post['reply_count'])},
                    {'field': 'reads', 'value': str(post['reads'])},
                    {'field': 'topic', 'value': post['topic_title']},
                    {'field': 'topic_slug', 'value': post['topic_slug']},
                    {'field': 'cooked', 'value': post['cooked']},
                ]
            }

            post_response = requests.post(BABEL_API_URL + 'manifestations',
                                          json=post_data,
                                          headers={
                                              'Authorization': 'Token %s' % (
                                                  AUTH_TOKEN)
                                          })

            if post_response.status_code == 201:
                print("Post from '%s' saved" % post['name'])
            else:
                print("Error: %s" % post_response.content)

        else:
            print("Error: %s" % profile.content)


if __name__ == '__main__':
    if 'all' in sys.argv:
        get_all_posts()
    else:
        get_latest_posts()
