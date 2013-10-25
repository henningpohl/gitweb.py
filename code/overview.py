import os
import time
import hashlib
from pygments import highlight
from pygments.lexers import get_lexer_for_filename
from pygments.formatters import HtmlFormatter
from git import *
import web
from web import form
from decorators import requires_login
from util import find
import gitHelper

render = web.template.render(
    'templates/',
    base='main',
    globals={'time':time, 'session':web.config.session, 'ctx':web.ctx})

 

class allGroupss:
    @requires_login
    def GET(self):
        grouplist = web.config.db.query(
            """SELECT
                groups.id AS id,
                groups.name AS name,
                groups.owner AS owner,
                groups.description AS description,
                COUNT(group_users.userid) AS num_users,
                COUNT(repositories.id) AS num_repos
              FROM groups
                INNER JOIN group_users ON groups.id = group_users.groupid
                INNER JOIN repositories ON groups.id = repositories.owner""").list()
        
        return render.allGroups(grouplist)

class allRepositories:
    @requires_login
    def GET(self):
        repolist = web.config.db.query(
            """SELECT id, name, owner, description
               FROM repositories
               WHERE access = 'public'""").list()
        
        return render.allRepositories(repolist)



