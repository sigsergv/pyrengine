export FLASK_APP := pyrengine
export FLASK_ENV := development
export PYRENGINE_SETTINGS := $(realpath ./development.cfg)
export FLASK_DEBUG := 1
export FLASK_RUN_EXTRA_FILES := $(FLASK_APP)/translations/en/LC_MESSAGES/messages.mo:$(FLASK_APP)/translations/ru/LC_MESSAGES/messages.mo

default:
	@echo "All commands: run, babel-collect, babel-compile"

run:
	flask run 

flask-shell:
	flask shell

babel-collect:
	pybabel extract -F babel.cfg -o $(FLASK_APP)/translations/messages.pot $(FLASK_APP)
	pybabel update -i $(FLASK_APP)/translations/messages.pot -d $(FLASK_APP)/translations

babel-compile:
	pybabel compile -d $(FLASK_APP)/translations

clean-init-db:
	rm -rf migrations
	flask db init
	flask db migrate -m "Initial migration."
	flask db upgrade
	flask init-db

.PHONY: run babel-collect babel-compile flask-shell
