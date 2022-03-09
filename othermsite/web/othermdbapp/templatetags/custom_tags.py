from django import template
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError
from ..models import Equipment, EquipmentMonitoringSystemSpec, MonitoringSystemSpec
from datetime import datetime
import pandas as pd

register = template.Library()

# -- begin hack to run daily summaries --
# TODO:  set up a command to run in cron job
from ..daily_summaries import create_daily_summaries, get_daily_summaries

@register.simple_tag
def daily_summary(site):
    qs = Equipment.objects.filter(site=site).values('uuid')
    print(qs)
    for i in range(len(qs)):
         equip_uuid = qs[i]['uuid']
         print(equip_uuid)
         df = create_daily_summaries(equip_uuid)
         return df.to_html()

# -- end hack --

# Gets the quantity of equipment at a specific site
@register.simple_tag
def equipment_quantity(site):
    quantity = Equipment.objects.filter(site=site).count()
    return quantity

# Gets the number of records for equipment at a specific site
@register.simple_tag
def monitoring_stats(site):
    stats = {}
    obj = Equipment.objects.filter(site=site).values('uuid').first()
    try:
        equip_uuid = obj['uuid']
        ds = get_daily_summaries(equip_uuid, "2016-01-01", "2016-12-31")
        stats.update({"first": ds['date'].iloc[0]})
        stats.update({"records": ds['n_records'].sum()})
        stats.update({"last": ds['date'].iloc[-1]})
        return stats
    except:
        stats.update({"first": "None"})
        stats.update({"last": "None"})
        stats.update({"records": 0})
        return stats


# Gets the type of monitoring system at the site
@register.simple_tag
def monitoring_system(site):
    qs = Equipment.objects.filter(site=site).values('id').first()
    if qs is None:
        return None
    equip = qs['id']
    monitor = EquipmentMonitoringSystemSpec.objects.filter(equip_id=equip)
    if monitor:
        mon_sys = f"{monitor[0].monitoring_system_spec}"
        return mon_sys
    return

# Gets the quantity of equipment at a specific site
@register.simple_tag
def equipment_site_name(equipment):
    return equipment.site.name

# Gets a string representing the spec for a given equipment (... means multiple, cant be shown)
@register.simple_tag
def equipmentmonitoringsystemspec_string_from_equipment(equip):
    specs = EquipmentMonitoringSystemSpec.objects.filter(equip_id=equip).filter(end_date=None)

    if specs.count() == 1:
        return specs.first()
    return "..."  

# Gets the quantity of equipment at a specific site
@register.simple_tag
def specstartdate_from_equipment(equip):
    specs = EquipmentMonitoringSystemSpec.objects.filter(equip_id=equip).filter(end_date=None)
    if specs.count() == 1:
        return specs.first().start_date
    return "..."


# Gets the quantity of equipment at a specific site
@register.simple_tag
def equipment_model_string(equipment):
    return equipment.model.__str__()

# Gets monitoring system specs for a specific monitoring system id
@register.simple_tag
def get_monitoring_system_specs(monitoring_system_id):
    monitoring_system_specs = MonitoringSystemSpec.objects.filter(monitoring_system=monitoring_system_id)
    return monitoring_system_specs
