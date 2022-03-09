## OVERVIEW
The oTherm project aims to lower the cost and complexity of conducting monitoring and verification (M&V) studies of renewable thermal technologies deployed for the heating and cooling of buildings.   The project consists of three main components:  (1) a web-based application that serves as the primary data management tool (2) a separate set of Python scripts for accessing and analyzing data, using ground source heat pump as an example technology, and (3) a set of [Best Practices](https://unh.box.com/s/v6ru037omhz54obywmk4apkzk1jsvu14) documents that guide practioners on establising a monitoring and verification program to meet their specific needs.   By standardizing the data collection and documentation of individual M&V projects, there is a greater ability to share data between projects that would collectively improve the rate at which clean heating and cooling technologies are adopted and deployed. 

This documentation focuses on the deployment of web-application for an *othermsite* that would be used by an individual M&V program. The web-application is written in Django/Python with ___ java libraries.   The application requires two backend databases: (1) a PostgreSQL database for the Django models, and (2) an InfluxDB database for the time series monitoring data.  

The web-application provides a frontend browser-based interface for users to input data through individual forms and uploading files.  A full set of APIs provide the user with easy access to the data.  Example Python scripts are provided ([oTherm_GSHP](https://github.com/otherm/gshp-analysis)) to illustrate how those APIs can be incorporated in a data analyses.

## USAGE
The application is deployed using Docker.  

### Local testing and development with Docker
1. Install Docker on host machine
2. Clone repository into a local directory
3. Build the container image and run locally 

```$docker-compose -f docker-compose.dev.yml up --build  web```

4. To stop the container, Cntl-C to stop application, then:

```$docker-compose -f docker-compose.dev.yml down```

### Django migrations

1. Build the container image and run locall, but in detached mode

``` $docker-compose -f docker-compose.dev.yml up --build  --detach web ```

2. Find container id of `web` image

``` $docker ps -a ```

3. Open shell in virtual environment
```docker exec -t -i [container id] bash```

4. Run and apply migrations

```#pipenv run python ./manage.py makemigrations```

```#pipenv run python ./manage.py migrate```

## DEPLOYMENT

Instructions for deploying on a server:
    InfluxDB 
    NginX
    etc. 



