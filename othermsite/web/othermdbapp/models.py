import uuid as uuid
from datetime import datetime
from django.contrib.postgres.fields import ArrayField

from django.core.validators import RegexValidator
from django.db import models


class WeatherData(models.Model):
    """Class may not be used.  _rel on field names different than influx db.  Perhaps that is intentional
       WeatherStations is below
    """
    id = models.CharField(primary_key=True, max_length=100)
    latitude = models.FloatField(default=0 )
    longitude = models.FloatField(default=0)
    reliability = models.FloatField()
    temp_rel = models.FloatField()
    wind_speed_rel = models.FloatField()
    barometric_pressure_rel = models.FloatField()
    humidity_rel = models.FloatField()
    dewpoint_rel = models.FloatField()

    class Meta:
        verbose_name_plural = 'weather data'

    def save(self, *args, **kwargs):
        if not self.id:
            self.timestamp = datetime.utcnow()
        return super(WeatherData, self).save(*args, **kwargs)

    def __str__(self):
        return '%s' % (self.site)

    def __unicode__(self):
        return u'%s' % (self.site)


class Manufacturer(models.Model):
    name = models.CharField(unique=True, max_length=20)
    description = models.TextField(blank=True, null=True)
    equipment_type = models.ForeignKey('EquipmentType', models.DO_NOTHING, db_column='type', null=True)

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        db_table = 'manufacturer'


class Model(models.Model):
    id = models.CharField(primary_key=True, max_length=50, help_text='series + capacity, e.g. NVV036')
    manufacturer = models.ForeignKey('Manufacturer', on_delete=models.CASCADE)
    equipment_type = models.ForeignKey('EquipmentType', models.DO_NOTHING, db_column='type', null=True)
    model_number = models.CharField(blank=True, null=True, max_length=50, help_text='full model number [optional]')
    def __unicode__(self):
        return u'%s' % (self.id)

    def __str__(self):
        return '%s' % (self.id)

    class Meta:
        db_table = 'model'
        verbose_name = 'Equipment model'



class Equipment(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    name = models.CharField(max_length=50, default="")
    model = models.ForeignKey('Model', on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True, help_text='optional')
    type = models.ForeignKey('EquipmentType', models.DO_NOTHING, db_column='type', null=True)
    site = models.ForeignKey('Site', models.DO_NOTHING, db_column='site', blank=True, null=True,
                             help_text='associate equipment with site')
    manufacturer = models.ForeignKey('Manufacturer', models.DO_NOTHING, db_column='manufacturer', blank=True, null=True)
    no_flowmeter_flowrate = models.FloatField(blank=True, null=True, default=None,
                                              help_text='[gpm]: fixed ground loop flow rate when no flowmeter is present')
    maintenance = models.ForeignKey('MaintenanceHistory', on_delete=models.CASCADE, null=True, default=None)

    class Meta:
        db_table = 'equipment'
        verbose_name_plural = 'equipment'

    def __unicode__(self):
        return u'%s-%s-%s' % (self.site, self.model, self.description)

    def __str__(self):
        return '%s-%s-%s' % (self.site, self.model, self.description)


class EquipmentType(models.Model):
    name = models.CharField(unique=True, max_length=20)
    description = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        db_table = 'equipment_type'


class EquipmentMonitoringSystemSpec(models.Model):
    equip_id = models.ForeignKey(Equipment, on_delete=models.SET_NULL, db_column='equip_id', blank=True, null=True)
    monitoring_system_spec = models.ForeignKey('MonitoringSystem', models.DO_NOTHING,
                                               db_column='monitoring_system_spec', blank=True, null=True)
    monitoring_system_mac_address = models.CharField(max_length=20, blank=True, null=True, default=' ')
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    def __unicode__(self):
        return u'%s' % (self.monitoring_system_spec)

    def __str__(self):
        return '%s' % (self.monitoring_system_spec)

    class Meta:
        db_table = 'equipment_monitoring_system_spec'


class MeasurementLocation(models.Model):
    name = models.CharField(unique=True, max_length=20)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'measurement_location'

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)


class MeasurementType(models.Model):
    name = models.CharField(unique=True, max_length=30)
    msp_columns = ArrayField(models.CharField(max_length=30), null=True)
    description = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        db_table = 'measurement_type'


class MeasurementUnit(models.Model):
    name = models.CharField(unique=True, max_length=10)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'measurement_unit'

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)


class MonitoringSystem(models.Model):
    name = models.CharField(unique=True, max_length=40)
    description = models.TextField(blank=True, null=True)
    manufacturer = models.ForeignKey(Manufacturer, models.DO_NOTHING, db_column='manufacturer', blank=True, null=True)

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        db_table = 'monitoring_system'


class MeasurementSpec(models.Model):
    name = models.CharField(unique=True, max_length=30)
    description = models.TextField(blank=True, null=True, help_text='for heat pump power measurements, indicate'
                                                                    'inclusion of pump and/or fan power')
    type = models.ForeignKey('MeasurementType', models.DO_NOTHING, db_column='type')
    accuracy = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)
    accuracy_pct = models.BooleanField(blank=True, null=True)
    meas_bias_abs = models.FloatField(default=0.0, help_text='measurement bias in units of measurement')
    meas_bias_pct = models.FloatField(default=0.0, help_text='measurement bias as a percent (10%) of reading')
    location = models.ForeignKey(MeasurementLocation, models.DO_NOTHING, db_column='location', blank=True, null=True)
    unit = models.ForeignKey('MeasurementUnit', models.DO_NOTHING, db_column='unit', default=None, null=True)

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        db_table = 'measurement_spec'


class MonitoringSystemSpec(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    monitoring_system = models.ForeignKey(MonitoringSystem, models.DO_NOTHING, db_column='monitoring_system',
                                          blank=True, null=True)
    measurement_type = models.ForeignKey(MeasurementType, models.DO_NOTHING, db_column='measurement_type', blank=True,
                                         null=True)
    measurement_spec = models.ForeignKey(MeasurementSpec, models.DO_NOTHING, db_column='measurement_spec', blank=True,
                                         null=True)

    def __unicode__(self):
        return u'%s-%s' % (self.monitoring_system, self.uuid)

    def __str__(self):
        return '%s-%s' % (self.monitoring_system, self.uuid)

    class Meta:
        db_table = 'monitoring_system_spec'


class Site(models.Model):
    name = models.CharField(unique=True, max_length=50, help_text='M&V program identifier')
    description = models.TextField(blank=True, null=True, help_text='optional')
    city = models.CharField(max_length=60, default='')
    state = models.ForeignKey('State', models.DO_NOTHING, db_column='state', blank=True, null=True)
    zip_code = models.CharField(max_length=9, validators=[RegexValidator(
        regex=r'^[0-9]{5}(?:-[0-9]{4})?$',
        message=u'Must be valid zipcode in formats 12345 or 12345-1234')])
    timezone = models.ForeignKey('Tzone', models.DO_NOTHING, db_column='timezone', blank=True, null=True)
    application = models.CharField(max_length=60, default='', help_text='e.g. retrofit, new construction, etc')
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    thermal_load = models.ForeignKey('ThermalLoad', models.DO_NOTHING, blank=True, null=True)
    weather_station_nws_id = models.ForeignKey('WeatherStation', models.DO_NOTHING, blank=True, null=True)

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        db_table = 'site'


class State(models.Model):
    name = models.CharField(primary_key=True, max_length=40, default='')

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        db_table = 'state'


class Tzone(models.Model):
    tzone_name = models.TextField(primary_key=True)

    def __unicode__(self):
        return u'%s' % (self.tzone_name)

    def __str__(self):
        return '%s' % (self.tzone_name)

    class Meta:
        db_table = 'tzone'

class ThermalLoad(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(unique=True, max_length=40)
    description = models.TextField(blank=True, null=True)
    conditioned_area = models.FloatField(help_text='square feet')
    heating_design_load = models.FloatField(help_text='MBtuH')
    cooling_design_load = models.FloatField(help_text='MBtuH')
    heating_design_oat = models.FloatField(help_text='Degrees F')
    cooling_design_oat = models.FloatField(help_text='Degrees F')

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        db_table = 'thermal_load'

    pass

class WeatherStation(models.Model):
    """ field for name was redundant and removed"""
    nws_id = models.CharField(primary_key=True, unique=True, max_length=30,
                              help_text='National Weather Service ID (e.g. KPSM)')
    description = models.TextField(blank=True, null=True, help_text='optional')

    lat = models.FloatField()
    lon = models.FloatField()

    def __unicode__(self):
        return u'%s' % (self.nws_id)

    def __str__(self):
        return '%s' % (self.nws_id)

    class Meta:
        db_table = 'weather_station'

    pass


class SiteSourceMap(models.Model):

    name = models.CharField(unique=True, max_length=50, default="",
                            help_text='use site name and source name, if more than source, include n')
    site = models.ForeignKey('Site', models.DO_NOTHING, db_column='site', blank=True, null=True)
    source = models.ForeignKey('Source', models.DO_NOTHING, null=True)

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        db_table = 'site_source_map'

    pass


class Source(models.Model):

    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    name = models.CharField(unique=True, max_length=50, help_text='use site_id and type, if more than one, include n')
    description = models.TextField(blank=True, null=True)
    type = models.ForeignKey('SourceType', models.DO_NOTHING, null=True)
    spec = models.ForeignKey('SourceSpec', models.DO_NOTHING, null=True)


    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        db_table = 'source'

    pass

class SourceType(models.Model):

    name = models.CharField(unique=True, max_length=50, help_text='general source type: air, ground, district, etc.')
    description = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        db_table = 'source_type'

    pass

class SourceSpec(models.Model):

    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    name = models.CharField(unique=True, max_length=50)
    description = models.TextField(blank=True, null=True)
    type = models.ForeignKey('SourceType', models.DO_NOTHING, null=True)

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        db_table = 'source_spec'

    pass


class AirSourceSpec(SourceSpec):

    compressor_location = models.CharField(max_length=25, blank=True, null=True, help_text='e.g. pad, ground, wall, roof')
    duct_configuration = models.CharField(max_length=35, blank=True, null=True, help_text='single-zone ducted, etc.')

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        db_table = 'air_source_spec'

    pass

class GhexPipeSpecifications(models.Model):

    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    name = models.CharField(unique=True, max_length=50, default="")
    dimension_ratio = models.CharField(blank=True, null=True, max_length=50, help_text='e.g. DR11')
    n_pipes_in_circuit = models.IntegerField(blank=True, null=True, help_text='for a single u-tube, enter 1')
    n_circuits = models.IntegerField(blank=True, null=True, help_text='for 2 boreholes with split flow, enter 2')
    total_pipe_length = models.FloatField(blank=True, null=True, help_text='[ft]: for single u-tube in 200ft bore, enter 400')

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        db_table = 'ghex_pipe_spec'

    pass


class StandingColumnSpec(SourceSpec):

    source_well_depth = models.FloatField(blank=True, null=True, help_text='feet')
    static_water_depth = models.FloatField(blank=True, null=True, help_text='feet')
    supply_return_separation = models.FloatField(blank=True, null=True, help_text='feet')
    shroud = models.BooleanField(blank=True, null=True)
    bleed = models.BooleanField(blank=True, null=True)
    deadband_temp = models.FloatField(blank=True, null=True, help_text='degree F')

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        db_table = 'standing_column_spec'

    pass



class OpenLoopSpec(SourceSpec):

    supply_well_depth = models.FloatField(blank=True, null=True, help_text='feet')
    static_water_depth = models.FloatField(blank=True, null=True, help_text='feet')
    return_well_depth = models.FloatField(blank=True, null=True, help_text='feet')
    supply_return_separation = models.FloatField(blank=True, null=True, help_text='feet')
    formation_type = models.CharField(max_length=50, blank=True, null=True)

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        db_table = 'open_loop_spec'

    pass

class VerticalLoopSpec(SourceSpec):

    ghex_pipe_spec = models.ForeignKey('GhexPipeSpecifications', on_delete=models.CASCADE, blank=True, null=True)
    antifreeze = models.ForeignKey('Antifreeze', on_delete=models.CASCADE, blank=True, null=True)
    freeze_protection = models.FloatField(blank=True, null=True, help_text='degree F')
    grout_conductivity = models.FloatField(blank=True, null=True, help_text='Btu/hr-ft-F')
    grout_type = models.CharField(max_length=50, blank=True, null=True)
    formation_conductivity = models.FloatField(blank=True, null=True, help_text='Btu/hr-ft-F')
    formation_type = models.CharField(max_length=50, blank=True, null=True, help_text='geologic type')

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        db_table = 'vertical_loop_spec'

    pass

class HorizontalLoopSpec(SourceSpec):

    ghex_pipe_spec = models.ForeignKey('GhexPipeSpecifications', on_delete=models.CASCADE, blank=True, null=True)
    antifreeze = models.ForeignKey('Antifreeze', on_delete=models.CASCADE, blank=True, null=True)
    freeze_protection = models.FloatField(blank=True, null=True, help_text='degree F')
    trench_depth = models.FloatField(blank=True, null=True, help_text='feet')
    orientation = models.CharField(max_length=50, blank=True, null=True, help_text='Table number from IGSHPA Table 5.16')
    flow_per_flowpath = models.FloatField(blank=True, null=True, help_text='gpm')
    soil_type = models.CharField(max_length=50, blank=True, null=True)

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        db_table = 'horizontal_loop_spec'

    pass

class PondSpec(SourceSpec):

    heat_exchanger = models.TextField(blank=True, null=True, help_text='description' )
    antifreeze = models.ForeignKey('Antifreeze', on_delete=models.CASCADE, blank=True, null=True)
    freeze_protection = models.FloatField(blank=True, null=True, help_text='degree F')

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        db_table = 'pond_spec'

    pass


class Antifreeze(models.Model):
    name = models.CharField(unique=True, max_length=20)
    description = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        db_table = 'antifreeze'

class EquipmentSpec(models.Model):

    name = models.CharField(unique=True, max_length=50)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    description = models.TextField(blank=True, null=True)
    manufacturer = models.ForeignKey('Manufacturer', on_delete=models.CASCADE)
    model = models.ForeignKey('Model', on_delete=models.CASCADE)
    n_stages = models.IntegerField(null=False, blank=False)

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        db_table = 'equipment_spec'

    pass

class MaintenanceHistory(models.Model):
    equip_id = models.ForeignKey(Equipment, on_delete=models.SET_NULL, db_column='equip_id', blank=True, null=True)
    name = models.CharField(max_length=50, blank=True, null=True)
    service_date = models.DateField(max_length=20, blank=True, null=True,)
    description = models.TextField(blank=True, null=True)
    contractor = models.CharField(max_length=50, blank=True, null=True, help_text='company name')
    technician = models.CharField(max_length=50, blank=True, null=True, help_text='lead technician initials')

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        db_table = 'maintenance'

class GSHPEquipmentSpec(EquipmentSpec):

    hc_at_32F = models.FloatField(blank=True, null=True, help_text='MBtuH')
    cc_at_77F = models.FloatField(blank=True, null=True, help_text='MBtuH')
    cop_at_20F = models.FloatField(blank=True, null=True, help_text='MBtuH')
    cop_at_30F = models.FloatField(blank=True, null=True, help_text='MBtuH')
    cop_at_40F = models.FloatField(blank=True, null=True, help_text='MBtuH')
    cop_at_50F = models.FloatField(blank=True, null=True, help_text='MBtuH')
    eer_at_60F = models.FloatField(blank=True, null=True, help_text='MBtuH')
    eer_at_70F = models.FloatField(blank=True, null=True, help_text='MBtuH')
    eer_at_80F = models.FloatField(blank=True, null=True, help_text='MBtuH')

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        db_table = 'gshp_equipment_spec'

    pass


class ASHPEquipmentSpec(EquipmentSpec):

    hc_at_5F = models.FloatField(blank=True, null=True, help_text='MBtuH')
    hc_at_17F = models.FloatField(blank=True, null=True, help_text='MBtuH')
    hc_at_47F = models.FloatField(blank=True, null=True, help_text='MBtuH')
    cc_at_82F = models.FloatField(blank=True, null=True, help_text='MBtuH')
    cc_at_95F = models.FloatField(blank=True, null=True, help_text='MBtuH')
    cop_at_5F = models.FloatField(blank=True, null=True, help_text='MBtuH')
    cop_at_17F = models.FloatField(blank=True, null=True, help_text='MBtuH')
    cop_at_47F = models.FloatField(blank=True, null=True, help_text='MBtuH')
    cop_at_82F = models.FloatField(blank=True, null=True, help_text='MBtuH')
    cop_at_95F = models.FloatField(blank=True, null=True, help_text='MBtuH')

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        db_table = 'ashp_equipment_spec'

    pass

class EquipmentSpecMap(models.Model):

    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    equipment = models.ForeignKey('Equipment', on_delete=models.CASCADE)
    equipment_spec = models.ForeignKey('EquipmentSpec', on_delete=models.CASCADE)
    source = models.ForeignKey('Source', on_delete=models.CASCADE)

    def __unicode__(self):
        return u'%s' % (self.name)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        db_table = 'equipment_spec_map'

    pass

