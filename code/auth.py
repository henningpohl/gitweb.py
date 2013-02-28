import hashlib
import ldap

class RequireRegistrationException(Exception):
	def __init__(self, username, userfullname):
		self.username = username
		self.userfullname = userfullname
		
	def __str__(self):
		return "User: %s (%s)" % (self.username, self.userfullname)

class Auth(object):
	def __init__(self):
		self.name = None

	def login(self, username, password, session, config):
		raise NotImplementedError

	def can_handle_user(self, username):
		return False

	def _get_rights(self, uid, config):
		rights = config.db.select('owners', dict(u=uid), where="id=$u", what="rights").list()
		if len(rights) == 1:
			return rights[0]
		else:
			return "member"


class LocalAuth(Auth):
	def __init__(self):
		self.name = "local"
		
	def login(self, username, password, config):
		p = dict(u=username, p=hashlib.sha256(config.salt + password).hexdigest())
		u = config.db.select('localusers', p, where="email=$u and password=$p", what="id,name").list()
		if len(u) is 1:
			return True, {
				'userid' : u[0].id, 
				'userfullname' : u[0].name, 
				'rights' : self._get_rights(u[0].id, config)
			}
		return False, {}
		
	def can_handle_user(self, username):
		return "@" in username

class LdapAuth(Auth):
	def __init__(self):
		self.name = "ldap"

	def login(self, username, password, config):
		try:
			l = ldap.initialize(config.auth.ldapserver)
			l.protocol_version = ldap.VERSION3
			user = "uid=%s,%s" % (username, config.auth.ldapbasedn)
			l.simple_bind_s(user, password)

			u = config.db.select('ldapusers', dict(u=username), where="username=$u", what="id, name").list()
			if len(u) is not 1: # there is no such user yet, redirect to registration
				raise RequireRegistrationException(username, cnsearch[0][1]['gecos'][0])
			
			return True, {
				'userid' : u[0].id, 
				'userfullname' : u[0].name, 
				'rights' : self._get_rights(u[0].id, config)
			}
			
		except ldap.INVALID_CREDENTIALS:
			print "Invalid credentials"
		except ldap.LDAPError, error_message:
			print "LDAP error: ", error_message
		return False, {}

	def can_handle_user(self, username):
		return "@" not in username
