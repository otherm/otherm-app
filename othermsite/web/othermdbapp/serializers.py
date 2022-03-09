from rest_framework import serializers
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError

import os


from .models import Equipment, WeatherStation, Site, ThermalLoad, EquipmentMonitoringSystemSpec, MonitoringSystem, \
    MonitoringSystemSpec, MeasurementType, MeasurementLocation, MeasurementUnit, MeasurementSpec, Source, SiteSourceMap,\
    SourceSpec, VerticalLoopSpec, AirSourceSpec, StandingColumnSpec, OpenLoopSpec, HorizontalLoopSpec, PondSpec,\
    GhexPipeSpecifications, SourceType, Antifreeze, EquipmentSpecMap, EquipmentSpec, EquipmentType, GSHPEquipmentSpec,\
    ASHPEquipmentSpec, Model, MaintenanceHistory

class WeatherStationSerializer(serializers.ModelSerializer):

    weather_data = serializers.SerializerMethodField('get_weather_data')

    def get_weather_data(self, station):
        start_date = self.context.get("start_date") 
        end_date = self.context.get("end_date")
        
        # convert into query strings
        start_date = "" if start_date is None else f" AND time > \'{start_date}T00:00:00.000Z\'"
        end_date = "" if end_date is None else f" AND time < \'{end_date}T23:59:59.000Z\'"
        client = InfluxDBClient(host='influxdb', port=8086, username=os.environ.get('INFLUXDB_ADMIN_USER'), password=os.environ.get('INFLUXDB_ADMIN_PASSWORD'))
        # Complete query of the influx database
        fields = f'*'
        table = f'"otherm".."weather"'
        where = f'site=\'{station}\' {start_date} {end_date}'
        query = (
            f"SELECT {fields} "
            f"FROM {table} "
            f"WHERE {where} ")
        # Get the result set back from the query
        result_set = client.query(query)
        points = result_set.get_points()
        return list(points)

    class Meta:
        model = WeatherStation
        fields = [
            'nws_id', 'lat', 'lon', 'weather_data'
        ]

class ThermalLoadSerializer(serializers.ModelSerializer):

    class Meta:
        model = ThermalLoad
        fields = (
            'uuid', 'name', 'description', 'conditioned_area', 'heating_design_load',
            'cooling_design_load', 'heating_design_oat', 'cooling_design_oat',
        )

class MeasurementLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementLocation
        fields = ['name', 'description']

class MeasurementUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementUnit
        fields = ['name', 'description']

class MeasurementTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementType
        fields = ('name', 'msp_columns', 'description')

class MeasurementSpecSerializer(serializers.ModelSerializer):
    location = serializers.SerializerMethodField('get_measurement_location')
    unit = serializers.SerializerMethodField('get_measurement_unit')
    type = serializers.SerializerMethodField('get_measurement_type')

    def get_measurement_location(self, mmnt_spec):
        return MeasurementLocationSerializer(mmnt_spec.location).data

    def get_measurement_unit(self, mmnt_spec):
        return MeasurementUnitSerializer(mmnt_spec.unit).data

    def get_measurement_type(self, mmnt_spec):
        return MeasurementTypeSerializer(mmnt_spec.type).data

    class Meta:
        model = MeasurementSpec
        fields = ('name', 'description', 'type', 'accuracy', 'accuracy_pct', 'meas_bias_abs', 'meas_bias_pct',
                  'location', 'unit')

class MonSysSpecSerializer(serializers.ModelSerializer):
    measurement_spec = serializers.SerializerMethodField('get_measurement_spec')

    def get_measurement_spec(self, mon_sys_spec):
        return MeasurementSpecSerializer(mon_sys_spec.measurement_spec).data

    class Meta:
        model = MonitoringSystemSpec
        fields = ('uuid', 'measurement_spec')


class MonSysSerializer(serializers.ModelSerializer):

    monitoring_system_specs = serializers.SerializerMethodField('get_monitoring_system_specs')

    def get_monitoring_system_specs(self, monitoring_system):
        return [MonSysSpecSerializer(mss).data for mss in
                MonitoringSystemSpec.objects.filter(monitoring_system=monitoring_system)];

    class Meta:
        model = MonitoringSystem
        fields = ('id', 'name', 'description', 'manufacturer', 'monitoring_system_specs',)

class EquipmentMonitoringSystemSerializer(serializers.ModelSerializer):

    monitoring_sys_info = serializers.SerializerMethodField('get_monitoring_system_info')

    def get_monitoring_system_info(self, monitoring_system_spec):
        mon_sys_info = MonSysSerializer(monitoring_system_spec.monitoring_system_spec)
        return mon_sys_info.data

    class Meta:
        model = EquipmentMonitoringSystemSpec
        fields = ('id', 'start_date', 'end_date', 'equip_id', 'monitoring_system_spec', 'monitoring_sys_info')

class SiteSourceMapSerializer(serializers.ModelSerializer):

    # Custom fields that can be added to the serializer
    source_info = serializers.SerializerMethodField('get_source_info')

    def get_source_info(self, site_source_map):
        source_info = SourceSerializer(site_source_map.source);
        return source_info.data;

    class Meta:
        model = SiteSourceMap
        fields = ['id', 'site', 'source_id', 'name', 'source_info']

class EquipmentInfoSerializer(serializers.ModelSerializer):

    # Custom fields that can be added to the serializer
    equip_specs = serializers.SerializerMethodField('get_equipment_spec')
    equip_model_info = serializers.SerializerMethodField('get_equipment_type')

    def get_equipment_type(self, equipment_specs):
        equip_model_info = EquipmentModelSerializer(equipment_specs.model)
        return equip_model_info.data;


    def get_equipment_spec(self, equipment_spec):
        # list of EquipmentSpec subclasses (so we only have to create it once)
        equipment_spec_subclasses = EquipmentSpec.__subclasses__()
        # find the right serialzer class
        for ser in serializers.ModelSerializer.__subclasses__():
            if hasattr(ser, 'Meta') and hasattr(ser.Meta, 'model') and ser.Meta.model in equipment_spec_subclasses:
                qs = ser.Meta.model.objects.filter(equipmentspec_ptr=equipment_spec.id)
                if qs.count() > 0:
                    return ser(qs.first()).data
        return None

    class Meta:
        model = EquipmentSpec
        fields = (
            'n_stages', 'manufacturer', 'equip_model_info', 'equip_specs',
        )


class EquipmentModelSerializer(serializers.ModelSerializer):

    equipment_type = serializers.SerializerMethodField('get_equip_type')

    def get_equip_type(self, model):
        equipment_type = EquipmentTypeSerializer(model.equipment_type)
        return equipment_type.data

    class Meta:
        model = Model
        fields = '__all__'

class EquipmentTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = EquipmentType
        fields = ['name']


class GSHPEquipmentSpecSerializer(serializers.ModelSerializer):

    class Meta:
        model = GSHPEquipmentSpec
        fields = '__all__'


class ASHPEquipmentSpecSerializer(serializers.ModelSerializer):
    class Meta:
        model = ASHPEquipmentSpec
        fields = '__all__'



class SourceTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = SourceType
        fields = '__all__'

class SourceSerializer(serializers.ModelSerializer):

    source_spec_info = serializers.SerializerMethodField('get_source_spec')
    source_type = serializers.SerializerMethodField('get_source_type')

    def get_source_type(self, source):
        source_type = SourceTypeSerializer(source.type)
        return source_type.data

    def get_source_spec(self, source):
        # list of SourceSpec subclasses (so we only have to create it once)
        source_spec_subclasses = SourceSpec.__subclasses__()
        # find the right serialzer class
        for ser in serializers.ModelSerializer.__subclasses__():
            if hasattr(ser, 'Meta') and hasattr(ser.Meta, 'model') and ser.Meta.model in source_spec_subclasses:
                qs = ser.Meta.model.objects.filter(sourcespec_ptr=source.spec)
                if qs.count() > 0:
                    return ser(qs.first()).data
        return SourceSpecSerializer(source.spec).data

    class Meta:
        model = Source
        fields = ['id', 'uuid', 'name', 'description', 'spec', 'source_type', 'source_spec_info']

class SourceSpecSerializer(serializers.ModelSerializer):

    class Meta:
        model = SourceSpec
        fields = '__all__'

class AirSourceSpecSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirSourceSpec
        fields = '__all__'

class StandingColumnSpecSerializer(serializers.ModelSerializer):
    class Meta:
        model = StandingColumnSpec
        fields = '__all__'

class OpenLoopSpecSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpenLoopSpec
        fields = '__all__'

class GhexPipeSpecSerializer(serializers.ModelSerializer):
    class Meta:
        model = GhexPipeSpecifications
        fields = '__all__'

class VerticalLoopSpecSerializer(serializers.ModelSerializer):
    ghex_specs = serializers.SerializerMethodField('get_ghex_pipe_specs')
    antifreeze_info = serializers.SerializerMethodField('get_antifreeze')

    def get_ghex_pipe_specs(self, vertical_loop_spec):
        ghex_specs = GhexPipeSpecSerializer(vertical_loop_spec.ghex_pipe_spec);
        return ghex_specs.data;

    def get_antifreeze(self, horizontal_loop_spec):
        antifreeze_info = AntifreezeSerializer(horizontal_loop_spec.antifreeze);
        return antifreeze_info.data;

    class Meta:
        model = VerticalLoopSpec
        fields = ['freeze_protection', 'grout_type', 'formation_conductivity', 'formation_type', 'grout_conductivity',
                  'antifreeze_info', 'ghex_specs']

class AntifreezeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Antifreeze
        fields = '__all__'

class HorizontalLoopSpecSerializer(serializers.ModelSerializer):
    ghex_specs = serializers.SerializerMethodField('get_ghex_pipe_specs')
    antifreeze_info = serializers.SerializerMethodField('get_antifreeze')

    def get_ghex_pipe_specs(self, horizontal_loop_spec):
        ghex_specs = GhexPipeSpecSerializer(horizontal_loop_spec.ghex_pipe_spec);
        return ghex_specs.data;

    def get_antifreeze(self, horizontal_loop_spec):
        antifreeze_info = AntifreezeSerializer(horizontal_loop_spec.antifreeze);
        return antifreeze_info.data;

    class Meta:
        model = HorizontalLoopSpec
        fields = ['freeze_protection', 'trench_depth', 'orientation', 'flow_per_flowpath', 'soil_type',
                  'antifreeze_info', 'ghex_specs']

class PondSpecSerializer(serializers.ModelSerializer):
    class Meta:
        model = PondSpec
        fields = '__all__'


class MaintenanceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceHistory
        fields = '__all__'

class EquipmentSerializer(serializers.ModelSerializer):

    #Retrieve any maintenance records also
    maintenance_history = serializers.SerializerMethodField('get_maintenance')

    def get_maintenance(self, equipment):
        print(equipment.maintenance)
        maintenance_history = MaintenanceHistorySerializer(equipment.maintenance)
        return maintenance_history.data

    class Meta:
        model = Equipment
        fields = ['id', 'uuid', 'model', 'description', 'type', 'site', 'manufacturer',
                  'no_flowmeter_flowrate', 'maintenance', 'maintenance_history']

class EquipmentDataSerializer(serializers.ModelSerializer):

    # Custom fields that can be added to the serializer
    heat_pump_metrics = serializers.SerializerMethodField('get_metrics')

    def get_metrics(self, equipment):
        start_date = self.context.get("start_date")
        end_date = self.context.get("end_date")
        # convert into query strings
        start_date = "" if start_date is None else f" AND time > \'{start_date}T00:00:00.000Z\'"
        end_date = "" if end_date is None else f" AND time < \'{end_date}T23:59:59.000Z\'"

        client = InfluxDBClient(host='influxdb', port=8086, username=os.environ.get('INFLUXDB_ADMIN_USER'), password=os.environ.get('INFLUXDB_ADMIN_PASSWORD'))
        # Complete query of the influx database
        fields = f'*'
        table = f'"otherm"."autogen"."otherm-data"'
        where = f'equipment=\'{equipment.uuid}\' {start_date} {end_date}'
        query = (
            f"SELECT {fields} "
            f"FROM {table} "
            f"WHERE {where} ")
        # Get the result set back from the query
        result_set = client.query(query)
        points = result_set.get_points()

        return list(points)


    class Meta:
        model = Equipment
        fields = (
            'id', 'uuid', 'model', 'description', 'type', 'site', 'manufacturer', 'heat_pump_metrics',
        )

class SiteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Site
        fields = '__all__'

class SiteThermalLoadSerializer(serializers.ModelSerializer):

    # Custom fields that can be added to the serializer
    thermal_load = serializers.SerializerMethodField('get_thermal_load')

    def get_thermal_load(self, site):
        thermal_load = ThermalLoadSerializer(site.thermal_load);
        return thermal_load.data;

    class Meta:
        model = Site
        fields = (
            'id', 'name', 'city', 'state', 'thermal_load',
        )
