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

 

class allProjects:
    @requires_login
    def GET(self):
        projectlist = web.config.db.query(
            """SELECT
                projects.id AS id,
                projects.name AS name,
                projects.owner AS owner,
                projects.description AS description,
                COUNT(project_users.userid) AS num_users,
                COUNT(repositories.id) AS num_repos
              FROM projects
                INNER JOIN project_users ON projects.id = project_users.projectid
                INNER JOIN repositories ON projects.id = repositories.owner""").list()
        
        return render.allProjects(projectlist)

class allRepositories:
    @requires_login
    def GET(self):
        repolist = web.config.db.query(
            """SELECT id, name, owner, description
               FROM repositories
               WHERE access = 'public'""").list()
        
        return render.allRepositories(repolist)



