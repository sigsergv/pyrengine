export FLASK_APP := app
export FLASK_ENV := development
export PYRENGINE_SETTINGS := $(realpath examples/development.cfg)
export FLASK_DEBUG := 1
export FLASK_RUN_EXTRA_FILES := translations/en/LC_MESSAGES/messages.mo:translations/ru/LC_MESSAGES/messages.mo

default:
	@echo "All commands: run, babel-collect, babel-compile"

run:
	flask run 

babel-collect:
	pybabel extract -F babel.cfg -o translations/messages.pot app
	pybabel update -i translations/messages.pot -d translations

babel-compile:
	pybabel compile -d translations

.PHONY: run babel-collect babel-compile
