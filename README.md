# Spectrum Backend

## Git and Heroku set up

Download the [Heroku Toolbelt](https://devcenter.heroku.com/articles/heroku-cli#download-and-install). Then `heroku login` once it's all set up. Ask Jesse for Heroku access and GitHub permissions

Then, clone this repo:
```
git clone git@github.com:spectrum-app/spectrum_backend.git
```

Also add the Heroku remote:
```
git remote add heroku https://git.heroku.com/spectrum-backend.git
```

## Environment set-up (DEFAULT IF YOU AREN'T USING PYTHON THROUGH ANACONDA)
If you don't have it installed already, install Python 3 and pip.

Set up virtualenv:
```
pip install virtualenv
pip install virtualenvwrapper
```
Add the following lines to your startup file (~/.bash_profile is standard for OSX), as instructed in virtualenvwrapper installation instructions:

```
export WORKON_HOME=$HOME/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh # May be different depending on your local setup, search for virtualenvwrapper.sh
```
Finally, source your startup file so that these changes take effect immediately in your current session:

```
$ source ~/.bash_profile
```

Install requirements (need xcode toolbelt for psycopg2)
```
mkvirtualenv -p python3 spectrum_backend
add2virtualenv .
workon spectrum_backend
xcode-select --install
pip install -U pip
pip install -r requirements.txt
```

## Environment set-up (IF YOU ARE USING PYTHON THROUGH ANACONDA)
(Anaconda doesn't play nicely with virtualenv)
```
conda create -n spectrum_backend python=3.5
source activate spectrum_backend
pip install -r requirements.txt
```

## Database set-up

We are using Postgres for our local DB and remote DB.

Set up Postgres role:
```
brew install postgresql
brew services start postgresql
psql
create role spectrum with createdb login password 'seetheotherside';
create database spectrum_backend;
```

Exit out of psql, then migrate and create database:
```
python manage.py migrate
```

We also develop using the remote data, so you'll need to get into the Heroku backend. Ask Jesse for access to Heroku provisioning if you don't have access already. Once you are set up:

```
heroku pg:backups:capture
heroku pg:backups:download
```

You'll have a file called "latest.dump" in your spectrum_backend folder. Import this into your local DB with:

```
pg_restore --verbose --clean --no-acl --no-owner -h localhost -U spectrum -d spectrum_backend latest.dump
```
Delete the latest.dump file with `rm latest.dump`.


## Create super user roles (only necessary if you need to edit admin records):

```
heroku run python manage.py createsuperuser
python manage.py createsuperuser

```
You can then log in at http://spectrum-backend.herokuapp.com/admin.

## Ongoing development

## Database set-up

Migrate and create database:
```
python manage.py migrate
```

This will create and migrate your database. We use a sqlite database locally. If you need to perform a potentially destructive action while developing, you can just rename/copy the db to back it up and restore it if the action fails.

We also develop using the remote data, so you'll need to get into the Heroku backend. Create a superuser role on the backend. Ask Jesse for access to Heroku provisioning if you don't have access already.
```
heroku run python manage.py createsuperuser
python manage.py createsuperuser

```
You can then log in at http://spectrum_backend.herokuapp.com/admin.

## Ongoing development

Resume work on spectrum in new BASH instance:

```
workon spectrum_backend
```

Pull from master:
```
git fetch
git rebase origin/master
```

Install new packages as needed:
```
pip install -r requirements.txt
```

Freeze packages (if you added a new package into the virtual env):
```
pip freeze > requirements.txt
```

Please build your features on feature branches, e.g. `feature/new_bias_algorithm`. Then, push your feature branch `git push origin feature/new_bias_algorithm` and create a pull request on the GitHub repo. Your PR will be reviewed/merged from there.

## Article fetching tasks and other jobs

The following are the commands for the backend Python jobs:

- `python manage.py rss_fetcher` - This job runs every 10 minutes on Heroku to fetch the articles from the RSS feeds with records in the Feed model. Also crawls the articles.
- `scrapy crawl articles` - This is an ad-hoc job to crawl articles. Automatically runs from the rss_fetcher so generally not needed.
- `python manage.py clean_entries` - This is an ad-hoc job to clean the FeedItem entries based on changes to the data model or processing. The entry processing happens automatically with rss_fetcher so this is only necessary to clean old articles.


The following are the Celery commands for running the background jobs:

- `redis-server` (need to have Redis installed globally)
- Add ENV variable for that SPECTRUM_REDIS_URL='redis://localhost:6379'
- `celery -A spectrum_backend worker -l info` - run celery worker
- rss_fetcher job will automatically run the new associations job

KNOWN BUGS:
`RuntimeError(u'Acquire on closed pool)` is a Celery bug and can be fixed by restarting the worker with `heroku ps:scale worker=0`

If you have errors with psycopg2 let Jesse know (especially `Library not loaded: @rpath/libssl.1.0.0.dylib` or `Symbol not found: _PQbackendPID`) He's been through it all :) Specifically, make sure your version of Python matches your system architecture and try installing your virtualenv with the 32-bit version of Python.


