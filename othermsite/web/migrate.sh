#!/usr/bin/env bash

pipenv run python ./manage.py makemigrations
pipenv run python ./manage.py migrate
