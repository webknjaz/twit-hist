#!/usr/bin/env python3
import sys
from datetime import datetime
import time
#import requests
from twython import Twython
from twython.exceptions import TwythonRateLimitError

from pymongo import Connection

# import data


class Crawler(object):
    def __init__(self, noTwi=False):
        self.conn = Connection()
        self.db = self.conn.twit
        self.app_key = 'gnkaxR5nCIkkj64P0Vdlg'
        self.app_secret = 'GoxnQjhFEmLgEBwEK0jdQuyY8txAkeX1ma4eIwqBbc'
        if not noTwi:
            self.twi_auth()

    def twi_auth(self):
        """docstring for twi_auth"""
        twitter = Twython(self.app_key, self.app_secret, oauth_version=2)
        self.access_token = twitter.obtain_access_token()
        self.twitter = Twython(self.app_key, access_token=self.access_token)

    def to_datetime(self, string):
        #time_format = '%a, %d %b %Y %H:%M:%S +0000'
        time_format = '%a %b %d %H:%M:%S +0000 %Y'
        # ValueError: time data 'Wed Sep 04 20:53:47 +0000 2013' does not match
        # format '%a, %d %b %Y %H:%M:%S +0000'

        t = time.strptime(string, time_format)
        return datetime(
            year=t.tm_year,
            month=t.tm_mon,
            day=t.tm_mday,
            hour=t.tm_hour,
            minute=t.tm_min,
            second=t.tm_sec)

    def fetch_tweets(self, htags):
        assert self.twitter is not None, 'Twitter API is disabled!'

        def get_tweets_from_api(htag):
            print(htag)
            r = [_ for _ in self.twitter.search_gen(htag)]
            print(r)
            print()
            #print(res)
            print('{tag} fetched...'.format(tag=htag))
            return r

        res = {}
        print('scaning htags...')
        rate_limit = {}
        for htag in htags:
            rate_limit = self.twitter\
                .get_application_rate_limit_status(resources='search')[
                    'resources']['search']['/search/tweets']
            print(rate_limit)
            if rate_limit['remaining'] < 1 and rate_limit['reset'] > time.time():
                time.sleep(rate_limit['reset'] - time.time())

            try:
                res[htag] = get_tweets_from_api(htag)
            except TwythonRateLimitError as e:
                rate_limit = self.twitter\
                    .get_application_rate_limit_status(resources='search')[
                        'resources']['search']['/search/tweets']
                print('Rate limit: {0}'.format(rate_limit))
                print(e)
                if rate_limit['reset'] > time.time():
                    time.sleep(rate_limit['reset'] - time.time())
                res[htag] = get_tweets_from_api(htag)
            except e:
                print(e)
                pass
        return res

    def check_tweet(self, tweet):
        db_tweet = self.db.tweet.find_one({'id': tweet['id']})
        if db_tweet:
            return True
        else:
            return False

    def save_tweet(self, htag, tweet):
        tweet_data = {
            'htags': [htag] + [
                '#{0}'.format(ht['text'])
                for ht in tweet['entities']['hashtags']
            ],
            'id': tweet['id'],
            'datetime': self.to_datetime(tweet['created_at']),
            'from_user': tweet['user']['screen_name'],
            'profile_image_url': tweet['user']['profile_image_url'],
            'text': tweet['text'],
            'raw': tweet
        }
        db_tweet = self.check_tweet(tweet)
        print(db_tweet)
        if not db_tweet:
            try:
                self.db.tweet.insert(tweet_data)
                print('Tweet was recorded')
                for ht in tweet_data['htags']:
                    self.db.meta.insert({
                        'hashtag': ht
                    })
                print('Hashtags saved')
                print(tweet_data)
                print(
                    '''
                            ID: {id}
                        Author: @{author}
                        Tweet: {tweet}
                    Written: {when}
                    '''
                    .format(
                        id=tweet['id'],
                        author=tweet['from_user'],
                        tweet=tweet['text'],
                        when=self.to_datetime(tweet['created_at'])
                    )
                )
                return True
            except:
                print('An exception raised')
                pass
            finally:
                return True
        else:
            print('Tweet was not recorded')
            return False

    def find_tweets(self, htag, date_from, date_to, lim=None):
        dt_from = {'datetime': {'$gte': date_from}}
        dt_to = {'datetime': {'$lte': date_to}}
        query = {'htags': htag,
                 '$and': [dt_from, dt_to]}
        tweets = self.db.tweet.find(query).sort('datetime', -1)
        if lim is not None:
            tweets = tweets.limit(lim)
        return [{'date': str(t['datetime']),
                 'author': t['from_user'],
                 'image': t['profile_image_url'],
                 'text': t['text']} for t in tweets]

    def crawl_tweets(self, htag):
        tweets = self.fetch_tweets(htag)
        for htag, tweets in list(tweets.items()):
            #print(htag)
            for tweet in tweets:
                if not self.save_tweet(htag, tweet):
                    print('Tweet skipped...')
                    print(tweet)
                    pass
                    #break
                else:
                    #print('Tweet added:',tweet)
                    #print('Tweet added...')
                    pass
                #print(tweet)

    def graph_data(self, htag, date_from, date_to):
        tweets = self.find_tweets(htag, date_from, date_to)
        res = {}
        for t in tweets:
            dt = datetime.strptime(t['date'], "%Y-%m-%d %H:%M:%S")
            date = (datetime.now() - dt).days
            res[date] = res.get(date, 0) + 1
        #print(res)
        return sorted([[-k, v] for k, v in list(res.items())])

    def htags(self):
        return [_['hashtag'] for _ in self.db.meta.find()]
        return (x['htags'] for x in self.db.tweet.find({}, {'htags': 1}))
        return [_ for _ in self.db.tweet.distinct('htags')]

    def ensure_indexes(self):
        self.db.tweet.ensure_index('htags')
        self.db.tweet.ensure_index('id')
        self.db.tweet.ensure_index('datetime')


def main(tags=[]):
    crawler = Crawler()
    if not tags:
        tags = crawler.htags()
    crawler.crawl_tweets(tags)

if __name__ == '__main__':
    main(sys.argv[1:])
