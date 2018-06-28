from decouple import config
import requests


BABEL_API_URL = config('BABEL_API_URL', default='http://localhost:8000/api/v1/')
EDEMOCRACIA_URL = config('EDEMOCRACIA_URL', default='https://edemocracia.camara.leg.br')
CHANNEL_ID = config('CHANNEL_ID', default='')
MANIFESTATION_TYPE_ID = config('MANIFESTATION_TYPE_ID', default='')
AUTH_TOKEN = config('AUTH_TOKEN', default='')


def get_wikilegis_comments():
    data = requests.get(EDEMOCRACIA_URL + '/wikilegis/api/v1/comment/').json()
    comments = data['objects']
    next_url = data['meta']['next']

    while(next_url):
        data = requests.get(EDEMOCRACIA_URL + next_url).json()
        comments += data['objects']
        print(next_url)

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
                'manifestation_type_id': MANIFESTATION_TYPE_ID,
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

            print("Manifestation '%s' Status: %s" % (
                comment['id'], r_comment.status_code))


if __name__ == '__main__':
    get_wikilegis_comments()
