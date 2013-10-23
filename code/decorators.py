import web

def requires_login(func):
    def wrapped(*args, **kwargs):
        if web.config.get('session', {}).get('loggedin', False):
            return func(*args, **kwargs)
        else:
            raise web.seeother('/')
    return wrapped

def requires_admin(func):
    def wrapped(*args, **kwargs):
        rights = web.config.get('session', {}).get('userrights', "none")
        if rights == "admin":
            return func(*args, **kwargs)
        else:
            raise web.seeother('/')
    return wrapped

def requires_repo_admin(func):
    def wrapped(*args, **kwargs):
        if len(args) != 3:
            raise web.seeother('/')

        d = dict(o=args[1],i=args[2],u=web.config.session.userid)
        curUserRights = web.config.db.select('repo_users', d, where="repoid=$i and repoowner=$o and userid=$u", what="access").list()
        if len(curUserRights) != 1 or curUserRights[0].access != "admin":
            raise web.seeother('/')
        else:
            return func(*args, **kwargs)
    return wrapped
