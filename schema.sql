PRAGMA foreign_keys = ON;

DROP VIEW IF EXISTS users;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS repo_users;
DROP TABLE IF EXISTS repositories;
DROP TABLE IF EXISTS project_users;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS ldapusers;
DROP TABLE IF EXISTS localusers;
DROP TABLE IF EXISTS owners;

CREATE TABLE IF NOT EXISTS owners (
	id NVARCHAR(255)  NOT NULL PRIMARY KEY,
	type VARCHAR(20)  NOT NULL,
	rights VARCHAR(20)  NOT NULL  DEFAULT 'none'
);

CREATE TABLE IF NOT EXISTS ldapusers (
	id NVARCHAR(255)  PRIMARY KEY,
	username NVARCHAR(255)  NOT NULL,
	name NVARCHAR(255)  NOT NULL,
	FOREIGN KEY (id) REFERENCES owners(id)
);

CREATE TABLE IF NOT EXISTS localusers (
	id NVARCHAR(255)  PRIMARY KEY,
	name NVARCHAR(255)  NOT NULL,
	email NVARCHAR(255)  NULL,
	password NVARCHAR(64)  NOT NULL,
	FOREIGN KEY (id) REFERENCES owners(id)
);

CREATE TABLE IF NOT EXISTS projects (
	id NVARCHAR(255)  PRIMARY KEY,
	name NVARCHAR(255)  NOT NULL,
	owner NVARCHAR(255)  NOT NULL,
	description TEXT  NULL,
	FOREIGN KEY (id) REFERENCES owners(id),
	FOREIGN KEY (owner) REFERENCES owners(id)
);

CREATE TABLE IF NOT EXISTS project_users (
	projectid NVARCHAR(255) NOT NULL,
	userid NVARCHAR(255) NOT NULL,
	role NVARCHAR(16) NOT NULL DEFAULT 'member',
	FOREIGN KEY (projectid) REFERENCES projects(id),
	FOREIGN KEY (userid) REFERENCES owners(id),
	PRIMARY KEY (projectid, userid)
);

CREATE TABLE IF NOT EXISTS repositories (
	id NVARCHAR(255)  NOT NULL,
	name NVARCHAR(255)  NOT NULL,
	owner NVARCHAR(255)  NOT NULL,
	description NULL,
	FOREIGN KEY (owner) REFERENCES owners(id),
	PRIMARY KEY (owner, id)
);

CREATE TABLE IF NOT EXISTS repo_users (
	repoid NVARCHAR(255)  NOT NULL,
	repoowner NVARCHAR(255)  NOT NULL,
	userid NVARCHAR(255)  NOT NULL,
	FOREIGN KEY (repoid, repoowner) REFERENCES repositories(id, owner),
	FOREIGN KEY (userid) REFERENCES owners(id),
	PRIMARY KEY (repoid, repoowner, userid)
);

/* http://webpy.org/cookbook/sessions */
CREATE TABLE IF NOT EXISTS sessions (
	session_id CHAR(128) UNIQUE NOT NULL,
	atime TIMESTAMP NOT NULL default current_timestamp,
	data TEXT
);

/* New view showing all users */
CREATE VIEW IF NOT EXISTS users AS
	SELECT id, type, rights, name, identifier 
	FROM owners INNER JOIN (
		SELECT id, name, email AS identifier FROM localusers
		UNION
		SELECT id, name, username AS identifier FROM ldapusers)
	USING (id);


/* Trigger to automatically populate owner table on user creation */

CREATE TRIGGER local_user_creation BEFORE INSERT ON localusers
BEGIN
	INSERT INTO owners VALUES(NEW.id, "localuser", "none");
END;

CREATE TRIGGER ldap_user_creation BEFORE INSERT ON ldapusers
BEGIN
	INSERT INTO owners VALUES(NEW.id, "ldapuser", "member");
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
INSERT INTO localusers VALUES ("admin", "Git Admin", "admin@localhost", "64986686b737bb7d8facfa5eac88c9a6d999fc6489b4b92a9b3641eafb6aa55b");
UPDATE owners SET rights="administrator" WHERE id="admin";


