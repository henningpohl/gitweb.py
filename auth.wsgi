import os
import re

# http://www.davidfischer.name/2009/10/django-authentication-and-mod_wsgi/
# https://code.google.com/p/modwsgi/wiki/AccessControlMechanisms
def check_password(environ, user, password):
    if 'REQUEST_URI' not in environ:
        return None
    
    m = re.match(r"(?:/repositories)?/(\w+)/(\w+).git.*", environ['REQUEST_URI'])
    if m is None:
        return None
    
    owner, repo = m.groups()
    
    if user == 'test':
        if password == 'test':
            return True
        return False
    return None