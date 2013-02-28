import os
import web

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


