#!/usr/bin/env python3
# ~*~ coding: utf-8 ~*~
import requests
from requests import HTTPError
from datetime import time
import pandas as pd
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError
import os


# Gets the data at the specified url and returns it in JSON format
def get_data(url, source, id):
    print(f"\nPolling {source} [{id}]: {url}")
    try:
        # Attempt to query the data three times
        for i in range(3):
            try:
                # Get the response from the specified url
                response = requests.get(url)
                break
            except:
                # wait before retrying
                time.sleep(3)

        # Raise an error if there is a problem with the response
        response.raise_for_status()

        # Get the json response
        data = response.json()
        return data
    except HTTPError as http_err:
        print(http_err)


def test_mydb(client, data, site):
    # Switch to the correct database
    client.switch_database('otherm')
    try:
        # Fields read from the file

        temp_c = round(data['properties']['temperature']['value'], 2)
        pres_kpa = round(data['properties']['barometricPressure']['value'], 2) / 1000
        humi_per = round(data['properties']['relativeHumidity']['value'], 2)
        time = data['properties']['timestamp']

        print(f"temp_c: {temp_c}, pres_kpa: {pres_kpa}, humi_per: {humi_per}")
        formatted_data = [
            {
                "measurement": site,
                "fields": {
                    "temperature_c": temp_c,
                    "pressure_kpa": pres_kpa,
                    "humidity_percent": humi_per,
                },
                "time": time
            }
        ]
        try:
            print(f"writing points to influx")
            client.write_points(formatted_data)
            print(f"write succeeded")
        except InfluxDBClientError as e:
            print(e)
    except:
        print("error")


def main():
    # File containing the station ids for the sites we would like to poll
    sites = pd.read_csv('./NWS_stations.csv', header=0)

    # Iterate through the stations and grab the JSON data
    for index, row in sites.iterrows():
        station_id = row['code']
        # Build the url for the request and then create the directory name
        nws_url = "https://api.weather.gov/stations/" + station_id + "/observations/latest?require_qc=true"

        # Get the data from the national weather service and write it to a file
        data = get_data(nws_url, "NWS", station_id)
        client = InfluxDBClient(host='influxdb', port=8086, username=os.environ.get('INFLUXDB_ADMIN_USER'), password=os.environ.get('INFLUXDB_ADMIN_PASSWORD'))
        test_mydb(client, data, station_id)


if __name__ == "__main__":
    main()
    pass
