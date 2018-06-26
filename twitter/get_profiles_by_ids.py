from decouple import config
import tweepy
import requests
import sys


BABEL_API_URL = config('BABEL_API_URL', default='http://localhost:8000/api/v1/')
CHANNEL_ID = config('CHANNEL_ID', default='')
AUTH_TOKEN = config('AUTH_TOKEN', default='')
CONSUMER_KEY = config('CONSUMER_KEY', default='')
CONSUMER_SECRET = config('CONSUMER_SECRET', default='')
ACCESS_TOKEN = config('ACCESS_TOKEN', default='')
ACCESS_TOKEN_SECRET = config('ACCESS_TOKEN_SECRET', default='')


def get_profiles(file):
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    for line in open(file).read().splitlines():
        try:
            profile = api.get_user(id=line)
            author_params = {
                "name": str.upper(profile.name),
                "author_type": "Deputado"}
            author = requests.get(BABEL_API_URL + 'authors',
                                  params=author_params).json()['results']

            profile_data = {
                'channel_id': CHANNEL_ID,
                'url': profile.url,
                'id_in_channel': profile.id_str,
                'is_reference': 'true',
                'attrs': [
                    {'field': 'name', 'value': profile.name},
                    {'field': 'screen_name', 'value': profile.screen_name},
                    {'field': 'location', 'value': profile.location},
                    {'field': 'description', 'value': profile.description},
                    {'field': 'entities', 'value': str(profile.entities)},
                    {'field': 'profile_image_url',
                     'value': profile.profile_image_url},
                ]
            }
            if author:
                profile_data['author_id'] = author[0]['id']
            else:
                print("Sem autor cadastrado.")

            r = requests.post(BABEL_API_URL + 'profiles',
                              json=profile_data,
                              headers={
                                  'Authorization': 'Token %s' % AUTH_TOKEN
                              })

            print("Profile: %s <status: %s>" % (profile.name, r.status_code))

        except tweepy.TweepError as e:
            print("Profile ID: %s <%s>" % (line, e))


if __name__ == '__main__':
    # Deve ser passado um arquivo .txt com os ids dos deputados no twitter como
    # parâmetro. Ex.: python get_profiles_by_ids.py ids.txt
    get_profiles(sys.argv[-1])
