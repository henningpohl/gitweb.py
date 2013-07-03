import os
import time
import web
from web import form
from util import make_id_string, check_id
from decorators import requires_login

render = web.template.render(
    'templates/',
    base='main',
    globals={'time':time, 'session':web.config.session})

project_register_form = form.Form(
    form.Textbox("name", description="Project name"),
    form.Textbox("id", description="Identifier"),
    form.Textarea("desc", description="Description"),
    validators = [
        form.Validator("Invalid Identifier", lambda i: i.id == make_id_string(i.id)),
        form.Validator("Invalid Identifier (keyword clash)", lambda i: check_id(i.id))])

class create:
    @requires_login
    def GET(self):
        f = project_register_form()
        return render.createProject(f)

    @requires_login
    def POST(self):
        f = project_register_form()
        if not f.validates():
            return render.createProject(f)

        web.config.db.insert('projects', id=f.d.id, name=f.d.name, description=f.d.desc, owner=web.config.session.userid)
        raise web.seeother('/' + f.d.id)

