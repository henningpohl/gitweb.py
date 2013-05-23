import os
import sqlite3

def create_database(dbname):
    if os.path.exists('schema.sql') == False:
        print "Can't find schema.sql, aborting"
        return

    script = open('schema.sql', 'r').read()
    
    if os.path.exists('data.s3db'):
        print "Database already exists, overwrite? (y/n)"
        answer = raw_input('')
        if answer != 'y':
            print "Aborting"
            return

    con = sqlite3.connect('data.s3db')
    cur = con.cursor()
    cur.executescript(script)
    con.close()


if __name__ == '__main__':
    create_database('data.s3db')
