import pandas as pd
import numpy as np
import datetime
import os

from influxdb import DataFrameClient
from influxdb import InfluxDBClient

from .models import Site, Equipment
 
# queries the "dailysummary" InfluxDB for the daily summary data
def get_daily_summaries(equip_uuid, start_date, end_date=None):
    end_date = start_date if end_date is None else end_date
    try:
        start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return pd.DataFrame()
    dfs = pd.DataFrame()
    for day_i in range((end_dt - start_dt).days+1):
        delta_days = datetime.timedelta(1) * day_i
        day_n = start_dt + delta_days
        day_string = day_n.strftime("%Y-%m-%d")

        client = InfluxDBClient(host='influxdb', port=8086, username=os.environ.get('INFLUXDB_ADMIN_USER'), password=os.environ.get('INFLUXDB_ADMIN_PASSWORD'))
        fields = f'*'
        table = f'"dailysummaries"."autogen"."{equip_uuid}"'
        where = f"date = '{day_string}'"
        query = (
            f"SELECT {fields} "
            f"FROM {table} "
            f"WHERE {where} ")

        dfs = dfs.append(pd.DataFrame(client.query(query).get_points()), ignore_index=True)
    return dfs

# queries the "otherm" InfluxDB for the equipment data
def get_equipment_data(equipment, start_date, end_date):
    # convert into query strings
    start_date = "" if start_date is None else f" AND time > \'{start_date}T00:00:00.000Z\'"
    end_date = "" if end_date is None else f" AND time < \'{end_date}T23:59:59.000Z\'"

    client = InfluxDBClient(host='influxdb', port=8086, username=os.environ.get('INFLUXDB_ADMIN_USER'), password=os.environ.get('INFLUXDB_ADMIN_PASSWORD'))
    # Complete query of the influx database
    fields = f'*'
    table = f'"otherm"."autogen"."otherm-data"'
    where = f'equipment=\'{equipment}\' {start_date} {end_date}'
    query = (
        f"SELECT {fields} "
        f"FROM {table} "
        f"WHERE {where} ")
    print(f"querying influxdb:\n\t{query}")
    
    return pd.DataFrame(client.query(query).get_points())


# create the daily summary for the given DataFrame (typically `get_equipment_data` return value),
#   and optionally save to InfluxDB
def create_daily_summaries(equip_uuid, start_date, end_date, dry_run=False):
    heatpump_threshold_watts = 500    # watts
    data = get_equipment_data(equip_uuid, start_date, end_date)
    data.set_index(pd.to_datetime(data['time']), inplace=True)
    data['time_elapsed'] = data.index.to_series().diff().dt.seconds.div(3600, fill_value=0)

    #TODO:  otherm:  move weather data to line-protocol file and upload to otherm db
    #then join weather data with heat pump data into 'outdoor_temperature' column

    data['OAT_F'] = data['outdoor_temperature']*(9/5) + 32.

    data['cooling_degrees'] = np.where(data['OAT_F'] > 65., (data['OAT_F'] - 65) * data['time_elapsed']/24, 0.)
    data['heating_degrees'] = np.where(data['OAT_F'] < 65., (65 - data['OAT_F']) * data['time_elapsed']/24, 0.)

    data['heatpump_on'] = np.where(data['heatpump_power'] > heatpump_threshold_watts, True, False)

    data['ewt_on'] = (data['heatpump_on'] * data['source_supplytemp']).apply(lambda x: np.nan if x == 0 else x)

    data['heatpump_compressor_kwh'] = np.where(data['time_elapsed'] < 0.083,
                                      data['heatpump_power'] * data['time_elapsed'] / 1000., 0)

    if 'heatpump_aux' in data.columns:
        data['heatpump_aux_kwh'] = np.where(data['time_elapsed'] < 0.083,
                                     data['heatpump_aux'] * data['time_elapsed']/1000.,0)

    if 'sourcefluid_pump_power' in data.columns:
        data['sourcefluid_pump_kwh'] = np.where(data['time_elapsed'] < 0.083,
                                     data['sourcefluid_pump_power'] * data['time_elapsed']/1000.,0)

    data['delta_t'] = np.where(data['heatpump_on'],
                                      data['source_supplytemp'] - data['source_returntemp'], 0)

    data['heatpump_runtime'] = np.where((data['time_elapsed'] < 0.083) & (data['heatpump_on']),
                                        data['heatpump_on']*data['time_elapsed'], 0)

    if 'heat_flow_rate' not in data.columns:
        data['btus_exchanged'] = np.where((data['time_elapsed'] < 0.083) & (data['heatpump_on']),
                                          900*data['sourcefluid_flowrate']*data['delta_t']*data['time_elapsed'], 0)
    else:
        data['btus_exchanged'] = np.where((data['time_elapsed'] < 0.083) & (data['heatpump_on']),
                                          data['heat_flow_rate']*data['time_elapsed'], 0)

    data['btu_heating'] = np.where((data['heatpump_on'] & data['btus_exchanged'] > 0),
                                   3412.14 * data['heatpump_compressor_kwh'], 0)

    data['btu_cooling'] = np.where((data['heatpump_on'] & data['btus_exchanged'] < 0),
                                   3412.14 * data['heatpump_compressor_kwh'], 0)

    # Initialize data frame for computing and storing daily values
    # use np.nan as placeholder, as needed to make consistent with
    ds = pd.DataFrame()

    ds['runtime'] = data['heatpump_runtime'].resample('D').sum()
    ds['heatpump_kwh'] = data['heatpump_compressor_kwh'].resample('D').sum()
    ds['auxiliary_kwh'] = data['heatpump_aux_kwh'].resample('D').sum()
    #ds['kwh_loop_pump'] = data['loop_pump_kwh'].resample('D').sum()
    ds['total_kwh'] = ds['heatpump_kwh'] + ds['auxiliary_kwh'] #+ ds['kwh_loop_pump']

    ds['cooling_degree_days'] = data['cooling_degrees'].resample('D').sum()
    ds['heating_degree_days'] = data['heating_degrees'].resample('D').sum()
    ds['mbtus_exchanged'] = data['btus_exchanged'].resample('D').sum()/1000

    ds['mbtus_heat'] = data['btu_heating'].resample('D').sum()/1000
    ds['mbtus_cool'] = data['btu_cooling'].resample('D').sum()/1000

    ds['ewt_min'] = data['ewt_on'].resample('D').min()*(9/5)+32.
    ds['ewt_max'] = data['ewt_on'].resample('D').max()*(9/5)+32.

    ds['OAT_F'] = data['OAT_F'].resample('D').mean()
    ds['n_records'] = data['OAT_F'].resample('D').count()

    ds['date'] = ds.index.strftime("%Y-%m-%d")

    if not dry_run:
        # upload to dailysummaries InfluxDB
        client = DataFrameClient(host='influxdb', port=8086, username=os.environ.get('INFLUXDB_ADMIN_USER'), password=os.environ.get('INFLUXDB_ADMIN_PASSWORD'))
        client.write_points(ds, measurement=equip_uuid, database='dailysummaries', time_precision='h', protocol='line')

    return ds

