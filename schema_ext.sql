PRAGMA foreign_keys = ON;

/* Trigger to automatically populate owner table on user creation */

CREATE TRIGGER local_user_creation BEFORE INSERT ON localusers
BEGIN
	INSERT INTO owners VALUES(NEW.id, "localuser");
END;

CREATE TRIGGER ldap_user_creation BEFORE INSERT ON ldapusers
BEGIN
	INSERT INTO owners VALUES(NEW.id, "ldapuser");
END;

/* Retain userid in owner table but mark as deleted user on user deletion */

CREATE TRIGGER local_user_deletion AFTER DELETE ON localusers
BEGIN
	DELETE FROM owners WHERE id=OLD.id;
END;

CREATE TRIGGER ldap_user_deletion AFTER DELETE ON ldapusers
BEGIN
	DELETE FROM owners WHERE id=OLD.id;
END;

/* Assign groups and repositories to dummy users on owner deletion */

CREATE TRIGGER owner_delete BEFORE DELETE ON owners
BEGIN
	UPDATE repositories SET owner = "dummy" WHERE owner = OLD.id;
	DELETE FROM repo_users WHERE userid = OLD.id;
	UPDATE groups SET owner = "dummy" WHERE owner = OLD.id;
	DELETE FROM group_users WHERE userid = OLD.id;
END;

/* Make user ids immutable */

CREATE TRIGGER local_uid_change BEFORE UPDATE ON localusers WHEN NEW.id != OLD.id
BEGIN
	SELECT RAISE(FAIL, "can't change user id");
END;

CREATE TRIGGER ldap_uid_change BEFORE UPDATE ON ldapusers WHEN NEW.id != OLD.id
BEGIN
	SELECT RAISE(FAIL, "can't change user id");
END;

/* Trigger to automatically populate owner table on group creation */

CREATE TRIGGER group_creation BEFORE INSERT ON groups
BEGIN
	INSERT INTO owners VALUES(NEW.id, "group");
	INSERT INTO group_users VALUES(NEW.id, NEW.owner, "admin");
END;

/* Trigger to remove deleted groups from owners table */

CREATE TRIGGER group_deletion AFTER DELETE ON groups
BEGIN
	DELETE FROM group_users WHERE groupid = OLD.id;
	DELETE FROM owners WHERE id = OLD.id;
END;

/* Trigger to make repository owners automatically admins */

CREATE TRIGGER repository_creation AFTER INSERT ON repositories 
BEGIN 
	INSERT INTO repo_users VALUES(NEW.id, NEW.owner, NEW.owner, "admin");
END;

/* Trigger to ensure all repository users are removed when a repository is deleted */
CREATE TRIGGER repository_deletion BEFORE DELETE ON repositories 
BEGIN 
	DELETE FROM repo_users WHERE repoowner = OLD.owner AND repoid = OLD.id;
END;

/* Make group ids immutable */

CREATE TRIGGER gid_change BEFORE UPDATE ON groups WHEN NEW.id != OLD.id
BEGIN
	SELECT RAISE(FAIL, "can't change group id");
END;
