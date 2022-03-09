from influxdb import InfluxDBClient


def main():
    client = InfluxDBClient(host='influxdb', port=8086)
    print(client.get_list_database())
    results = client.query(
        'SELECT "temperature_c", "rel_humidity", "time" FROM "weather"."autogen"."weather" GROUP BY "site"')
    points = results.get_points(tags={'site': 'K12N'})
    for point in points:
        print("Humidity Percentage: %0.2f, Temperature in C: %0.2f at %s" % (
            point['rel_humidity'], point['temperature_c'], point['time']))
    pass


if __name__ == "__main__":
    main()
    pass
