from datetime import datetime
import os
import os.path
from tornado import autoreload
import tornado.ioloop
import tornado.web
import json
import crawler3

FROM = datetime(2000, 1, 1)
TO = datetime(2100, 1, 1)


class MainHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self, htag):
        c = crawler3.Crawler()
        c.crawl_tweets([htag])
        tweets = c.find_tweets(htag, FROM, TO, 1000)
        del c
        self.write(json.dumps({'htag': htag, 'count': len(tweets), 'results': list(tweets)}))
        del tweets
        self.finish()

class GraphHandler(tornado.web.RequestHandler):
    def get(self, htag):
        c = crawler3.Crawler()
        data = c.graph_data(htag, FROM, TO)
        del c
        # data = [[161.2, 51.6], [167.5, 59.0], [159.5, 49.2], [157.0, 63.0], [155.8, 53.6]]
        self.write(json.dumps(data))
        del data


class HomeHandler(tornado.web.RequestHandler):
    def get(self):
        c = crawler3.Crawler()
        htags = c.htags()
        del c
        self.render('index.html', **{'htags': json.dumps(sorted(htags))})
        del htags

class wkHandler(tornado.web.RequestHandler):
    def get(self, slug):
        self.write('test {0}'.format(slug))

static_path = 'static/htdocs/'

settings = {
    'template_path': os.path.join(os.path.dirname(__file__), "templates"),
    'xsrf_cookies': True,
    'static_path': os.path.join(os.path.dirname(__file__), static_path),
}

import tornado.options
tornado.options.parse_command_line()
application = tornado.web.Application([
    (r"/", HomeHandler),
    (r"/api/v.1/([^/]+)", MainHandler),
    (r"/api/graph/([^/]+)", GraphHandler),
    (r"/([^/]+)", wkHandler),
], **settings)

if __name__ == "__main__":
    application.listen(8888)
    ioloop = tornado.ioloop.IOLoop.instance()
    tornado.autoreload.watch(static_path)
    tornado.autoreload.watch('templates/index.html')
    tornado.autoreload.start(ioloop)
    ioloop.start()
