#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'Rich Wareham'
SITENAME = u'Scattered Tech'
SITEURL = ''

TIMEZONE = 'Europe/Paris'

DEFAULT_LANG = u'en'

# Make the article URLs a little nicer
ARTICLE_URL = '{date:%Y}/{date:%m}/{date:%d}/{slug}/'
ARTICLE_SAVE_AS = '{date:%Y}/{date:%m}/{date:%d}/{slug}/index.html'

# Add an explicit 'downloads' static URL location
STATIC_PATHS = ['images', 'downloads']

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None

FEED_DOMAIN = 'http://rjw57.github.io/blog/feeds'
FEED_ATOM = 'all.atom.xml'

## Blogroll
#LINKS =  (('Pelican', 'http://getpelican.com/'),
#          ('Python.org', 'http://python.org/'),
#          ('Jinja2', 'http://jinja.pocoo.org/'),
#          ('You can modify those links in your config file', '#'),)
#
## Social widget
#SOCIAL = (('You can add links in your config file', '#'),
#          ('Another social link', '#'),)

THEME = 'themes/octopress'

DEFAULT_PAGINATION = False

# Uncomment following line if you want document-relative URLs when developing
RELATIVE_URLS = True

# Various links to social media
GITHUB_USER = 'rjw57'
GITHUB_SHOW_USER_LINK = True
GITHUB_SKIP_FORK = True
GITHUB_REPO_COUNT = 3

TWITTER_USER = 'richwareham'
TWITTER_TWEET_BUTTON = True

GOOGLE_PLUS_USER = '114005052144439249039'

# Various 'spam your friends' on social media buttons
GOOGLE_PLUS_ONE = True
TWITTER_FOLLOW_BUTTON = True
