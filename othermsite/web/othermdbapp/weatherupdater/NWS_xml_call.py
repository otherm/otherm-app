# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 12:27:58 2019

@author: jmd1
"""

import datetime
import os
import time

import pandas as pd
import urllib3
from xml.dom import minidom

from ..models import WeatherData


def getxmldata(dom, field):
    xml = dom.getElementsByTagName(field)[0].toxml()
    x = xml.replace('<' + field + '>', ' ').replace('</' + field + '>', '')
    return float(x)


def getWeatherData():
    now = datetime.datetime.utcnow()
    created = datetime.datetime.strftime(now, "%m/%d/%Y %H:%M")
    workpath = os.path.dirname(os.path.abspath(__file__))

    data = pd.read_csv(os.path.join(workpath, 'NWS_stations.csv'), header=0)

    for index, row in data.iterrows():
        wx_id = row['code']
        noaa_url = 'http://w1.weather.gov/xml/current_obs/display.php?stid='
        wxurl = noaa_url + wx_id

        for i in range(3):
            try:
                user_agent = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'}
                http = urllib3.PoolManager(headers=user_agent)
                read_str = http.request('GET', wxurl)
                break
            except:
                # wait before retrying
                time.sleep(3)
        dom = minidom.parseString(read_str.data)
        try:
            lat = getxmldata(dom, 'latitude')
            lon = getxmldata(dom, 'longitude')
        except Exception as e:
            print('Failed to get lat long from station %s:%s' % (wx_id, e))
        try:
            temp_F = getxmldata(dom, 'temp_f')
            wind_mph = getxmldata(dom, 'wind_mph')
            humid = getxmldata(dom, 'relative_humidity')
        except Exception as e:
            print('Failed to get weather data from station %s:%s' % (wx_id, e))

        # print index, wx_id, row['Name'],lat, lon
        # print(index + 1, wx_id, row['Name'], temp_F, wind_mph, humid)

        new_weather_data = WeatherData()
        now = datetime.datetime.now()

        new_weather_data.id = wx_id + now.strftime("%H:%M:%S.%f")
        new_weather_data.latitude = lat
        new_weather_data.longitude = lon
        new_weather_data.site = row['Name']
        new_weather_data.temp = temp_F
        new_weather_data.wind_speed = wind_mph
        new_weather_data.humidity = humid
        new_weather_data.save()
        print("saving...\n" + new_weather_data.site)
