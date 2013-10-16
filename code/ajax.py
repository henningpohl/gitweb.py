import os
import json
import web
from decorators import requires_login

class checkId:
    def GET(self):
        if 'id' not in web.input():
            return "false"
        
        u = web.config.db.select('users', dict(u=web.input().id), where="id=$u", what="id").list()
        if len(u) is 0:
            return "true"
        else:
            return "false"

class checkRepo:
    def GET(self):
        if 'id' not in web.input():
            return "false"

        if 'repo' not in web.input():
            return "false"

        v = dict(o=web.input().id, i=web.input().repo)
        u = web.config.db.select('repositories', v, where="id=$i and owner=$o", what="id").list()
        if len(u) is 0:
            return "true"
        else:
            return "false"

class getInfo:
    @requires_login
    def GET(self):
        if 'type' not in web.input():
            return ""

        if web.input().type == 'users':
            users = web.config.db.select('users', what='id,name').list()
            return json.dumps(users)
        else:
            return ""
        


