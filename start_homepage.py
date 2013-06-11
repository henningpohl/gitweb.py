import os
import sys

# http://www.hyperink.com/blog/?p=13
try:
    app_path = os.path.abspath(os.path.dirname(__file__))
except NameError:
    app_path = os.path.abspath(".")

sys.path.append(app_path)
sys.path.append(os.path.join(app_path, "code"))
os.chdir(app_path)

# hack to patch up web.validip6addr for windows systems
import socket
if 'inet_pton' not in socket.__all__:
    def inet_pton(t, a):
        raise socket.error
    socket.inet_pton = inet_pton

import time
import web

urls = (
  '/favicon.ico',                             'favicon',
  '/',                                        'home.home',
  '/register',                                'register.register',
  '/login',                                   'login.login',
  '/logout',                                  'login.logout',
  '/checkId',                                 'ajax.checkId',
  '/checkRepo',                               'ajax.checkRepo',
  '/newRepository',                           'repositories.create',
  '/newProject',                              'projects.create',
  '/adminPanel',                              'admin.adminPanel',
  '/([\w\-]+)',                               'browse.owner',
  '/([\w\-]+)/([\w\-]+)/commits/([\w\-]+)',   'browse.repositoryCommits',
  '/([\w\-]+)/([\w\-]+)/blob/([\w\-]+)/(.+)', 'browse.repositoryShowFile',
  '/([\w\-]+)/([\w\-]+)/tree/([\w\-]+)/(.+)', 'browse.repositoryShowDirectory',
  '/([\w\-]+)/([\w\-]+)',                     'browse.repositoryHome',  
)

app = web.application(urls, globals(), autoreload=False)

import config

if web.config.get('_session') is None:
    #session = web.session.Session(app, web.session.DBStore(web.config.db, 'sessions'), {'loggedin': False})
    session = web.session.Session(app, web.session.DiskStore('sessions'), {'loggedin': False})
    web.config.session = session

class favicon:
    def GET(self):
        raise web.redirect("/static/favicon.ico")

def notfound():
    return web.notfound("404")
app.notfound = notfound

if __name__ == "__main__":
    sys.argv.append("7000") # run on port 7000
    app.run()
else:
    web.config.debug = False
    application = app.wsgifunc()
    
