Title: Geo-locating Tweets in real-time with Twython
slug: geolocating_tweets_with_twython
Date: 2013-06-24
status: draft

```python
from twython import Twython
from credentials import CONSUMER_KEY, CONSUMER_SECRET
twitter = Twython(CONSUMER_KEY, CONSUMER_SECRET)
```

```python
auth = twitter.get_authentication_tokens()
OAUTH_TOKEN = auth['oauth_token']
OAUTH_TOKEN_SECRET = auth['oauth_token_secret']
print('Go to {0} and authenticate your application'.format(auth['auth_url']))
```

```python
PIN = '1234567'
twitter = Twython(CONSUMER_KEY, CONSUMER_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
final_step = twitter.get_authorized_tokens(PIN)
twitter = Twython(CONSUMER_KEY, CONSUMER_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
```

```pycon
>>> print(twitter.get_user_timeline(screen_name='stephenfry')[0])
{u'contributors': None,
 u'coordinates': None,
 u'created_at': u'Mon Jun 24 09:54:54 +0000 2013',
 u'entities': {u'hashtags': [],
  u'media': [{u'display_url': u'pic.twitter.com/zmciUu7AwM',
    u'expanded_url': u'http://twitter.com/stephenfry/status/349103329164550144/photo/1',
    u'id': 349103329168744448,
    u'id_str': u'349103329168744448',
    u'indices': [59, 81],
    u'media_url': u'http://pbs.twimg.com/media/BNhDoNUCYAAQMnk.jpg',
    u'media_url_https': u'https://pbs.twimg.com/media/BNhDoNUCYAAQMnk.jpg',
    u'sizes': {u'large': {u'h': 496, u'resize': u'fit', u'w': 648},
     u'medium': {u'h': 459, u'resize': u'fit', u'w': 600},
     u'small': {u'h': 260, u'resize': u'fit', u'w': 340},
     u'thumb': {u'h': 150, u'resize': u'crop', u'w': 150}},
    u'type': u'photo',
    u'url': u'http://t.co/zmciUu7AwM'}],
  u'symbols': [],
  u'urls': [],
  u'user_mentions': [{u'id': 61759552,
    u'id_str': u'61759552',
    u'indices': [46, 57],
    u'name': u'Kathy Lette',
    u'screen_name': u'KathyLette'}]},
 u'favorite_count': 1544,
 u'favorited': False,
 u'geo': None,
 u'id': 349103329164550144,
 u'id_str': u'349103329164550144',
 u'in_reply_to_screen_name': None,
 u'in_reply_to_status_id': None,
 u'in_reply_to_status_id_str': None,
 u'in_reply_to_user_id': None,
 u'in_reply_to_user_id_str': None,
 u'lang': u'en',
 u'place': None,
 u'possibly_sensitive': False,
 u'retweet_count': 4600,
 u'retweeted': False,
 u'source': u'<a href="http://www.apple.com" rel="nofollow">iOS</a>',
 u'text': u'The Pope finally ends the ban on condoms (via @kathylette) http://t.co/zmciUu7AwM',
 u'truncated': False,
 u'user': {u'contributors_enabled': False,
  u'created_at': u'Tue Jul 15 11:45:30 +0000 2008',
  u'default_profile': False,
  u'default_profile_image': False,
  u'description': u'British Actor, Writer, Lord of Dance, Prince of Swimwear & Blogger. NEVER reads Direct Messages: Instagram - stephenfryactually',
  u'entities': {u'description': {u'urls': []},
   u'url': {u'urls': [{u'display_url': u'stephenfry.com',
      u'expanded_url': u'http://www.stephenfry.com/',
      u'indices': [0, 22],
      u'url': u'http://t.co/4Kht71pdlB'}]}},
  u'favourites_count': 78,
  u'follow_request_sent': False,
  u'followers_count': 5899575,
  u'following': None,
  u'friends_count': 51550,
  u'geo_enabled': True,
  u'id': 15439395,
  u'id_str': u'15439395',
  u'is_translator': False,
  u'lang': u'en',
  u'listed_count': 55611,
  u'location': u'London',
  u'name': u'Stephen Fry',
  u'notifications': None,
  u'profile_background_color': u'A5E6FA',
  u'profile_background_image_url': u'http://a0.twimg.com/profile_background_images/797461062/0ec127e26ce9be73cdafb2afca999cd6.jpeg',
  u'profile_background_image_url_https': u'https://si0.twimg.com/profile_background_images/797461062/0ec127e26ce9be73cdafb2afca999cd6.jpeg',
  u'profile_background_tile': False,
  u'profile_banner_url': u'https://pbs.twimg.com/profile_banners/15439395/1360662717',
  u'profile_image_url': u'http://a0.twimg.com/profile_images/344513261579148157/ba4807791ef9cce28dc0d4aa2ce9372c_normal.jpeg',
  u'profile_image_url_https': u'https://si0.twimg.com/profile_images/344513261579148157/ba4807791ef9cce28dc0d4aa2ce9372c_normal.jpeg',
  u'profile_link_color': u'1C83A6',
  u'profile_sidebar_border_color': u'FFFFFF',
  u'profile_sidebar_fill_color': u'48CCF4',
  u'profile_text_color': u'333333',
  u'profile_use_background_image': False,
  u'protected': False,
  u'screen_name': u'stephenfry',
  u'statuses_count': 16297,
  u'time_zone': u'London',
  u'url': u'http://t.co/4Kht71pdlB',
  u'utc_offset': 0,
  u'verified': True}}
```

```python
from twython import TwythonStreamer

class MyStreamer(TwythonStreamer):
    def on_success(self, data):
        """If we're managing a tweet list, and this tweet has geo-information, add it to the list."""
        try:
            self.tweet_list.append({ 
                'coordinates': data['geo']['coordinates'], 'source': data['source']
            })
        except (KeyError, AttributeError, TypeError):
            pass

    def on_error(self, status_code, data):
        """On error, print the error code and disconnect ourselves."""
        print('Error: {0}'.format(status_code))
        self.disconnect()
```

![](|filename|/images/geolocating-twython/twitter-api-key.png)
