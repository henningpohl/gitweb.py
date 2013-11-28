import os
import time
import hashlib
from git import *
import web
from web import form
import register
from util import find
from decorators import requires_login
from common import *
import queries
import gitHelper

class home:
    def GET(self):
        web.header('Content-Type', 'text/html')
        if web.config.session.loggedin:
            return self.home_page()
        else:
            return self.welcome_page()

    def welcome_page(self):
        return render.welcomePage(form=register.register_form)

    def home_page(self):
        grouplist = queries.groups_for_user(web.config.session.userid).list()
        repolist = queries.repos_for_user(web.config.session.userid).list()

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
        commits = sorted(commits, key=lambda c: c.date, reverse=True)
        
        return render.homePage(news=commits[:10], groups=grouplist, repositories=repolist)


    


