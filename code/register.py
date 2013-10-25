import os
import time
import hashlib
import web
from web import form
from decorators import requires_login
from util import make_id_string, check_id

render = web.template.render(
    'templates/',
    base='main',
    globals={'time':time, 'session':web.config.session})

vpass = form.regexp(r".{3,}$", 'must be at least 3 characters long')
vemail = form.regexp(r".*@.*", "must be a valid email address")

register_form = form.Form(
    form.Textbox("name", id="form_name", description="Name"),
    form.Textbox("id", id="form_id", description="Identifier"), 
    form.Textbox("email", vemail, description="Email"),
    form.Password("password", vpass, description="Password"),
    form.Password("password2", description="Repeat password"),
    form.Button("submit", type="submit", description="Register"),
    validators = [
        form.Validator("Passwords did't match", lambda i: i.password == i.password2),
        form.Validator("Invalid Identifier", lambda i: i.id == make_id_string(i.id)),
        form.Validator("Invalid Identifier (uses keywords)", lambda i: check_id(i.id))])

ldap_register_form = form.Form(
    form.Textbox("username", description="Username"),
    form.Textbox("fullname", description="Name"),
    form.Textbox("id", description="Identifier"), 
    form.Button("submit", type="submit", description="Pick Identifier"),
    validators = [
        form.Validator("Invalid Identifier", lambda i: i.id == make_id_string(i.id)),
        form.Validator("Invalid Identifier (keyword clash)", lambda i: check_id(i.id))])

class register:
    def GET(self):
        if 'showIdentifierRegistration' not in web.config.session:
            raise web.seeother('/')

        f = ldap_register_form()
        f.username.value = web.config.session.userid
        f.fullname.value = web.config.session.userfullname
        f.id.value = make_id_string(web.config.session.userfullname)

        return render.ldapRegistration(f)

    def POST(self):        
        if 'email' in web.input():
            return self.local_registration()
        else:
            return self.ldap_registration()

    def ldap_registration(self):       
        f = ldap_register_form()        
        if not f.validates():
            return render.ldapRegistration(f)

        auth = [m for m in web.config.auth.methods if m.get_usertype() == 'ldapuser'][0]
        web.config.db.insert('ldapusers', id=f.d.id, username=f.d.username, name=f.d.fullname)
        web.config.session.loggedin = True
        web.config.session.userid = f.d.id
        web.config.session.userrights = auth.get_rights(f.d.username, web.config)
        del web.config.session.showIdentifierRegistration
        raise web.seeother('/')
    
    def local_registration(self):    
        f = register_form()
        if not f.validates():
            return render.welcomePage(f)
        else:
            u = web.config.db.select('localusers', dict(u=f.d.email, i=f.d.id), where="email=$u or id=$i", what="id").list()
            if len(u) is not 0:
                f.note = "There's already an account for your email address or identifier"
                return render.welcomePage(f)

            pwhash = hashlib.sha256(web.config.salt + f.d.password).hexdigest()
            web.config.db.insert('localusers', id=f.d.id, name=f.d.name, email=f.d.email, password=pwhash)

            u = web.config.db.select('localusers', where="rowid=last_insert_rowid()", what="id, name").list()
            web.config.session.loggedin = True
            web.config.session.userid = u[0].id
            web.config.session.userfullname = u[0].name
            raise web.seeother('/')
