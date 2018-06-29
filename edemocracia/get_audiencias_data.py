from decouple import config
import requests
# import sys


BABEL_API_URL = config('BABEL_API_URL', default='http://localhost:8000/api/v1/')
EDEMOCRACIA_URL = config('EDEMOCRACIA_URL', default='https://edemocracia.camara.leg.br')
AUTH_TOKEN = config('AUTH_TOKEN', default='')
CHANNEL_ID = config('CHANNEL_ID', default='')
QUESTION_TYPE_ID = config('QUESTION_TYPE_ID', default='')


def api_get_objects(url):
    data = requests.get(url).json()
    objects = data['results']
    next_url = data['next']

    while(next_url):
        data = requests.get(next_url).json()
        objects += data['results']
        print(next_url)

    return objects


def send_profile(author):
    profile_data = {
        'channel_id': CHANNEL_ID,
        'url': EDEMOCRACIA_URL + '/audiencias/api/user/' + author['username'],
        'id_in_channel': 'audiencias-' + str(author['id']),
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


def get_questions():
    url = EDEMOCRACIA_URL + '/audiencias/api/question/'
    questions = api_get_objects(url)

    for question in questions:
        profile = send_profile(question['user'])

        if profile.status_code == 201:
            question_data = {
                'manifestation_type_id': QUESTION_TYPE_ID,
                'profile_id': profile.json()['id'],
                'url': url + str(question['id']),
                'id_in_channel': 'audiencias-question-' + str(question['id']),
                'content': question['question'],
                'timestamp': question['created'],
                'attrs': [
                    {'field': 'modified', 'value': question['modified']},
                    {'field': 'votes', 'value': str(question['votes'])},
                    {'field': 'room', 'value': question['room']},
                ]
            }

            r_question = send_manifestation(question_data)

            if r_question.status_code == 201:
                print("Question '%s' created" % question['id'])
            else:
                print("Error: %s" % r_question.content)


if __name__ == '__main__':
    # if 'questions' in sys.argv:
    #     get_questions()
    # else:
    get_questions()
