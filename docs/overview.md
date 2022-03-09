# Overview
This document serves to outline the process of building, running, and interacting with the Docker containers that this project is composed of.

This project utilizes Docker Compose, which is a tool that allows for the trivial definition and management of several Docker containers simultaneously. The documentation for Docker Compose can be found [here.](https://docs.docker.com/compose/)

---

Although the usage of Docker eliminates the need to install these directly, the following libraries/frameworks are utliized in the various containers to run the project:
| Library/framework | Purpose |
| ----------- | ----------- |
| Django | The web framework used for site. (verson 2.2.6)|
| PostgreSQL | The database used for storage by the Django server. (version 13.4) |
| InfluxDB | The database used to store time-series data from the Django server. (version 1.8.6) |
| Nginx | The server that handles incoming web requests and either redirects them to the Django server, serves static resource files, or handles certificate distribution for HTTPS. |
| SchemaSpy | The application used to build interactive documentation of the PostgreSQL database schema. |

More information about which containers utilize these technologies and how can be found below (see "Containers" header).

# Running the Containers

## Prerequisites 
### Software
In order to build and run the containers via Docker Compose, the following applications must be installed:
 - Python (3.7)
 - Docker
 - Docker Compose

### Configuration
Before running the containers, some environement-specific configuration is needed.

---

Before the containers can be started, a username/password file must be configured for the various services. A template of this file can be found here: `othermsite/docker/passwords-template.env`. This file contains example declarations for the usernames and passwords for the Django, InfluxDB, and PostgreSQL instances.

The file should be modified to contain the desired login credentials and renamed to `.passwords.env`.

There is also a section to specify the secret key used for Django. Information on the purpose and usage of the secret key can be found [here.](https://docs.djangoproject.com/en/2.2/ref/settings/#secret-key.

---

The file `othermsite/docker/.env.prod` contains several environment variables that are utilized by the web :link here container. The `DJANGO_ALLOWED_HOSTS` variable needs to be set to whatever the hostname used to access the site will be. For example, if the site will be accessed by the URL `http://othermsite.mydomain/`, then `othermsite.mydomain` must be added to the `DJANGO_ALLOWED_HOSTS` variable. Multiple hosts may be specified by separating them with a space.

The documentation for this variable can be found [here](https://docs.djangoproject.com/en/2.2/ref/settings/#allowed-hosts). **However**, note that this documentation specifies the usage of this variable in Python, but this environment variable is manipulated before it's read by Python. As a result, specifying the hosts as a Python list (as the aformentioned documentation suggests) will not work. Instead, the hosts should be space-separated and without quotes.

--- 

Although optional, if HTTPS is desired, the certbot container is available and requires additional configuration. The certbot documentation can be found [here.](https://eff-certbot.readthedocs.io/en/stable/intro.html)


## Containers
The normal documentation for Docker Compose is fully applicable to this project and can be found [here.](https://docs.docker.com/compose/)

This section serves to outline each container used in this project and describes its function.

### db
The purpose of the `db` container is to host the database instance that is utilized by Django. This container simply runs a PostgreSQL database and stores all the data necessary for Django to run.

### schemaspy
The purpose of the `schemaspy` container is to generate interactive documentation outlining the schema of the Django PostgreSQL database. Accessing this documentation can be done via the path: `example-otherm-host/schemaspy`. Before accessing this URL, the schemaspy container must be brought up at least once before.

### influxdb
The purpose of the `influxdb` container is to host the database instance that is used by Django to store time series data (InfluxDB 1.8). Documentation for this InfluxDB version can be found [here.](https://docs.influxdata.com/influxdb/v1.8/) 

### web
The purpose of the `web` container is to run the Django 2.2 instance. Documentation for this Django version can be found [here.](https://docs.djangoproject.com/en/2.2/)

### nginx
The purpose of the `nginx` container is to run an nginx instance that handles the incoming requests and directs them accordingly. Documentation for nginx can be found [here.](http://nginx.org/en/docs/)

### certbot
The purpose of the `certbot` container is to generate certificates for HTTPS, if desired. Documentation on how to utilize this container can be found [here.](https://eff-certbot.readthedocs.io/en/stable/install.html#running-with-docker) Note that there is additional, host-specific configuration required for certbot to function correctly.

### weather
The purpose of the `weather` container is to populate the InfluxDB instance with weather data retrieved from api.weather.gov


# Requirements

## Prerequisites 
This project consists of several docker containers that work in conjunction and are controlled by Docker Compose. As a result, the requirements to run the containers include Python (3.7), Docker, and Docker Compose.

## Configuration
Some configuration is needed to ensure the containers function as expected.
---

###
`DJANGO_ALLOWED_HOSTS` variable...
django wont let a machine without its host name listed here run the server, so add it (space-separated, gets imported into python, link page:
https://docs.djangoproject.com/en/3.2/ref/settings/#allowed-hosts
 )



(add a note about building the containers first?)


### 
add note about also changing admin password by modifying `DJANGO_SUPERUSER_PASSWORD`, though it's optional



### Setup script
There is a script named `setup.sh` that performs a few necessary steps needed to configure/prepare Django:
`docker-compose -f docker-compose.prod.yml exec web bash /code/setup.sh`

This command only needs to be run once--it makes and applies database migrations, collects the static files, and creates an admin user (using env var DJANGO_SUPERUSER_PASSWORD)


### 


# Docker Containers
The oTherm application uses three container, one for each of: 
- Django application (2.2.6)
- PostgresQL database (13.4)
- InfluxDB database (1.8.6)


### Accessing a Docker Container shell
The command shell of a docker container can be accessed using `docker exec`.  For example, to access the shell of the influxdb container

Obtain the container id. 

`> docker ps `

    CONTAINER ID   IMAGE                   COMMAND                   ...      NAMES
    e1cac66f0809   web                     "/code/docker-init.sh"             docker_web_1
    4ae67511db6a   postgres:alpine         "docker-entrypoint.s…"             docker_db_1
    7f8de15d52d4   influxdb:1.8.6-alpine   "/entrypoint.sh infl…"             influxdb

Using the `CONTAINER ID`, access the shell.  Using the InfluxDB container id in this example:

`> docker exec -t -i 7f8de15d52d4 bash`   will result in the command prompt.

    bash-5.0#

Login to the shell using the InfluxDB administrator username and password. This will enable you to use the [InfluxDB Query Language](https://docs.influxdata.com/influxdb/v1.8/query_language/) commands, such as `SHOW DATABASES`: 


`bash-5.0# influx -username [admin-username] -password [admin-password]`

    Connected to http://localhost:8086 version 1.8.6
    InfluxDB shell version: 1.8.6
    >SHOW DATABASES

    name
    ----
    otherm
    dailysummaries
    _internal
    

When running command lines for the django app in the `web` container, it is necessary to prefix python with `pinenv run`.  For example, when running Django migrations, the command lines are:

	#pipenv run python ./manage.py makemigrations
	#pipenv run python ./manage.py migrate




