import glob
import json
import threading
import timeit
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from time import strftime, gmtime

lock = threading.Lock()
timestamps = {}
actual_time = strftime("%Y-%m-%d %H-%M-%S", gmtime())


def worker(file):
    file_object = open(file, "r")
    contents = json.load(file_object)

    date_obj = datetime.strptime(contents['properties']['timestamp'], '%Y-%m-%dT%X%z')
    utc = date_obj.replace(tzinfo=timezone.utc)
    unix_timestamp = str(int(utc.timestamp())) + "000000000"

    temp_c = round(contents['properties']['temperature']['value'], 2)
    pres_kpa = round(contents['properties']['barometricPressure']['value'], 2) / 1000
    humi_per = round(contents['properties']['relativeHumidity']['value'], 2)
    site = contents['properties']['station'].rsplit('/', 1)[-1]

    with lock:
        if unix_timestamp not in timestamps:

            try:
                outfile = open("C:\\Users\\Jon\Documents\\IOL Work\\data\\output" + actual_time + ".txt", "a")
                outfile.write('weather'
                              + ',site=' + str(site)
                              + ' temperature_c=' + str(temp_c)
                              + ',pressure_kpa=' + str(pres_kpa)
                              + ',humidity_percent=' + str(humi_per)
                              + ' ' + str(unix_timestamp) + '\n')
                timestamps[unix_timestamp] = 1
            except:
                print("Write failed")


def main():
    print("This program converts one or many json files to InfluxDB Line Protocol")

    user_input = input("Enter the directory or single json file to convert: \n")

    if '.json' in user_input:
        try:
            file_object = open(user_input, "r")
            print(f"Converting {user_input} to line protocol")
            contents = json.load(file_object)
            print(contents)
            print(contents['properties']['timestamp'])

        except IOError:
            print(f"Couldn't open {user_input}")
    else:
        print(f"Converting files in directory {user_input} to line protocol")
        files = glob.glob(user_input + '/*.json')
        start = timeit.default_timer()
        with ThreadPoolExecutor(16) as executor:
            results = executor.map(worker, files)
        stop = timeit.default_timer()
        print('Time: ', stop - start)


if __name__ == "__main__":
    main()
