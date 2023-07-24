export FLASK_APP := app
export FLASK_ENV := development
export PYRENGINE_SETTINGS := $(realpath examples/development.cfg)
export FLASK_DEBUG := 1
export FLASK_RUN_EXTRA_FILES := translations/en/LC_MESSAGES/messages.mo:translations/ru/LC_MESSAGES/messages.mo

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

.PHONY: run babel-collect babel-compile flask-shell
