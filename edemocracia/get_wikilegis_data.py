from decouple import config
import requests
import sys


BABEL_API_URL = config('BABEL_API_URL', default='http://localhost:8000/api/v1/')
EDEMOCRACIA_URL = config('EDEMOCRACIA_URL', default='https://edemocracia.camara.leg.br')
AUTH_TOKEN = config('AUTH_TOKEN', default='')
CHANNEL_ID = config('CHANNEL_ID', default='')
COMMENT_TYPE_ID = config('COMMENT_TYPE_ID', default='')
VOTE_TYPE_ID = config('VOTE_TYPE_ID', default='')


def api_get_objects(url):
    data = requests.get(url).json()
    objects = data['objects']
    next_url = data['meta']['next']

    while(next_url):
        data = requests.get(EDEMOCRACIA_URL + next_url).json()
        objects += data['objects']
        print(next_url)

    return objects


def get_comments():
    url = EDEMOCRACIA_URL + '/wikilegis/api/v1/comment/'
    comments = api_get_objects(url)

    for comment in comments:
        profile_data = {
            'channel_id': CHANNEL_ID,
            'url': EDEMOCRACIA_URL + comment['author']['resource_uri'],
            'id_in_channel': comment['author']['id'],
            'is_reference': 'false',
            'attrs': [
                {'field': 'first_name',
                 'value': comment['author']['first_name']},
                {'field': 'last_name',
                 'value': comment['author']['last_name']},
                {'field': 'username',
                 'value': comment['author']['username']},
            ]
        }

        r_profile = requests.post(BABEL_API_URL + 'profiles',
                                  json=profile_data,
                                  headers={
                                      'Authorization': 'Token %s' % AUTH_TOKEN
                                  })

        print("Profile status %s" % r_profile.status_code)

        if r_profile.status_code == 201:
            comment_data = {
                'manifestation_type_id': COMMENT_TYPE_ID,
                'profile_id': r_profile.json()['id'],
                'url': EDEMOCRACIA_URL + comment['resource_uri'],
                'id_in_channel': comment['id'],
                'content': comment['text'],
                'timestamp': comment['created'],
                'attrs': [
                    {'field': 'content_type', 'value': comment['content_type']},
                    {'field': 'object_id', 'value': comment['object_id']},
                    {'field': 'modified', 'value': comment['modified']},
                ]
            }

            r_comment = requests.post(BABEL_API_URL + 'manifestations',
                                      json=comment_data,
                                      headers={
                                          'Authorization': 'Token %s' % (
                                              AUTH_TOKEN)
                                      })

            if r_comment.status_code == 201:
                print("Comment '%s' created" % comment['id'])
            else:
                print("Error: %s" % r_comment.content)


def get_votes():
    url = EDEMOCRACIA_URL + '/wikilegis/api/v1/vote/'
    votes = api_get_objects(url)

    for vote in votes:
        profile_data = {
            'channel_id': CHANNEL_ID,
            'url': EDEMOCRACIA_URL + vote['user']['resource_uri'],
            'id_in_channel': vote['user']['id'],
            'is_reference': 'false',
            'attrs': [
                {'field': 'first_name',
                 'value': vote['user']['first_name']},
                {'field': 'last_name',
                 'value': vote['user']['last_name']},
                {'field': 'username',
                 'value': vote['user']['username']},
            ]
        }

        r_profile = requests.post(BABEL_API_URL + 'profiles',
                                  json=profile_data,
                                  headers={
                                      'Authorization': 'Token %s' % AUTH_TOKEN
                                  })

        print("Profile status %s" % r_profile.status_code)

        if r_profile.status_code == 201:
            vote_data = {
                'manifestation_type_id': VOTE_TYPE_ID,
                'profile_id': r_profile.json()['id'],
                'url': EDEMOCRACIA_URL + vote['resource_uri'],
                'id_in_channel': vote['id'],
                'content': str(vote['vote']),
                'timestamp': vote['created'],
                'attrs': [
                    {'field': 'content_type', 'value': vote['content_type']},
                    {'field': 'object_id', 'value': vote['object_id']},
                    {'field': 'modified', 'value': vote['modified']},
                ]
            }

            r_vote = requests.post(BABEL_API_URL + 'manifestations',
                                   json=vote_data,
                                   headers={
                                       'Authorization': 'Token %s' % (
                                           AUTH_TOKEN)
                                   })

            if r_vote.status_code == 201:
                print("Vote '%s' created" % vote['id'])
            else:
                print("Error: %s" % r_vote.content)


if __name__ == '__main__':
    if 'comments' in sys.argv:
        get_comments()
    elif 'votes' in sys.argv:
        get_votes()
