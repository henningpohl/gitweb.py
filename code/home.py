import os
import time
import hashlib
from git import *
import web
from web import form
import register
from util import find
from decorators import requires_login
import gitHelper

render = web.template.render(
    'templates/',
    base='main',
    globals={'time':time, 'session':web.config.session})

class home:
    def GET(self):
        if web.config.session.loggedin:
            return self.home_page()
        else:
            return self.welcome_page()

    def welcome_page(self):
        return render.welcomePage(web.config.pagename, web.config.auth.methods, register.register_form)

    def home_page(self):
        projectlist = web.config.db.query(
            """SELECT projects.id, projects.name FROM project_users
               INNER JOIN projects
               ON project_users.projectid = projects.id
               WHERE project_users.userid = $u""", vars=dict(u=web.config.session.userid)).list()
        
        repolist = web.config.db.query(
            """SELECT repositories.id, repositories.owner, repositories.name FROM repo_users
               INNER JOIN repositories
               ON repo_users.repoid = repositories.id
               WHERE repo_users.userid = $u""", vars=dict(u=web.config.session.userid)).list()

        commits = []
        for r in repolist:
            repo = Repo(os.path.join(web.config.reporoot, r.owner, r.id + ".git"))
            for c in repo.iter_commits('master', max_count=10):
                commits.append(web.utils.storage(
                    ownerid = r.owner,
                    repoid = r.id,
                    date = c.authored_date,
                    author = c.author,
                    message = c.message))
        
        return render.homePage(commits, projectlist, repolist)


    


