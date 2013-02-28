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

class owner:
    @requires_login
    def GET(self, owner):

        userinfo = web.config.db.select("users", dict(u=owner), where="id=$u").list()
        if len(userinfo) != 1:
            return web.internalerror("Couldn't find user information")
        
        repoquery = web.config.db.query(
            """SELECT repositories.id, repositories.owner, repositories.name FROM repo_users
               INNER JOIN repositories
               ON repo_users.repoid = repositories.id
               WHERE repo_users.userid = $u""", vars=dict(u=owner))

        return render.userPage(userinfo[0], repoquery)

class repositoryFiles:
    def GET(self, owner, repoId):

        repo = Repo(os.path.join(web.config.reporoot, owner, repoId + ".git"))
        if 'master' not in repo.heads:
            return render.showRepoFiles(owner, repoId, [])
        
        tree = repo.heads.master.commit.tree
        curHashes = [entry.hexsha for entry in tree]
        changeinfo = gitHelper.get_last_updating_commit(repo, 'master', curHashes)
        filelist = [(entry.name, changeinfo[entry.hexsha]) for entry in tree]
        
        return render.showRepoFiles(owner, repoId, filelist)

class repositoryCommits:
    def GET(self, owner, repoId, branch):

        repo = Repo(os.path.join(web.config.reporoot, owner, repoId + ".git"))
        commits = repo.iter_commits('master', max_count=20)
       
        return render.showRepoCommits(owner, repoId, commits)

class repositoryShowFile:
    def GET(self, owner, repoId, branch, filepath):
        repo = Repo(os.path.join(web.config.reporoot, owner, repoId + ".git"))

        fileblob = find(repo.heads.master.commit.tree.blobs, lambda x: x.name == filepath)
        if fileblob is None:
            return web.notfound()

        lexer = get_lexer_for_filename(filepath)
        formatter = HtmlFormatter(linenos=True, cssclass="code")
        style = formatter.get_style_defs()
        style = """
            .codetable tr { vertical-align:top; }
            .codetable pre { border:0px; }
            %s
            """ % style
        code = highlight(fileblob.data_stream.read(), lexer, formatter)
        
        return render.showFile(owner, repoId, filepath, style, code)

    


