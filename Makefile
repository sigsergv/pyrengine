export FLASK_APP := app
export FLASK_ENV := development
export PYRENGINE_SETTINGS := $(realpath examples/development.cfg)
export FLASK_DEBUG := 1
export FLASK_RUN_EXTRA_FILES := app/translations/en/LC_MESSAGES/messages.mo:app/translations/ru/LC_MESSAGES/messages.mo

default:
	@echo "All commands: run, babel-collect, babel-compile"

run:
	flask run 

flask-shell:
	flask shell

babel-collect:
	pybabel extract -F babel.cfg -o app/translations/messages.pot app
	pybabel update -i app/translations/messages.pot -d app/translations

babel-compile:
	pybabel compile -d app/translations

clean-init-db:
	rm -rf migrations
	flask db init
	flask db migrate -m "Initial migration."
	flask db upgrade
	flask init-db

.PHONY: run babel-collect babel-compile flask-shell
