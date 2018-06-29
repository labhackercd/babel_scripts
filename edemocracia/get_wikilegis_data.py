from decouple import config
import requests
import sys


BABEL_API_URL = config('BABEL_API_URL', default='http://localhost:8000/api/v1/')
EDEMOCRACIA_URL = config('EDEMOCRACIA_URL', default='https://edemocracia.camara.leg.br')
AUTH_TOKEN = config('AUTH_TOKEN', default='')
CHANNEL_ID = config('CHANNEL_ID', default='')
COMMENT_TYPE_ID = config('COMMENT_TYPE_ID', default='')
VOTE_TYPE_ID = config('VOTE_TYPE_ID', default='')
AMENDMENT_TYPE_ID = config('AMENDMENT_TYPE_ID', default='')


def api_get_objects(url):
    data = requests.get(url).json()
    objects = data['objects']
    next_url = data['meta']['next']

    while(next_url):
        data = requests.get(EDEMOCRACIA_URL + next_url).json()
        objects += data['objects']
        print(next_url)

    return objects


def send_profile(author):
    profile_data = {
        'channel_id': CHANNEL_ID,
        'url': EDEMOCRACIA_URL + author['resource_uri'],
        'id_in_channel': 'wikilegis-' + str(author['id']),
        'is_reference': 'false',
        'attrs': [
            {'field': 'first_name',
             'value': author['first_name']},
            {'field': 'last_name',
             'value': author['last_name']},
            {'field': 'username',
             'value': author['username']},
        ]
    }

    response = requests.post(BABEL_API_URL + 'profiles',
                             json=profile_data,
                             headers={
                                 'Authorization': 'Token %s' % AUTH_TOKEN
                             })

    if response.status_code == 201:
        print("Profile '%s' created" % author['id'])
    else:
        print("Error: %s" % response.content)

    return response


def send_manifestation(data):
    response = requests.post(BABEL_API_URL + 'manifestations',
                             json=data,
                             headers={
                                 'Authorization': 'Token %s' % (
                                     AUTH_TOKEN)
                             })
    return response


def get_comments():
    url = EDEMOCRACIA_URL + '/wikilegis/api/v1/comment/'
    comments = api_get_objects(url)

    for comment in comments:
        profile = send_profile(comment['author'])

        if profile.status_code == 201:
            comment_data = {
                'manifestation_type_id': COMMENT_TYPE_ID,
                'profile_id': profile.json()['id'],
                'url': EDEMOCRACIA_URL + comment['resource_uri'],
                'id_in_channel': 'wikilegis-comment-' + str(comment['id']),
                'content': comment['text'],
                'timestamp': comment['created'],
                'attrs': [
                    {'field': 'content_type', 'value': comment['content_type']},
                    {'field': 'object_id', 'value': comment['object_id']},
                    {'field': 'modified', 'value': comment['modified']},
                ]
            }

            r_comment = send_manifestation(comment_data)

            if r_comment.status_code == 201:
                print("Comment '%s' created" % comment['id'])
            else:
                print("Error: %s" % r_comment.content)


def get_votes():
    url = EDEMOCRACIA_URL + '/wikilegis/api/v1/vote/'
    votes = api_get_objects(url)

    for vote in votes:
        profile = send_profile(vote['user'])

        if profile.status_code == 201:
            vote_data = {
                'manifestation_type_id': VOTE_TYPE_ID,
                'profile_id': profile.json()['id'],
                'url': EDEMOCRACIA_URL + vote['resource_uri'],
                'id_in_channel': 'wikilegis-vote-' + str(vote['id']),
                'content': str(vote['vote']),
                'timestamp': vote['created'],
                'attrs': [
                    {'field': 'content_type', 'value': vote['content_type']},
                    {'field': 'object_id', 'value': vote['object_id']},
                    {'field': 'modified', 'value': vote['modified']},
                ]
            }

            r_vote = send_manifestation(vote_data)

            if r_vote.status_code == 201:
                print("Vote '%s' created" % vote['id'])
            else:
                print("Error: %s" % r_vote.content)


def get_amendments():
    amendment_types = [
        'supressamendment', 'modifieramendment', 'additiveamendment']
    url = EDEMOCRACIA_URL + '/wikilegis/api/v1/'

    for object_type in amendment_types:
        amendments = api_get_objects(url + object_type)

        for amendment in amendments:
            profile = send_profile(amendment['author'])
            if profile.status_code == 201:
                if object_type == 'supressamendment':
                    reference = amendment['supressed']['content']
                    reference_url = (EDEMOCRACIA_URL +
                                     amendment['supressed']['resource_uri'])
                elif object_type == 'modifieramendment':
                    reference = amendment['replaced']['content']
                    reference_url = (EDEMOCRACIA_URL +
                                     amendment['replaced']['resource_uri'])
                elif object_type == 'additiveamendment':
                    reference = amendment['reference']['content']
                    reference_url = (EDEMOCRACIA_URL +
                                     amendment['reference']['resource_uri'])
                else:
                    reference = None
                    reference_url = None

                amendment_data = {
                    'manifestation_type_id': AMENDMENT_TYPE_ID,
                    'profile_id': profile.json()['id'],
                    'url': EDEMOCRACIA_URL + amendment['resource_uri'],
                    'id_in_channel': 'wikilegis-' + object_type + '-' + str(amendment['id']),
                    'content': amendment['content'],
                    'timestamp': amendment['created'],
                    'attrs': [
                        {'field': 'downvote_count',
                         'value': amendment['downvote_count']},
                        {'field': 'upvote_count',
                         'value': amendment['upvote_count']},
                        {'field': 'votes_count',
                         'value': amendment['votes_count']},
                        {'field': 'votes', 'value': str(amendment['votes'])},
                        {'field': 'comments_count',
                         'value': amendment['comments_count']},
                        {'field': 'comments',
                         'value': str(amendment['comments'])},
                        {'field': 'participation_count',
                         'value': amendment['participation_count']},
                        {'field': 'number', 'value': amendment['number']},
                        {'field': 'order', 'value': amendment['order']},
                        {'field': 'segment_type',
                         'value': str(amendment['segment_type'])},
                        {'field': 'segment_reference', 'value': reference},
                        {'field': 'segment_reference_url',
                         'value': reference_url},
                    ]
                }

                r_amendment = send_manifestation(amendment_data)

                if r_amendment.status_code == 201:
                    print("%s '%s' created" % (object_type, amendment['id']))
                else:
                    print("Error: %s" % r_amendment.content)


if __name__ == '__main__':
    if 'comments' in sys.argv:
        get_comments()
    elif 'votes' in sys.argv:
        get_votes()
    elif 'amendments' in sys.argv:
        get_amendments()
    else:
        get_comments()
        get_votes()
        get_amendments()
