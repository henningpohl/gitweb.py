import os
import time
import hashlib
import git
import web
from web import form
from decorators import requires_login

render = web.template.render(
    'templates/',
    base='main',
    globals={'time':time, 'session':web.config.session})

create_repo_form = form.Form(
    form.Dropdown("owner", args=["Yourself", "Some Project"], description="Owner"),
    form.Textbox("name", description="Name"),
    form.Textbox("id", description="id"),
    form.Textarea("desc", description="Description"),
    form.Radio("access", ["Public", "Private"], description="Access"),
    form.Button("submit", type="submit", description="Create repository"))

class create:
    @requires_login
    def GET(self):
        create_repo_form['owner'].args = [web.config.session.userid]
        return render.createRepo(create_repo_form)

    @requires_login
    def POST(self):
        f = create_repo_form()
        if not f.validates():
            return render.createRepo(f)

        v = dict(o=f.d.owner, i=f.d.id)
        u = web.config.db.select('repositories', v, where="id=$i and owner=$o", what="id").list()
        if len(u) != 0:
            return web.internalerror("Invalid repository")

        repoPath = os.path.join("repositories", f.d.owner, f.d.id + ".git")
        if os.path.exists(repoPath):
            print "Repository already exists."
            return web.internalerror("Repository already exists.")

        web.config.db.query("pragma foreign_keys=ON") # making sure constraints are enforced
        transaction = web.config.db.transaction()
        try:
            web.config.db.insert('repositories', id=f.d.id, name=f.d.name, owner=f.d.owner, description=f.d.desc)
            web.config.db.insert('repo_users', repoid=f.d.id, repoowner=f.d.owner, userid=f.d.owner)

            git.Repo.init(repoPath, bare=True)
            
            transaction.commit()
            return web.seeother("/%s/%s" % (f.d.owner, f.d.id))
        except Exception, e:
            transaction.rollback()
            print e
            return web.internalerror("Couldn't create repository")

