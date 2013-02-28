import os
import time
import web

render = web.template.render(
    'templates/',
    base='main',
    globals={'time':time, 'session':web.config.session})


class create:
    def GET(self):
        return "Project creation here"

