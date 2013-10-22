PRAGMA foreign_keys = ON;

DROP VIEW IF EXISTS users;
DROP VIEW IF EXISTS repo_access;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS repo_users;
DROP TABLE IF EXISTS repositories;
DROP TABLE IF EXISTS project_users;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS ldapusers;
DROP TABLE IF EXISTS localusers;
DROP TABLE IF EXISTS owners;

CREATE TABLE IF NOT EXISTS owners (
	id NVARCHAR(255)  NOT NULL CHECK(length(id) > 2) PRIMARY KEY,
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
