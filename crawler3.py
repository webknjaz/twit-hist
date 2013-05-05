#!/usr/bin/env python3
import json
import sys
import urllib.request, urllib.parse, urllib.error
import http.client
from datetime import datetime
import time
#import requests

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
        print('scaning htags...')
        for htag in htags:
            try:
                print(htag)
                url = base_url + urllib.parse.quote(htag)
                # url = base_url + htag
                #print(('fetching ', url))
                #print(requests.get(url).content)
                #print(urllib.request.urlopen(url).read().decode('utf8'))
                #d = json.loads(requests.get(url).content)
                try:
                    d = json.loads(urllib.request.urlopen(url).read().decode('utf8'))
                except urllib.error.HTTPError as e:
                    time.sleep(1)
                    d = json.loads(urllib.request.urlopen(url).read().decode('utf8'))
                except (http.client.BadStatusLine, urllib.error.URLError) as e:
                    time.sleep(5)
                    d = json.loads(urllib.request.urlopen(url).read().decode('utf8'))
                except:
                    continue
                #print(d)
                print('.', end='')
                raw_tweets = d['results']
                #print(raw_tweets)
                #if len(raw_tweets) > 0 and not (self.check_tweet(raw_tweets[0]) or self.check_tweet(raw_tweets[-1])):
                next_page = d.get('next_page', None)
                while next_page:
                    print('.', end='')
                    url = urllib.parse.urljoin(base_url, next_page)
                    #'?'.join([url,qs])
                    #print(('fetching ', url))
                    #d = json.loads(requests.get(url).content)
                    try:
                        d = json.loads(urllib.request.urlopen(url).read().decode('utf8'))
                    #except urllib.error.HTTPError as e:
                    #    time.sleep(1)
                    #    d = json.loads(urllib.request.urlopen(url).read().decode('utf8'))
                    #except (http.client.BadStatusLine, urllib.error.URLError) as e:
                    #    time.sleep(5)
                    #    d = json.loads(urllib.request.urlopen(url).read().decode('utf8'))
                    except:
                        continue
                    raw_tweets += d['results']
                    #print(raw_tweets)
                    # It's not ideal way of optimization, this cuts lots of tweets:
                    #if len(d['results']) > 0 and (self.check_tweet(d['results'][0]) or self.check_tweet(d['results'][-1])):
                    #    break
                    next_page = d.get('next_page', None)
                    # next_page = None
                    # for tweet in raw_tweets:
                    #     self.save_tweet(htag, tweet)
                res[htag] = raw_tweets
                print()
                #print(res)
                print('{tag} fetched...'.format(tag=htag))
            except:
                pass
        return res

    def check_tweet(self, tweet):
        db_tweet = self.db.tweet.find_one({'id': tweet['id']})
        if db_tweet:
            return True
        else:
            return False

    def save_tweet(self, htag, tweet):
        tweet_data = {'htags': [htag],
                      'id': tweet['id'],
                      'datetime': self.to_datetime(tweet['created_at']),
                      'from_user': tweet['from_user'],
                      'profile_image_url': tweet['profile_image_url'],
                      'text': tweet['text'],
                      'raw': tweet}
        db_tweet = self.check_tweet(tweet)
        #print(db_tweet)
        if not db_tweet:
            try:
                self.db.tweet.insert(tweet_data)
                print('''
                             ID: {id}
                         Author: @{author}
                          Tweet: {tweet}
                        Written: {when}
                        '''
                        .format(id = tweet['id'], author = tweet['from_user'], tweet = tweet['text'], when = self.to_datetime(tweet['created_at']))
                        )
                return True
            except:
                pass
            finally:
                return True
        else:
            return False

    def find_tweets(self, htag, date_from, date_to, lim = None):
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
        # tweets = self.fetch_tweets(urllib.unquote(htag))
        for htag, tweets in list(tweets.items()):
            print(htag)
            for tweet in tweets:
                if not self.save_tweet(htag, tweet):
                    print('Tweet skipped...')
                    pass
                    #break
                else:
                    #print('Tweet added:',tweet)
                    print('Tweet added...')
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
        return [_ for _ in self.db.tweet.distinct('htags')]

    def ensure_indexes(self):
        self.db.tweet.ensure_index('htags')
        self.db.tweet.ensure_index('id')
        self.db.tweet.ensure_index('datetime')


def main(tags=[]):
    crawler = Crawler()
    if not tags:
        tags = crawler.htags()
    tweets = crawler.fetch_tweets(tags)
    crawler.crawl_tweets(tags)

if __name__ == '__main__':
    main(sys.argv[1:])
