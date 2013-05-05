#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import sys
import urllib.request, urllib.parse, urllib.error
from datetime import datetime
import time
import requests

from pymongo import Connection

# import data


class Crawler(object):
    def __init__(self):
        self.conn = Connection()
        self.db = self.conn.twit

    def to_datetime(self, string):
        time_format = '%a, %d %b %Y %H:%M:%S +0000'
        t = time.strptime(string, time_format)
        return datetime(
                year=t.tm_year,
                month=t.tm_mon,
                day=t.tm_mday,
                hour=t.tm_hour,
                minute=t.tm_min,
                second=t.tm_sec)

    def fetch_tweets(self, htags):
        base_url = 'http://search.twitter.com/search.json?q='
        res = {}
        for htag in htags:
            try:
                print(htag)
                url = base_url + urllib.parse.quote(htag)
                # url = base_url + htag
                print(('fetching ', url))
                d = json.loads(requests.get(url).content)
                print(d)
                raw_tweets = d['results']
                next_page = d.get('next_page', None)
                while next_page:
                    url = urllib.basejoin(base_url, next_page)
                    print(('fetching ', url))
                    d = json.loads(requests.get(url).content)
                    try:
                        raw_tweets += d['results']
                    except:
                        pass
                    next_page = d.get('next_page', None)
                    # next_page = None
                    # for tweet in raw_tweets:
                    #     self.save_tweet(htag, tweet)
                res[htag] = raw_tweets
            except:
                break
        return res

    def save_tweet(self, htag, tweet):
        tweet_data = {'htags': [htag],
                      'id': tweet['id'],
                      'datetime': self.to_datetime(tweet['created_at']),
                      'from_user': tweet['from_user'],
                      'profile_image_url': tweet['profile_image_url'],
                      'text': tweet['text'],
                      'raw': tweet}
        db_tweet = self.db.tweet.find_one({'id': tweet_data['id']})
        if not db_tweet:
            self.db.tweet.insert(tweet_data)
            return True
        else:
            return False

    def find_tweets(self, htag, date_from, date_to):
        dt_from = {'datetime': {'$gte': date_from}}
        dt_to = {'datetime': {'$lte': date_to}}
        query = {'htags': htag,
                 '$and': [dt_from, dt_to]}
        tweets = self.db.tweet.find(query).sort('datetime', -1)
        return [{'date': str(t['datetime']),
                 'image': t['profile_image_url'],
                 'text': t['text']} for t in tweets]

    def crawl_tweets(self, htag):
        tweets = self.fetch_tweets(htag)
        # tweets = self.fetch_tweets(urllib.unquote(htag))
        for htag, tweets in list(tweets.items()):
            for tweet in tweets:
                if not self.save_tweet(htag, tweet):
                    break
                else:
                    print('Tweet added:',tweet)

    def graph_data(self, htag, date_from, date_to):
        tweets = self.find_tweets(htag, date_from, date_to)
        res = {}
        for t in tweets:
            dt = datetime.strptime(t['date'], "%Y-%m-%d %H:%M:%S")
            date = (datetime.now() - dt).days
            res[date] = res.get(date, 0) + 1
        print(res)
        return sorted([[-k, v] for k, v in list(res.items())])

    def htags(self):
        return [_ for _ in self.db.tweet.distinct('htags')]

    def ensure_indexes(self):
        self.db.tweet.ensure_index('htags')
        self.db.tweet.ensure_index('id')


def main(tags=[]):
    crawler = Crawler()
    if not tags:
        tags = crawler.htags()
    tweets = crawler.fetch_tweets(tags)
    crawler.crawl_tweets(tags)

if __name__ == '__main__':
    main(sys.argv[1:])
