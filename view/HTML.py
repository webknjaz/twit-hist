#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Twitter History @ DOU Hack

Front-end HTML output
"""

import sys
import os.path
CURRENT_DIR = os.path.dirname(__file__)
sys.path.append(CURRENT_DIR)

import cherrypy

import protection

db = protection.db

from jinja2 import Environment, PackageLoader
twi_env = Environment(loader=PackageLoader('twit_hist', 'static/tpl/'))

import locale
locale.setlocale(locale.LC_ALL, 'uk_UA')

GLOBAL_STRINGS = {'version_stage': 'pre-alpha', 'sitetitle': 'Twitter History'}

class TwiHist:
    _cp_config = {'tools.sessions.on': True}
    
    @cherrypy.expose
    def index(self, name = None):
        # Increase the silly hit counter
        count = cherrypy.session.get('count', 0) + 1
        # Store the new value in the session dictionary
        cherrypy.session['count'] = count

        # Ask for the user's name.
        if name is not None:
            cherrypy.session['name'] = name
        
        articles = db.getArticles()
        return twi_env.get_template('articles/list/index.tpl').render(GLOBAL_STRINGS, articles = articles)

    @cherrypy.expose
    def default(self, x=None):
        return 'Error: Cannot parse following URL ' + x + '. Trying to get required article'

from view import HTML

Root = HTML.TwiHist

from view import JSON

Root.json = JSON.Twihist

conf = os.path.join(CURRENT_DIR, 'twit_hist.conf')

