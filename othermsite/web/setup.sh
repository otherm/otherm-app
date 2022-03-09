pipenv run python manage.py makemigrations
pipenv run python manage.py migrate
pipenv run python manage.py collectstatic --no-input --clear
pipenv run python manage.py initialize-users
