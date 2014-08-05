import os
import time
import web
from sqlite3 import IntegrityError
from web import form
from util import make_id_string, check_id
from common import *
from decorators import requires_login, requires_group_admin

group_register_form = form.Form(
    form.Textbox("name", description="Group name"),
    form.Textbox("id", description="Identifier"),
    form.Textarea("desc", description="Description"),
    form.Radio("joinable", ["yes", "no"], description="Joinable"),
    validators = [
        form.Validator("Invalid characters in ID", lambda i: i.id == make_id_string(i.id)),
        form.Validator("Invalid ID (keyword clash)", lambda i: check_id(i.id)),
        form.Validator("ID too short", lambda i: len(i.id) > 3)])

class create:
    @requires_login
    def GET(self):
        web.header('Content-Type', 'text/html')
        f = group_register_form()
        return render.createGroup(form=f)

    @requires_login
    def POST(self):
        web.header('Content-Type', 'text/html')
        f = group_register_form()
        if not f.validates():
            return render.createGroup(form=f)

        joinable = 1 if f.d.joinable == 'yes' else 0

        try:
            web.config.db.insert('groups', id=f.d.id, name=f.d.name, description=f.d.desc, owner=web.config.session.userid, joinable=joinable)
        except IntegrityError, e:
            raise web.internalerror(e)
            return render.error(message=e)
        
        raise web.seeother('/' + f.d.id)
