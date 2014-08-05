import os
import time
import hashlib
import shutil
import web
from web import form
from decorators import requires_login, requires_admin
from common import *
from util import make_id_string, check_id
from gitHelper import gen_repository_list

class adminPanel:
    @requires_admin
    @requires_login
    def GET(self):
        web.header('Content-Type', 'text/html')
        userlist = web.config.db.select("users").list()
        for u in userlist:
            auth = [m for m in web.config.auth.methods if m.get_usertype() == u.type][0]
            u.userrights = auth.get_rights(u.id, web.config)
        
        grouplist = web.config.db.select("groups").list()
        repositorylist = web.config.db.select("repositories").list()

        filesystemrepos = set(gen_repository_list("repositories"))
        databaserepos = web.config.db.select("repositories", what="owner, id").list()
        databaserepos = set(os.path.join(dr.owner, dr.id + ".git") for dr in databaserepos)

        notindatabaserepos = filesystemrepos.difference(databaserepos)
        #notindatabaserepos = [os.path.split(nr) for nr in notindatabaserepos]
       
        return render.adminPanel(userlist=userlist, grouplist=grouplist, repositorylist=repositorylist, lostRepos=notindatabaserepos)
        

    @requires_admin
    @requires_login  
    def POST(self):
        web.header('Content-Type', 'text/plain')
        web.header('Cache-control', 'no-cache')        
        cmd = web.input()
        if cmd.action == "deleteRepo":
            return self.delete_repo(cmd.ownerId, cmd.repoId)
        elif cmd.action == "deleteUser":
            return self.delete_user(cmd.userId, cmd.userType)
        elif cmd.action == "promoteUser":
            return self.promote_user(cmd.userId)
        elif cmd.action == "demoteUser":
            return self.demote_user(cmd.userId)
        elif cmd.action == "approveUser":
            return self.approve_user(cmd.userId)
        elif cmd.action == "deleteGroup":
            return self.delete_group(cmd.groupId)
        elif cmd.action == "assignLostRepo":
            return self.assign_lost_repo(cmd.repopath, cmd.userid)
        elif cmd.action == "deleteLostRepo":
            return self.delete_lost_repo(cmd.repopath)
        else:
            return "error"

    def delete_repo(self, ownerid, repoid):
        p = dict(u=repoid, o=ownerid)
        web.config.db.delete("repositories", where="id=$u AND owner=$o", vars=p)
        web.config.db.delete("repo_users", where="repoid=$u AND repoowner=$o", vars=p)

        repopath = os.path.abspath(os.path.join(web.config.reporoot, ownerid, repoid + ".git"))
        if repopath.startswith(os.path.abspath(web.config.reporoot)) == False:
            raise internalerror("Access to directories outside repository root forbidden")
        
        shutil.rmtree(repopath)

    def delete_group(self, groupid):
        web.config.db.delete("group_users", where="groupid=$u", vars=dict(u=groupid))
        web.config.db.delete("groups", where="id=$u", vars=dict(u=groupid))
        return "deleted"

    def delete_user(self, userid, usertype):
        if usertype == "localuser":
            web.config.db.delete("localusers", where="id=$u", vars=dict(u=userid))
        elif usertype == "ldapuser":
            web.config.db.delete("ldapusers", where="id=$u", vars=dict(u=userid))
        else:
            return "error"
        return "deleted"

    def promote_user(self, userid):
        web.config.db.update("owners", where="id=$u", vars=dict(u=userid), rights="admin")
        if web.config.session.userid == userid:
            web.config.session.userrights = "admin"
        
        return "promoted"

    def demote_user(self, userid):
        web.config.db.update("owners", where="id=$u", vars=dict(u=userid), rights="member")
        if web.config.session.userid == userid:
            web.config.session.userrights = "member"
        return "demoted"

    def approve_user(self, userid):
        web.config.db.update("owners", where="id=$u", vars=dict(u=userid), rights="member")
        return "approved"
    
    def assign_lost_repo(self, repopath, userid):        
        reponame = os.path.split(repopath)[-1]
        reponame = ".".join(reponame.split(".")[:-1])
        oldrepopath = os.path.join(web.config.reporoot, repopath)
        newrepopath = os.path.join(web.config.reporoot, userid, reponame + ".git")

        if oldrepopath != newrepopath:
            if os.path.exists(newrepopath):
                raise web.internalerror("Won't transfer repository because of id clash.")
            os.rename(os.path.join(web.config.reporoot, repopath), newrepopath)

        web.config.db.insert("repositories", id=reponame, name=reponame, owner=userid)
        web.config.db.insert("repo_users", repoid=reponame, repoowner=userid, userid=userid)
        
        return "assigned"

    def delete_lost_repo(self, repopath):
        repopath = os.path.abspath(os.path.join(web.config.reporoot, repopath))
        if repopath.startswith(os.path.abspath(web.config.reporoot)) == False:
            raise internalerror("Access to directories outside repository root forbidden")
        
        shutil.rmtree(repopath)
        return "deleted"
