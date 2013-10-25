PRAGMA foreign_keys = ON;

DROP VIEW IF EXISTS users;
DROP VIEW IF EXISTS repo_access;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS repo_users;
DROP TABLE IF EXISTS repositories;
DROP TABLE IF EXISTS group_users;
DROP TABLE IF EXISTS groups;
DROP TABLE IF EXISTS ldapusers;
DROP TABLE IF EXISTS localusers;
DROP TABLE IF EXISTS owners;

CREATE TABLE IF NOT EXISTS owners (
	id NVARCHAR(255)  NOT NULL CHECK(length(id) > 2) PRIMARY KEY,
	type VARCHAR(20)  NOT NULL
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
	rights VARCHAR(20)  NOT NULL  DEFAULT 'none',
	FOREIGN KEY (id) REFERENCES owners(id)
);

CREATE TABLE IF NOT EXISTS groups (
	id NVARCHAR(255)  PRIMARY KEY,
	name NVARCHAR(255)  NOT NULL,
	owner NVARCHAR(255)  NOT NULL,
	description TEXT  NULL,
	FOREIGN KEY (id) REFERENCES owners(id),
	FOREIGN KEY (owner) REFERENCES owners(id)
);

CREATE TABLE IF NOT EXISTS group_users (
	groupid NVARCHAR(255) NOT NULL,
	userid NVARCHAR(255) NOT NULL,
	role NVARCHAR(16) NOT NULL DEFAULT 'member',
	FOREIGN KEY (groupid) REFERENCES groups(id),
	FOREIGN KEY (userid) REFERENCES owners(id),
	PRIMARY KEY (groupid, userid)
);

CREATE TABLE IF NOT EXISTS repositories (
	id NVARCHAR(255) NOT NULL CHECK(length(id) > 2),
	name NVARCHAR(255) NOT NULL,
	owner NVARCHAR(255) NOT NULL,
	description NULL,
	access NVARCHAR(10) NOT NULL DEFAULT 'private',
	FOREIGN KEY (owner) REFERENCES owners(id),
	PRIMARY KEY (owner, id)
);

CREATE TABLE IF NOT EXISTS repo_users (
	repoid NVARCHAR(255) NOT NULL,
	repoowner NVARCHAR(255) NOT NULL,
	userid NVARCHAR(255) NOT NULL,
	access NVARCHAR(10) NOT NULL DEFAULT 'read',
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
	SELECT id, type, name, identifier 
	FROM owners INNER JOIN (
		SELECT id, name, email AS identifier FROM localusers
		UNION
		SELECT id, name, username AS identifier FROM ldapusers)
	USING (id);

/* View aggregating all repository access rights */
CREATE VIEW IF NOT EXISTS repo_access AS
	SELECT id as userid, repoid, repoowner, access 
	FROM users INNER JOIN repo_users ON (id = userid)
	UNION
	SELECT group_users.userid AS userid, repoid, repoowner, 
	CASE WHEN group_users.role = "member" AND repo_users.access = "admin" THEN "write" ELSE repo_users.access END AS access
	FROM group_users INNER JOIN repo_users ON (groupid = repo_users.userid);
	
/* Create dummy owner to transfer repositories and groups on owner deletion */
INSERT INTO owners VALUES ("dummy", "dummy");