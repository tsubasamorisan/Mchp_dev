mchp-dev
========

Installation
------------

Clone the repository:
```
$ git clone https://github.com/mitchellias/mchp-dev
```
Install Python 3

Using homebrew:
```
$ brew install python3
```
Set up virtualenv: 

For Mac:
```
$ pyenv3.4 /mchp-dev
$ source mchp-dev/bin/activate
```
Other:
```
$ virtualenv3 ./mchp-dev
$ source mchp-dev/bin/activate
```
Install psycopg2 and postgres

For Mac:
```
$ pip install psycopg2
$ brew install postgresql
```
In the repository, install django:
```
$ pip install -r requirements.txt
```
Copy the settings_template.py to settings.py and add local changes. The dev is responsible for keeping this up to date any time it changes.

For getting AllAuth and Facebook integration working:
```
UPDATE django_site SET DOMAIN = '127.0.0.1:8000', name = 'mchp' WHERE id=2;
INSERT INTO socialaccount_socialapp (provider, name, secret, client_id, `key`)
VALUES ("facebook", "Facebook", "--put-your-own-app-secret-here--", "--put-your-own-app-id-here--", '');
INSERT INTO socialaccount_socialapp_sites (socialapp_id, site_id) VALUES (1,2);
```
And then set up the facebook side as well.

To start elasticsearch:
```
# elasticsearch -d es.config=/path/to/elasticsearch.yml
```

Amazon access id and secret key are now taken from environmental variables. Put these commands in a .bashrc or similar file to have them run every time a new shell is started. The settings file will take care about loading these.
```
export AWS_ACCESS_KEY_ID=--your-access-key--
export AWS_SECRET_ACCESS_KEY=--your-secret-key--
```

pip install django-storages leaves out S3.py, so you'll need to make the file yourself in the proper folder where (lowercase) s3.py is located. 
```
Here are the contents of that file: https://raw.githubusercontent.com/coagulant/django-storages-py3/py3/S3.py
```
