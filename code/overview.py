import os
import time
import hashlib
from pygments import highlight
from pygments.lexers import get_lexer_for_filename
from pygments.formatters import HtmlFormatter
from git import *
import web
from web import form
from common import *
from decorators import requires_login
from util import find
import gitHelper 

class allGroups:
    @requires_login
    def GET(self):
        web.header('Content-Type', 'text/html')
        grouplist = web.config.db.query(
            """SELECT
                groups.id AS id,
                groups.name AS name,
                groups.owner AS owner,
                groups.description AS description,
                COUNT(group_users.userid) AS num_users,
                COUNT(repositories.id) AS num_repos
              FROM groups
                LEFT JOIN group_users ON groups.id = group_users.groupid
                LEFT JOIN repositories ON groups.id = repositories.owner
              GROUP BY groups.id
              ORDER BY UPPER(groups.owner)""").list()
        
        return render.allGroups(groups=grouplist)

class allRepositories:
    @requires_login
    def GET(self):
        web.header('Content-Type', 'text/html')
        repolist = web.config.db.query(
            """SELECT id, name, owner, description
               FROM repositories
               WHERE access = 'public'
               ORDER BY UPPER(owner)""").list()
        
        return render.allRepositories(repos=repolist)



