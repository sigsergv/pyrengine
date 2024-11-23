export FLASK_APP := pyrengine
export FLASK_ENV := development
export FLASK_HOST ?= 127.0.0.1
export PYRENGINE_SETTINGS := $(realpath ./development.cfg)
export FLASK_DEBUG := 1
export FLASK_RUN_EXTRA_FILES := $(FLASK_APP)/translations/en/LC_MESSAGES/messages.mo:$(FLASK_APP)/translations/ru/LC_MESSAGES/messages.mo

default:
	@echo "All commands: run, babel-collect, babel-compile"

run:
	flask run --host=$(FLASK_HOST)

flask-shell:
	flask shell

babel-collect:
	pybabel extract -F babel.cfg -o $(FLASK_APP)/translations/messages.pot $(FLASK_APP)
	pybabel update -i $(FLASK_APP)/translations/messages.pot -d $(FLASK_APP)/translations

babel-compile:
	pybabel compile -d $(FLASK_APP)/translations

init-db:
	flask db upgrade -d pyrengine/models/migrations
	flask init-db

# Don't use this recipe, it's needed only for initial project setup
#clean-init-db:
#	rm -rf pyrengine/models/migrations
#	flask db init -d pyrengine/models/migrations
#	flask db migrate -d pyrengine/models/migrations -m "Initial migration."
#	flask db upgrade -d pyrengine/models/migrations
#	flask init-db

build: babel-compile
	rm -rf dist build
	python -m build --wheel

.PHONY: run babel-collect babel-compile flask-shell build
