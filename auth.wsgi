import sys
import os
import re
try:
    app_path = os.path.abspath(os.path.dirname(__file__))
except NameError:
    app_path = os.path.abspath(".")
sys.path.append(app_path)
sys.path.append(os.path.join(app_path, "code"))
import web
os.chdir(app_path)
import config
from auth import RequireRegistrationException

def get_rights(userid, ownerid, repoid):
    access = web.config.db.select("repo_users", what='access', where=web.db.sqlwhere({
        'repoid':repoid, 'repoowner':ownerid, 'userid': userid
        }))
    if bool(access) == False:
        return None
    else:
        return list(access)[0].access

# http://www.samba.org/~jelmer/dulwich/docs/protocol.html
def check_rights(request, userid, ownerid, repoid):
    rights = get_rights(userid, ownerid, repoid)

    if 'git-upload-pack' in request:
        # require at least read rights
        return rights in ['read', 'write', 'admin']
    elif 'git-receive-pack' in request:
        # require at least write rights
        return rights in ['read', 'write', 'admin']
    else:
        return False
 
# http://www.davidfischer.name/2009/10/django-authentication-and-mod_wsgi/
# https://code.google.com/p/modwsgi/wiki/AccessControlMechanisms
def check_password(environ, user, password):
    if 'REQUEST_URI' not in environ:
        return None
   
    m = re.match(r"(?:/repositories)?/(\w+)/(\w+).git.*", environ['REQUEST_URI'])
    if m is None:
        return None
    
    owner, repo = m.groups()

    authOptions = [am for am in web.config.auth.methods if am.can_handle_user(user)]
    if len(authOptions) == 0:
        return None

    for ao in authOptions:
        try:
            success, res = ao.login(user, password, web.config)
            if success == True:
                return check_rights(environ['REQUEST_URI'], res['userid'], owner, repo)
        except RequireRegistrationException, info:
            return False
    return None
