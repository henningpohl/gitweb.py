sudo apt-get install python-setuptools
sudo apt-get install libsasl2-dev libssl-dev libldap2-dev python-dev

sudo apt-get install sqlite3
sqlite3 -init data.s3db
sqlite data.s3db < schema.sql