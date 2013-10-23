#!/usr/bin/python
import os
import shutil
from git import *
import sqlite3
import tarfile

##
## For deployment via git push, create a bare repository
## and rename this file to REPO_PATH/hooks/post-receive.
## Update SITE_DIR to the directory to deploy to.
##

def delete_old_files(path):
    rmDirs = ["code", "doc", "static", "templates"]
    rmFiles = ["*.py", "schema_base.sql", "schema_ext.sql", "auth.wsgi"]
    keepFiles = ["config.py"]

    for d in rmDirs:
        shutil.rmtree(os.path.join(path, d), True)
    for f in rmFiles:
        if '*' in f:
            _, ext = os.path.splitext(f)
            filelist = [f for f in os.listdir(path) if f.endswith(ext)]
            for f in filelist:
                if f in keepFiles:
                    continue
                try:
                    os.remove(os.path.join(path, f))
                except:
                    pass
        else:
            try:
                os.remove(os.path.join(path, f))
            except:
                pass

def checkout_from_repo(path):
    repo = Repo(".")
    archive_file_path = os.path.join(path, "repo.tar")
    repo.archive(open(archive_file_path, 'wb'), format='tar')
    archive_file = tarfile.open(archive_file_path)
    archive_file.extractall(path)
    archive_file.close()
    os.remove(archive_file_path)

def query_db(con, statement):
    res = []
    try:
        cur = con.cursor()
        cur.execute(statement)
        res = cur.fetchall()
    except:
        pass
    finally:
        cur.close()
    return res

def update_database(path):
    base_script = open(os.path.join(SITE_DIR, 'schema_base.sql'), 'r').read()
    ext_script = open(os.path.join(SITE_DIR, 'schema_ext.sql'), 'r').read()
    con = sqlite3.connect(os.path.join(SITE_DIR, 'data.s3db'))

    with open(os.path.join(SITE_DIR, 'before_update_dump.sql'), 'w') as f:
        for line in con.iterdump():
            f.write('%s\n' % line)

    owners = query_db(con, "SELECT * FROM owners")
    ldapusers = query_db(con, "SELECT * FROM ldapusers")
    localusers = query_db(con, "SELECT * FROM localusers")
    projects = query_db(con, "SELECT * FROM projects")
    repositories = query_db(con, "SELECT * FROM repositories")
    project_users = query_db(con, "SELECT * FROM project_users")
    repo_users = query_db(con, "SELECT * FROM repo_users")

    try:
        cur = con.cursor()
        cur.executescript(base_script)
        cur.executemany("INSERT INTO owners VALUES(?, ?, ?)", owners)
        cur.executemany("INSERT INTO ldapusers VALUES(?, ?, ?)", ldapusers)
        cur.executemany("INSERT INTO localusers VALUES(?, ?, ?, ?)", localusers)
        cur.executemany("INSERT INTO projects VALUES(?, ?, ?, ?)", projects)
        cur.executemany("INSERT INTO repositories VALUES(?, ?, ?, ?, ?)", repositories)
        cur.executemany("INSERT INTO project_users VALUES(?, ?, ?)", project_users)
        cur.executemany("INSERT INTO repo_users VALUES(?, ?, ?, ?)", repo_users)
        cur.executescript(ext_script)
    except:
        print "Could not create database"
        raise
    finally:
        con.close()

if __name__ == '__main__':
    SITE_DIR = "../gitweb.py_Test_Deployment/"
    if os.path.exists(SITE_DIR) == False:
        os.mkdir(SITE_DIR)
    
    delete_old_files(SITE_DIR)
    checkout_from_repo(SITE_DIR)
    update_database(SITE_DIR)

