PRAGMA foreign_keys = ON;

/* Trigger to automatically populate owner table on user creation */

CREATE TRIGGER local_user_creation BEFORE INSERT ON localusers
BEGIN
	INSERT INTO owners VALUES(NEW.id, "localuser", "none");
END;

CREATE TRIGGER ldap_user_creation BEFORE INSERT ON ldapusers
BEGIN
	INSERT INTO owners VALUES(NEW.id, "ldapuser", "ldap");
END;

/* Retain userid in owner table but mark as deleted user on user deletion */

CREATE TRIGGER local_user_deletion AFTER DELETE ON localusers
BEGIN
	UPDATE owners SET type="deleted" WHERE id=OLD.id;
END;

CREATE TRIGGER ldap_user_deletion AFTER DELETE ON localusers
BEGIN
	UPDATE owners SET type="deleted" WHERE id=OLD.id;
END;

/* Make user ids immutable */

CREATE TRIGGER local_uid_change BEFORE UPDATE ON localusers WHEN NEW.id != OLD.id
BEGIN
	SELECT RAISE(FAIL, 'can''t change user id');
END;

CREATE TRIGGER ldap_uid_change BEFORE UPDATE ON ldapusers WHEN NEW.id != OLD.id
BEGIN
	SELECT RAISE(FAIL, 'can''t change user id');
END;

/* Trigger to automatically populate owner table on project creation */

CREATE TRIGGER project_creation BEFORE INSERT ON projects
BEGIN
	INSERT INTO owners VALUES(NEW.id, "project", "none");
	INSERT INTO project_users VALUES(NEW.id, NEW.owner, "admin");
END;

/* Trigger to make repository owners automatically admins */

CREATE TRIGGER repository_creation AFTER INSERT ON repositories 
BEGIN 
	INSERT INTO repo_users VALUES(NEW.id, NEW.owner, NEW.owner, "admin");
END;

/* Make project ids immutable */

CREATE TRIGGER pid_change BEFORE UPDATE ON projects WHEN NEW.id != OLD.id
BEGIN
	SELECT RAISE(FAIL, 'can''t change projects id');
END;

/* Prevent deletion of owners */

CREATE TRIGGER owner_protect BEFORE DELETE ON owners
BEGIN
	SELECT RAISE(FAIL, 'can''t delete owners');
END;

/* Create admin account with 'password' as password */
/*
INSERT INTO localusers VALUES ("admin", "Git Admin", "admin@localhost", "64986686b737bb7d8facfa5eac88c9a6d999fc6489b4b92a9b3641eafb6aa55b");
UPDATE owners SET rights="administrator" WHERE id="admin";
*/

