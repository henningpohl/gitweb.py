import hashlib
import datetime
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

    def get_rights(self, uid, config):
        return 'none'

    def get_join_date(self, uid, config):
        raise NotImplementedError

    def get_usertype(self):
        raise NotImplementedError

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
		'rights' : self.get_rights(u[0].id, config),
                'joined' : self.get_join_date(username, config)
	    }
	return False, {}
		
    def can_handle_user(self, username):
	return "@" in username

    def get_rights(self, uid, config):
	rights = config.db.select('localusers', dict(u=uid), where="id=$u", what="rights").list()
	if len(rights) == 1:
	    return rights[0]
	else:
	    return "member"

    def get_join_date(self, uid, config):
        raise NotImplementedError

    def get_usertype(self):
        return "localuser"

class LdapAuth(Auth):
    def __init__(self):
	self.name = "ldap"

    def login(self, username, password, config):
	try:
            l = ldap.initialize(config.auth.ldapserver)
            l.protocol_version = ldap.VERSION3
            user = "uid=%s,%s" % (username, config.auth.ldapbasedn)
            l.simple_bind_s(user, password)

            if config.auth.ldapusergroup is not None:
                group_membership = l.search_s(config.auth.ldapusergroup, ldap.SCOPE_BASE, "memberUid=%s" % username)
                if len(group_membership) is not 1:
                    return False, {}

            u = config.db.select('ldapusers', dict(u=username), where="username=$u", what="id, name").list()
            if len(u) is not 1: # there is no such user yet, redirect to registration
                cn = l.search_s(config.auth.ldapbasedn, ldap.SCOPE_SUBTREE, "uid=%s" % username, ["cn"])[0][1]['cn'][0]
                raise RequireRegistrationException(username, cn)

            return True, {
                'userid' : u[0].id, 
                'userfullname' : u[0].name, 
                'rights' : self.get_rights(username, config),
                'joined' : self.get_join_date(username, config)
            }
                
        except ldap.INVALID_CREDENTIALS:
            print "Invalid credentials"
        except ldap.LDAPError, error_message:
            print "LDAP error: ", error_message
        return False, {}
    def get_join_date(self, uid, config):
        raise NotImplementedError
    def can_handle_user(self, username):
	return "@" not in username

    def get_rights(self, uid, config):
        try:
            l = ldap.initialize(config.auth.ldapserver)
            l.protocol_version = ldap.VERSION3

            groupFilter = "memberUid=%s" % uid
            isAdmin = len(l.search_s(config.auth.ldapadmingroup, ldap.SCOPE_BASE, groupFilter)) >= 1
            isUser = len(l.search_s(config.auth.ldapusergroup, ldap.SCOPE_BASE, groupFilter)) >= 1

            if isAdmin:            
                return "admin"
            elif isUser:
                return "member"

        except ldap.INVALID_CREDENTIALS:
            print "Invalid credentials"
        except ldap.LDAPError, error_message:
            print "LDAP error: ", error_message
            
        return 'none'

    def get_join_date(self, uid, config):
        try:
            l = ldap.initialize(config.auth.ldapserver)
            l.protocol_version = ldap.VERSION3

            dn, timestamp = l.search_s(config.auth.ldapbasedn, ldap.SCOPE_SUBTREE, "uid=%s" % uid, ["createTimestamp"])[0]
            timestamp = "".join(c for c in timestamp["createTimestamp"][0] if c.isdigit())
            return datetime.datetime.strptime(timestamp, "%Y%m%d%H%M%S")
        except ldap.LDAPError, error_message:
            print "LDAP error: ", error_message

        return None

    def get_usertype(self):
        return "ldapuser"

