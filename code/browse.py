import os
import time
import hashlib
import itertools
from pygments import highlight
from pygments.lexers import get_lexer_for_filename, get_lexer_by_name
from pygments.formatters import HtmlFormatter
from git import *
import web
from web import form
from common import *
import queries
from decorators import requires_login, requires_repo_access, requires_group_admin
from util import find
import gitHelper

class owner:
    @requires_login
    def GET(self, owner):
        web.header('Content-Type', 'text/html')
        userinfo = web.config.db.select("owners", dict(u=owner), where="id=$u").list()
        if len(userinfo) != 1:
            raise web.notfound()

        if userinfo[0].type == "group":
            return self.GET_group(owner)
        elif userinfo[0].type in ["ldapuser", "localuser"]:
            return self.GET_user(owner)
        else:
            raise web.internalerror("Unexpected user type")

    def GET_group(self, owner):
        groupinfo = web.config.db.select("groups", dict(u=owner), where="id=$u").list()
        if len(groupinfo) != 1:
            return web.internalerror("Couldn't find user information")
        
        repos = queries.repos_for_owner(owner).list()
        for r in repos:
            repo = Repo(os.path.join(web.config.reporoot, r.owner, r.id + ".git"))
            r.lastUpdate = gitHelper.get_last_commit_time(repo)
        
        members = queries.members_for_group(owner).list()
        role = [m['role'] for m in members if m['id'] == web.config.session.userid]

        if len(role) == 1:
            users = web.config.db.select('users', what='id,name').list()
            users = [u for u in users if u.id not in [m['id'] for m in members]]
            return render.groupPageForMembers(group=groupinfo[0], repos=repos, members=members, role=role[0], users=users)
        else:
            return render.groupPageForVisitors(group=groupinfo[0], repos=repos, members=members)

    def GET_user(self, owner):
        userinfo = web.config.db.select("users", dict(u=owner), where="id=$u").list()
        if len(userinfo) != 1:
            return web.internalerror("Couldn't find user information")

        userinfo = userinfo[0]
        auth = [m for m in web.config.auth.methods if m.get_usertype() == userinfo.type][0]
        userinfo.joined = auth.get_join_date(userinfo.identifier, web.config)

        repos = queries.viewable_repos_for_user(owner, web.config.session.userid).list()
        for r in repos:
            repo = Repo(os.path.join(web.config.reporoot, r.owner, r.repoid + ".git"))
            r.lastUpdate = gitHelper.get_last_commit_time(repo)

        groups = queries.groups_with_membership_for_user(owner).list()

        return render.userPage(user=userinfo, repos=repos, groups=groups)

    @requires_login
    @requires_group_admin
    def POST(self, group):
        userinfo = web.config.db.select("owners", dict(u=group), where="id=$u").list()
        if len(userinfo) != 1:
            raise web.notfound()

        if userinfo[0].type != "group":
            raise web.internalerror("Unexpected user type")

        postvars = web.input()
        if 'type' not in postvars:
            return web.badrequest("Invalid parameters")

        if postvars.type == 'user':
            if 'userid' not in postvars:
                return web.badrequest("Invalid parameters")

            web.config.db.insert('group_users', groupid=group, userid=postvars.userid, role='member')
        elif postvars.type == 'info':
            if 'joinable' not in postvars:
                return web.badrequest("Invalid parameters")
            if 'desc' not in postvars:
                postvars.desc = ""
            
            if postvars.joinable not in ["yes", "no"]:
                return web.internalerror("Invalid joinable setting")

            joinable = 1 if postvars.joinable == "yes" else 0
            web.config.db.update('groups', where="id=$g", vars={'g':group}, description=postvars.desc, joinable=joinable)
        elif postvars.type == 'remove':
            if 'userid' not in postvars:
                return web.badrequest("Invalid parameters")

            web.config.db.delete('group_users', where="groupid=$g and userid=$u", vars={'g':group, 'u':postvars.userid})
        elif postvars.type == 'rights':
            if 'userid' not in postvars or 'access' not in postvars:
                return web.badrequest("Invalid parameters")
            if postvars.access not in ["admin"]:
                return web.internalerror("Invalid user right")

            web.config.db.update('group_users', where="groupid=$g and userid=$u", vars={'g':group, 'u':postvars.userid}, role='admin')
        elif postvars.type == 'delete':
            if postvars.confirm != "yes, I really want to delete this group":
                return web.seeother("/%s" % owner)

            transaction = web.config.db.transaction()
            try:
                web.config.db.delete('group_users', where="groupid=$g", vars={'g':group})
                web.config.db.delete('groups', where="id=$g", vars={'g':group})
            except Exception, e:
                transaction.rollback()
                print e
                return web.internalerror("Couldn't delete repository")
            transaction.commit()
            return web.seeother("/")

        return web.seeother("/%s" % group)

def get_common_repo_info(owner, repoId):
    d = dict(o=owner, i=repoId, u=web.config.session.userid)
    repoInfo = web.config.db.select('repositories', d, where="id=$i and owner=$o", what="description,access,name").list()
    if len(repoInfo) != 1:
        return None

    repoInfo = repoInfo[0]
    curUserRights = web.config.db.select('repo_access', d, where="repoid=$i and repoowner=$o and userid=$u", what="access").list()
    if len(curUserRights) == 1:
        repoInfo.userLevel = curUserRights[0]['access']

    return repoInfo

class repositoryHome:
    @requires_login
    @requires_repo_access
    def GET(self, owner, repoId):
        web.header('Content-Type', 'text/html')

        repoInfo = get_common_repo_info(owner, repoId)
        if repoInfo == None:
            return web.internalerror("Invalid repository")
        
        repo = Repo(os.path.join(web.config.reporoot, owner, repoId + ".git"))
        if 'master' not in repo.heads:
            return render.showRepoFiles(owner=owner, repoid=repoId, repoInfo=repoInfo, path="", filelist=[])
        
        tree = repo.heads.master.commit.tree
        curHashes = [entry.hexsha for entry in tree]
        changeinfo = gitHelper.get_last_updating_commit(repo, 'master', curHashes)
        filelist = [(entry, changeinfo[entry.hexsha]) for entry in tree]
        
        return render.showRepoFiles(owner=owner, repoid=repoId, repoInfo=repoInfo, path="", filelist=filelist)

class repositoryCommit:
    @requires_login
    @requires_repo_access
    def GET(self, owner, repoId, commitId):
        web.header('Content-Type', 'text/html')
        
        repoInfo = get_common_repo_info(owner, repoId)
        if repoInfo == None:
            return web.internalerror("Invalid repository")

        try:
            repo = Repo(os.path.join(web.config.reporoot, owner, repoId + ".git"))
            commit = repo.commit(commitId)
            changes = itertools.chain.from_iterable((p.diff(commit) for p in commit.parents))
            
            return render.showRepoCommit(owner=owner, repoid=repoId, repoInfo=repoInfo, commit=commit, changes=changes)
        except BadObject, e:
            raise web.notfound()
        

class repositoryCommits:
    @requires_login
    @requires_repo_access
    def GET(self, owner, repoId, branch):
        web.header('Content-Type', 'text/html')

        repoInfo = get_common_repo_info(owner, repoId)
        if repoInfo == None:
            return web.internalerror("Invalid repository")
            
        repo = Repo(os.path.join(web.config.reporoot, owner, repoId + ".git"))
        commits = repo.iter_commits('master', max_count=20)
       
        return render.showRepoCommits(owner=owner, repoid=repoId, repoInfo=repoInfo, commits=commits)

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

    @requires_login
    @requires_repo_access
    def GET(self, owner, repoId, branch, filepath):
        web.header('Content-Type', 'text/html')
        repo = Repo(os.path.join(web.config.reporoot, owner, repoId + ".git"))

        repoInfo = get_common_repo_info(owner, repoId)

        curnode = repo.heads.master.commit.tree
        try:
            for segment in path_parts(filepath):
                curnode = curnode[segment]
        except KeyError, e:
            return web.notfound()

        try:
            lexer = get_lexer_for_filename(filepath)
        except:
            lexer = get_lexer_by_name("text")
        formatter = HtmlFormatter(linenos=True, cssclass="code")
        style = formatter.get_style_defs()
        style = """
            .codetable tr { vertical-align:top; }
            .codetable pre { border:0px; }
            %s
            """ % style

        rawcontent = curnode.data_stream.read().decode('utf-8')
        content = highlight(rawcontent, lexer, formatter) 

        fileinfo = {
            'path': filepath,
            'name': os.path.basename(filepath),
            'extension': os.path.splitext(filepath)[1],
            'size': curnode.size,
            'lines': rawcontent.count('\n')}
        
        return render.showRepoFile(owner=owner, repoid=repoId, repoInfo=repoInfo, file=fileinfo, style=style, content=content)
            
class repositoryShowDirectory:
    @requires_login
    @requires_repo_access
    def GET(self, owner, repoId, branch, dirpath):
        web.header('Content-Type', 'text/html')

        repoInfo = get_common_repo_info(owner, repoId)
        if repoInfo == None:
            return web.internalerror("Invalid repository")

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
       
        return render.showRepoFiles(owner=owner, repoid=repoId, repoInfo=repoInfo, path=dirpath, filelist=filelist)


