import os
import time
import hashlib
import git
import web
from web import form
from decorators import requires_login, requires_repo_admin

render = web.template.render(
    'templates/',
    base='main',
    globals={'time':time, 'session':web.config.session, 'ctx':web.ctx})

create_repo_form = form.Form(
    form.Dropdown("owner", args=["Yourself", "Some Project"], description="Owner"),
    form.Textbox("name", description="Name"),
    form.Textbox("id", description="id"),
    form.Textarea("desc", description="Description"),
    form.Radio("access", ["public", "private"], description="Access"),
    form.Button("submit", type="submit", description="Create repository"))

class create:
    @requires_login
    def GET(self):
        userid = web.config.session.userid
        project_query = web.config.db.select('project_users', dict(u=userid), where="userid=$u", what="projectid")
        projectids = [p.projectid for p in project_query]
        projectids = [userid] + projectids
        create_repo_form['owner'].args = projectids
        return render.createRepo(create_repo_form)

    @requires_login
    def POST(self):
        f = create_repo_form()
        if not f.validates():
            return render.createRepo(f)

        v = dict(o=f.d.owner, i=f.d.id)
        u = web.config.db.select('repositories', v, where="id=$i and owner=$o", what="id").list()
        if len(u) != 0:
            return web.internalerror("Invalid repository id. Repository already exists.")

        repoPath = os.path.join("repositories", f.d.owner, f.d.id + ".git")
        if os.path.exists(repoPath):
            print "Repository already exists."
            return web.internalerror("Repository already exists.")

        web.config.db.query("pragma foreign_keys=ON") # making sure constraints are enforced
        transaction = web.config.db.transaction()
        try:
            print f.d
            web.config.db.insert('repositories', id=f.d.id, name=f.d.name, owner=f.d.owner, description=f.d.desc, access=f.d.access)
            # A trigger adds rights to repo_users at this point
            git.Repo.init(repoPath, bare=True)
            transaction.commit()
            return web.seeother("/%s/%s" % (f.d.owner, f.d.id))
        except Exception, e:
            transaction.rollback()
            print e
            return web.internalerror("Couldn't create repository")

class settings:
    @requires_login
    @requires_repo_admin
    def GET(self, owner, repoId):
        d = dict(o=owner,i=repoId,u=web.config.session.userid)
        repoInfo = web.config.db.select('repositories', d, where="id=$i and owner=$o", what="description,access,name").list()
        if len(repoInfo) != 1:
            return web.internalerror("Invalid repository")

        collaborators = web.config.db.select('repo_users', d, where="repoid=$i and repoowner=$o", what="userid,access").list()
        cids = [c.userid for c in collaborators]
        users = web.config.db.select('users', what='id,name').list()
        users = [u for u in users if u.id not in cids]
        
        return render.repoSettings(owner, repoId, repoInfo[0], collaborators, users)

    @requires_login
    @requires_repo_admin
    def POST(self, owner, repoId):
        postvars = web.input()
        
        if 'type' not in postvars:
            return web.badrequest("Invalid parameters")

        d = dict(o=owner,i=repoId,u=postvars.userid)
        if postvars.type == 'user':
            if 'userid' not in postvars or 'access' not in postvars:
                return web.badrequest("Invalid parameters")
            if postvars.access not in ["read", "write", "admin"]:
                return web.internalerror("Invalid user right")

            web.config.db.insert('repo_users', repoid=repoId, repoowner=owner, userid=postvars.userid, access=postvars.access)
        elif postvars.type == 'info':
            if 'desc' not in postvars or 'access' not in postvars:
                return web.badrequest("Invalid parameters")
            
            if postvars.access not in ["public", "private"]:
                return web.internalerror("Invalid access setting")

            web.config.db.update('repositories', where="id=$i and owner=$o", vars=d, description=postvars.desc, access=postvars.access)
        elif postvars.type == 'remove':
            if 'userid' not in postvars:
                return web.badrequest("Invalid parameters")

            web.config.db.delete('repo_users', where="repoid=$i and repoowner=$o and userid=$u", vars=d)
        elif postvars.type == 'rights':
            if 'userid' not in postvars or 'access' not in postvars:
                return web.badrequest("Invalid parameters")
            if postvars.access not in ["read", "write", "admin"]:
                return web.internalerror("Invalid user right")

            web.config.db.update('repo_users', where="repoid=$i and repoowner=$o and userid=$u", vars=d, access=postvars.access)
        return web.seeother("/%s/%s/settings" % (owner, repoId))

