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

group_register_form = form.Form(
    form.Textbox("name", description="Group name"),
    form.Textbox("id", description="Identifier"),
    form.Textarea("desc", description="Description"),
    validators = [
        form.Validator("Invalid Identifier", lambda i: i.id == make_id_string(i.id)),
        form.Validator("Invalid Identifier (keyword clash)", lambda i: check_id(i.id))])

class create:
    @requires_login
    def GET(self):
        f = group_register_form()
        return render.createGroup(f)

    @requires_login
    def POST(self):
        f = group_register_form()
        if not f.validates():
            return render.createGroup(f)

        web.config.db.insert('groups', id=f.d.id, name=f.d.name, description=f.d.desc, owner=web.config.session.userid)
        raise web.seeother('/' + f.d.id)

