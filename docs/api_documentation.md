# oTherm API Documentation

The primary method to access data in an oTherm instance is through a set of APIs.  The recommended usage is to use them from a python script.  For example,
```python
import requests

site_name = '03824'
site_url = "http://[otherm_instance_url]/api/site/?name=%s" % (site_name)
site_response = requests.get(site_url, auth=([username], [password]))

site_dict = site_url.json()[0]

```

## Site Endpoint
| API Endpoint | 
| -------------------------------------- |  
|/api/equipment_data/|

### Query Parameters
| Query string parameter | Required/optional | Description | Type |
| ----------------------- | ---------------| ------------ | -------- |
| site | Required | Site id | int |

### Response
```json
[{"id":1,
  "name":"Keene NH",
  "description":"Single family residence",
  "city":"Keene",
  "zip_code":"03455",
  "application":"New construction",
  "uuid":"0483e71e-974c-4ea6-8096-640c2ed9c44a",
  "state":"New Hampshire",
  "timezone":"US/Eastern",
  "thermal_load":"adcedbf2-4a11-4f4d-890a-64c7430092f7",
  "weather_station_nws_id":"KPSM"}
]
```
## Equipment Endpoint
| API Endpoint | 
| ------------------|  
|/api/equipment/|

### Query Parameters
| Query string parameter | Required/optional | Description | Type |
| ----------------------- | ---------------| ------------ | -------- |
| site | Required | Site id | int |

### Response
```json
[{id:3,
  uuid:"a5521cc6-825b-450b-a487-637b002777ea",
  model:"HXT048",
  description:"GES install 45",
  type:2,
  site:2,
  manufacturer:3,
  no_flowmeter_flowrate:null,
  maintenance:3,
  maintenance_history:{
      id:3,
      name:"Commissioning",
      service_date:"2016-01-03",
      description:"On site commissioning and  verification of monitoring system",
      contractor:"ABC geo",
      technician:"jmd",
      equip_id:3}
}]
```

## Equipment Data Endpoint
| API Endpoint | 
 --------------  
|/api/equipment/|



### Query Parameters
| Query string parameter | Required/optional | Description | Type |
| ----------------------- | ---------------| ------------ | -------- |
| site | Required | Site id | int |
| start_date | Optional | Start date of records to retrieve in format `YYYY-MM-DD` | string |
| end_date | Optional | End of record to retrieve, in format `YYYY-MM-DD` | string |

### Response
```json
 [{id:5,
  uuid:"5406f27f-5b03-4435-b705-fbdd3e814696",
  model:"HXT048",
  description:"",
  type:2,
  site:3,
  manufacturer:3,
  heat_pump_metrics:[
    {time:"2016-01-01T00:00:18Z",
       equipment:"5406f27f-5b03-4435-b705-fbdd3e814696",
       heat_flow_rate :null,
       heatpump_aux:0.0,
       heatpump_power:null,
       outdoor_temperature:3.0,
       source_returntemp:null,
       source_supplytemp:10.187292008993,
       sourcefluid_flowrate:9.0},
    {time:"2016-01-01T00:35:54Z",
       equipment:"5406f27f-5b03-4435-b705-fbdd3e814696",
       heat_flow_rate:17105.2249418171,
       heatpump_aux:0.0,
       heatpump_power:1359.6,
       outdoor_temperature:3.0,
       source_returntemp:6.5596691201413,
       source_supplytemp:8.749792008993,
       sourcefluid_flowrate:9.0}]]
```

