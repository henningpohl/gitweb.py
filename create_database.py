import os
import sqlite3

def create_database(dbname):
    if os.path.exists('schema_base.sql') == False:
        print "Can't find schema_base.sql, aborting"
        return

    if os.path.exists('schema_ext.sql') == False:
        print "Can't find schema_ext.sql, aborting"
        return

    base_script = open('schema_base.sql', 'r').read()
    ext_script = open('schema_ext.sql', 'r').read()
    
    if os.path.exists('data.s3db'):
        print "Database already exists, overwrite? (y/n)"
        answer = raw_input('')
        if answer != 'y':
            print "Aborting"
            return

    con = sqlite3.connect('data.s3db')
    cur = con.cursor()
    try:
        cur.executescript(base_script)
        cur.executescript(ext_script)
    except:
        print "Could not create database"
        raise
    finally:
        con.close()


if __name__ == '__main__':
    create_database('data.s3db')
