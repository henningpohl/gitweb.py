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
        if rights == "administrator":
            return func(*args, **kwargs)
        else:
            raise web.seeother('/')
    return wrapped

