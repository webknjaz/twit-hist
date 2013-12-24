#!/usr/bin/env python3
from datetime import datetime
import os
import os.path

import tornado.ioloop
import tornado.web
import tornado.wsgi

import json
import crawler3
import logging

FROM = datetime(2000, 1, 1)
TO = datetime(2100, 1, 1)


class MainHandler(tornado.web.RequestHandler):
    #@tornado.web.asynchronous
    def get(self, htag):
        c = crawler3.Crawler()
        c.crawl_tweets([htag])
        tweets = c.find_tweets(htag, FROM, TO, 1000)
        del c
        self.write(json.dumps({
            'htag': htag,
            'count': len(tweets),
            'results': list(tweets)
        }))
        del tweets
        self.finish()


class GraphHandler(tornado.web.RequestHandler):
    def get(self, htag):
        c = crawler3.Crawler(noTwi=True)
        data = c.graph_data(htag, FROM, TO)
        del c
        # data = [
        #     [161.2, 51.6],
        #     [167.5, 59.0],
        #     [159.5, 49.2],
        #     [157.0, 63.0],
        #     [155.8, 53.6]
        # ]
        self.write(json.dumps(data))
        del data


class HomeHandler(tornado.web.RequestHandler):
    def get(self):
        #c = crawler3.Crawler(noTwi=True)
        #htags = c.htags()
        #del c
        #logging.info(htags)
        #self.render('index.html', **{'htags': json.dumps(sorted(htags))})
        #self.render('index.html', **{'htags': json.dumps(htags)})
        #self.render('index.html', **{'htags': json.dumps([h for h in htags])})
        self.render('index.html', **{'htags': '[]'})
        #self.write('uwsgi test')
        #del htags


class wkHandler(tornado.web.RequestHandler):
    def get(self, slug):
        self.write('test {0}'.format(slug))


def decide_app_type():
    import tornado.options
    opts = tornado.options.parse_command_line()

    if '--wsgi' in [o.lower() for o in opts]:
        return tornado.wsgi.WSGIApplication
    else:
        return tornado.web.Application

static_path = 'static/htdocs/'

settings = {
    'template_path': os.path.join(os.path.dirname(__file__), "templates"),
    'xsrf_cookies': True,
    'static_path': os.path.join(os.path.dirname(__file__), static_path),
}

handlers = [
    (r"/", HomeHandler),
    (r"/api/v.1/([^/]+)", MainHandler),
    (r"/api/graph/([^/]+)", GraphHandler),
    (r"/([^/]+)", wkHandler),
]


def wsgi():
    """wsgi app creator"""
    print('test1')
    return main(AppClass=tornado.wsgi.WSGIApplication)


def main(AppClass=tornado.web.Application):
    from tornado import autoreload
    application = AppClass(handlers, **settings)
    print('test2')
    if isinstance(application, tornado.wsgi.WSGIApplication):
        print('test3')
        return application
    application.listen(8888, address='127.0.0.1')
    ioloop = tornado.ioloop.IOLoop.instance()
    autoreload.watch(static_path)
    autoreload.watch('templates/index.html')
    autoreload.start(ioloop)
    ioloop.start()
    return application

if __name__ == '__main__':
    main()
