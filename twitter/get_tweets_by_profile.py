from decouple import config
import time
import tweepy
import requests


BABEL_API_URL = config('BABEL_API_URL', default='http://localhost:8000/api/v1/')
CHANNEL_ID = config('CHANNEL_ID', default='')
MANIFESTATION_TYPE_ID = config('MANIFESTATION_TYPE_ID', default='')
AUTH_TOKEN = config('AUTH_TOKEN', default='')
CONSUMER_KEY = config('CONSUMER_KEY', default='')
CONSUMER_SECRET = config('CONSUMER_SECRET', default='')
ACCESS_TOKEN = config('ACCESS_TOKEN', default='')
ACCESS_TOKEN_SECRET = config('ACCESS_TOKEN_SECRET', default='')


def babel_profiles():
    data = requests.get(
        BABEL_API_URL + 'profiles', params={'channel__id': CHANNEL_ID}).json()
    profiles = data['results']

    while(data['next']):
        data = requests.get(data['next']).json()
        profiles += data['results']

    return profiles


def get_tweets():
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    profiles = babel_profiles()

    for profile in profiles:
        try:
            tweets = api.user_timeline(
                user_id=profile['id_in_channel'], include_rts=True, count=200,
                tweet_mode="extended")
        except tweepy.RateLimitError:
            time.sleep(60 * 15)
            continue

        for tweet in tweets:
            try:
                url = tweet.entities['urls'][0]['url']
            except (KeyError, IndexError) as e:
                url = None
                print('Url Error - reason "%s"' % e)

            manifestation_data = {
                'manifestation_type_id': MANIFESTATION_TYPE_ID,
                'profile_id': profile['id'],
                'url': url,
                'id_in_channel': tweet.id_str,
                'content': tweet.full_text,
                'timestamp': str(tweet.created_at),
                'attrs': [
                    {'field': 'retweeted', 'value': str(tweet.retweeted)},
                    {'field': 'retweet_count', 'value': tweet.retweet_count},
                    {'field': 'favorite_count', 'value': tweet.favorite_count},
                    {'field': 'favorited', 'value': str(tweet.favorited)},
                    {'field': 'source', 'value': tweet.source},
                    {'field': 'place', 'value': str(tweet.place)},
                    {'field': 'geo', 'value': str(tweet.geo)},
                    {'field': 'coordinates', 'value': str(tweet.coordinates)},
                    {'field': 'contributors', 'value': tweet.contributors},
                    {'field': 'lang', 'value': tweet.lang},
                    {'field': 'in_reply_to_user_id_str',
                     'value': tweet.in_reply_to_user_id_str},
                    {'field': 'in_reply_to_screen_name',
                     'value': tweet.in_reply_to_screen_name},
                    {'field': 'entities', 'value': str(tweet.entities)},
                ]
            }

            r = requests.post(BABEL_API_URL + 'manifestations',
                              json=manifestation_data,
                              headers={
                                  'Authorization': 'Token %s' % AUTH_TOKEN
                              })

            print("Manifestation '%s' Status: %s" % (
                tweet.id_str, r.status_code))


if __name__ == '__main__':
    get_tweets()
