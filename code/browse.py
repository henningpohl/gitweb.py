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
        userinfo = web.config.db.select("owners", dict(u=owner), where="id=$u").list()
        if len(userinfo) != 1:
            raise web.notfound()

        if userinfo[0].type == "project":
            return self.GET_project(owner)
        else:
            return self.GET_user(owner)
        
    def GET_project(self, owner):
        projectinfo = web.config.db.select("projects", dict(u=owner), where="id=$u").list()
        if len(projectinfo) != 1:
            return web.internalerror("Couldn't find user information")
        
        repoquery = web.config.db.query(
            """SELECT repositories.id, repositories.owner, repositories.name
               FROM repo_users INNER JOIN repositories
               ON repo_users.repoid = repositories.id
               WHERE repo_users.userid = $u""", vars=dict(u=owner))

        memberquery = web.config.db.query(
            """SELECT users.id AS id, project_users.role AS role, users.name AS name
               FROM project_users INNER JOIN users
               ON project_users.userid = users.id
               WHERE project_users.projectid = $u""", vars=dict(u=owner))

        return render.projectPage(projectinfo[0], repoquery, memberquery)   

    def GET_user(self, owner):
        userinfo = web.config.db.select("users", dict(u=owner), where="id=$u").list()
        if len(userinfo) != 1:
            return web.internalerror("Couldn't find user information")
        
        repoquery = web.config.db.query(
            """SELECT repositories.id, repositories.owner, repositories.name FROM repo_users
               INNER JOIN repositories
               ON repo_users.repoid = repositories.id
               WHERE repo_users.userid = $u""", vars=dict(u=owner))

        projectquery = web.config.db.query(
            """SELECT project_users.projectid AS id, projects.name AS name
               FROM project_users INNER JOIN projects
               ON project_users.projectid = projects.id
               WHERE project_users.userid = $u""", vars=dict(u=owner))

        return render.userPage(userinfo[0], repoquery, projectquery)   

class repositoryHome:
    def GET(self, owner, repoId):
        d = dict(o=owner,i=repoId,u=web.config.session.userid)
        repoInfo = web.config.db.select('repositories', d, where="id=$i and owner=$o", what="description,access,name").list()
        if len(repoInfo) != 1:
            return web.internalerror("Invalid repository")

        repoInfo = repoInfo[0]
        curUserRights = web.config.db.select('repo_users', d, where="repoid=$i and repoowner=$o and userid=$u", what="access").list()
        if len(curUserRights) == 1 and curUserRights[0].access == "admin":
            repoInfo.userLevel = "admin"
        
        repo = Repo(os.path.join(web.config.reporoot, owner, repoId + ".git"))
        if 'master' not in repo.heads:
            return render.showRepoFiles(owner, repoId, repoInfo, [])
        
        tree = repo.heads.master.commit.tree
        curHashes = [entry.hexsha for entry in tree]
        changeinfo = gitHelper.get_last_updating_commit(repo, 'master', curHashes)
        filelist = [(entry, changeinfo[entry.hexsha]) for entry in tree]
        
        return render.showRepoFiles(owner, repoId, repoInfo, filelist)

class repositoryCommits:
    def GET(self, owner, repoId, branch):
        d = dict(o=owner,i=repoId,u=web.config.session.userid)
        repoInfo = web.config.db.select('repositories', d, where="id=$i and owner=$o", what="description,access,name").list()
        if len(repoInfo) != 1:
            return web.internalerror("Invalid repository")

        repoInfo = repoInfo[0]
        curUserRights = web.config.db.select('repo_users', d, where="repoid=$i and repoowner=$o and userid=$u", what="access").list()
        if len(curUserRights) == 1 and curUserRights[0].access == "admin":
            repoInfo.userLevel = "admin"
            
        repo = Repo(os.path.join(web.config.reporoot, owner, repoId + ".git"))
        commits = repo.iter_commits('master', max_count=20)
       
        return render.showRepoCommits(owner, repoId, repoInfo, commits)

def path_parts(path):
    parts = []
    while path != "":
        path, tail = os.path.split(path)
        parts.append(tail)
    parts.reverse()
    return parts

class repositoryShowFile:
    def __get_file_handle(self, tree, filepath):
        for entry in tree.traverse():
            if entry.path == filepath:
                return entry
        return None
    
    def GET(self, owner, repoId, branch, filepath):
        repo = Repo(os.path.join(web.config.reporoot, owner, repoId + ".git"))

        curnode = repo.heads.master.commit.tree
        try:
            for segment in path_parts(filepath):
                curnode = curnode[segment]
        except KeyError, e:
            return web.notfound()

        lexer = get_lexer_for_filename(filepath)
        formatter = HtmlFormatter(linenos=True, cssclass="code")
        style = formatter.get_style_defs()
        style = """
            .codetable tr { vertical-align:top; }
            .codetable pre { border:0px; }
            %s
            """ % style
        code = highlight(curnode.data_stream.read(), lexer, formatter)
        
        return render.showFile(owner, repoId, filepath, style, code)
            
class repositoryShowDirectory:
    def GET(self, owner, repoId, branch, dirpath):
        repo = Repo(os.path.join(web.config.reporoot, owner, repoId + ".git"))

        curnode = repo.heads.master.commit.tree
        try:
            for segment in path_parts(dirpath):
                curnode = curnode[segment]
        except KeyError, e:
            return web.notfound()

        curHashes = [entry.hexsha for entry in curnode]
        changeinfo = gitHelper.get_last_updating_commit(repo, 'master', curHashes)
        filelist = [(entry, changeinfo[entry.hexsha]) for entry in curnode]
       
        return render.showRepoFiles(owner, repoId, filelist)


