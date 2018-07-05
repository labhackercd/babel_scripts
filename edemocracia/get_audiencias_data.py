from decouple import config
from datetime import datetime, timedelta
import requests
import sys


BABEL_API_URL = config('BABEL_API_URL', default='http://localhost:8000/api/v1/')
EDEMOCRACIA_URL = config('EDEMOCRACIA_URL', default='https://edemocracia.camara.leg.br')
AUTH_TOKEN = config('AUTH_TOKEN', default='')
CHANNEL_ID = config('CHANNEL_ID', default='')
QUESTION_TYPE_ID = config('QUESTION_TYPE_ID', default='')
MESSAGE_TYPE_ID = config('MESSAGE_TYPE_ID', default='')


def api_get_objects(url):
    data = requests.get(url).json()
    objects = data['results']

    while(data['next']):
        data = requests.get(data['next']).json()
        objects += data['results']
        print(data['next'])

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
    if sys.argv[-1].isdigit():
        today = datetime.today()
        since = today - timedelta(days=int(sys.argv[-1]))
        params = '?modified__gte=%s' % since.strftime('%Y-%m-%d')
        url = EDEMOCRACIA_URL + '/audiencias/api/question/' + params
    else:
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


def get_messages():
    if sys.argv[-1].isdigit():
        today = datetime.today()
        since = today - timedelta(days=int(sys.argv[-1]))
        params = '?modified__gte=%s' % since.strftime('%Y-%m-%d')
        url = EDEMOCRACIA_URL + '/audiencias/api/message/' + params
    else:
        url = EDEMOCRACIA_URL + '/audiencias/api/message/'

    messages = api_get_objects(url)

    for message in messages:
        profile = send_profile(message['user'])

        if profile.status_code == 201:
            message_data = {
                'manifestation_type_id': MESSAGE_TYPE_ID,
                'profile_id': profile.json()['id'],
                'url': url + str(message['id']),
                'id_in_channel': 'audiencias-message-' + str(message['id']),
                'content': message['message'],
                'timestamp': message['created'],
                'attrs': [
                    {'field': 'modified', 'value': message['modified']},
                    {'field': 'room', 'value': str(message['room'])},
                ]
            }

            r_message = send_manifestation(message_data)

            if r_message.status_code == 201:
                print("Message '%s' created" % message['id'])
            else:
                print("Error: %s" % r_message.content)


if __name__ == '__main__':
    if 'questions' in sys.argv:
        get_questions()
    elif 'messages' in sys.argv:
        get_messages()
    else:
        get_questions()
        get_messages()
