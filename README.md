# Spectrum Backend

Set up Postgres role:
```
psql
create role spectrum_backend with createdb login password 'seetheotherside';
create database spectrum_backend;
```

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

Set up working environment:
```
mkvirtualenv spectrum_backend
add2virtualenv .
pip install -r requirements.txt
```

Resume work on spectrum in new BASH instance:

```
workon spectrum_backend
```