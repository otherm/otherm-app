from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.forms import modelformset_factory
from influxdb import InfluxDBClient
import datetime
import os

from .models import MonitoringSystem, MeasurementSpec, Equipment, \
    EquipmentMonitoringSystemSpec, Model, Site, EquipmentType, Manufacturer, \
    ThermalLoad, Source, SourceSpec, AirSourceSpec, StandingColumnSpec, \
    OpenLoopSpec, VerticalLoopSpec, HorizontalLoopSpec, PondSpec, SiteSourceMap


# Form used to set the start date and end date of a piece of equipment
class EquipmentMonitoringSystemSpecForm(forms.ModelForm):
    site = forms.ModelChoiceField(Site.objects.none())
    
    class Meta:
        # The model which the form will pull fields from
        model = EquipmentMonitoringSystemSpec
        # this is necessary to determine field order
        fields = ('monitoring_system_spec', 'site', 'equip_id', 'start_date', 'end_date')
        labels = {
            "site": "Site",
            "equip_id": "Equipment",
            "monitoring_system_spec": "Monitoring System"
        }
        widgets = {
            'start_date': forms.TextInput(attrs={'placeholder': 'MM/DD/YYYY'}),
            'end_date': forms.TextInput(attrs={'placeholder': 'MM/DD/YYYY'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # we only want the sites that have equipment without monitoring systems
        # get a list of sites_ids that have equipment without monitoring systems
        site_ids = [s['site'] for s in Equipment.objects.filter(equipmentmonitoringsystemspec=None).values('site')]
        # now we populate our sites field with those options
        self.fields['site'].queryset = Site.objects.filter(pk__in=site_ids)
        
        self.fields['site'].required = False
        
        # Clear the fields as they are populated dependently based on previous dropdowns
        self.fields['equip_id'].queryset = Equipment.objects.all()


MeasurementSpecFormSet = modelformset_factory(MeasurementSpec, exclude=(), extra=1)

class ChangeMonitoringSystemForm(forms.ModelForm):
    class Meta:
        # The model which the form will pull fields from
        model = EquipmentMonitoringSystemSpec
        # Specify the fields to be included in the form
        # we don't need start_date, that should be now, and end_date won't be set yet
        fields = ['monitoring_system_spec', 'start_date', 'equip_id']
        widgets = {
            'start_date': forms.HiddenInput(),
            'equip_id': forms.HiddenInput()
        }

    def save(self, commit=True):
        data = super(ChangeMonitoringSystemForm, self).save(commit)

        # check if commit is true
        if commit and not(self.errors):
            # update old spec entry's end_date with today
            old_spec = EquipmentMonitoringSystemSpec.objects.get(pk=self.custom_vars['old_spec_id'])
            old_spec.end_date = data.start_date
            old_spec.save()
        return data

    def __init__(self, *args, **kwargs):
        # save the id of the old spec
        self.custom_vars = {"old_spec_id": kwargs.pop('id')}
        super().__init__(*args, **kwargs)

        self.fields['start_date'].initial = datetime.date.today()
        self.fields['equip_id'].initial = EquipmentMonitoringSystemSpec.objects.get(pk=self.custom_vars['old_spec_id']).equip_id
        self.fields['monitoring_system_spec'].queryset = MonitoringSystem.objects.all()
        self.fields['monitoring_system_spec'].label = "New Monitoring System Spec for " + self.fields['equip_id'].initial.__str__()

# Form used for the registration of new equipment that data is to be pulled from
class EquipmentRegistrationForm(forms.ModelForm):
    class Meta:
        # The model which the form will pull fields from
        model = Equipment
        # Specify the fields to be included in the form
        fields = ['type', 'manufacturer', 'model', 'site']
        # Add placeholder text for the name and hide the site input
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Name of Equipment'}),
            'site': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        # Retrieve the UUID that we saved in kwargs in the CreateView

        id = kwargs.pop('id')
        super().__init__(*args, **kwargs)
        # The types of equipment we should show is everything but monitoring systems
        self.fields['type'].queryset = EquipmentType.objects.exclude(name='Monitoring system')

        # Here we set the selection for the hidden input of site
        # This is set based on the slug we get passed in the URL
        self.fields['site'].initial = int(id)

        # Clear the manufacturer and model fields as they are populated dependently based on previous dropdowns
        self.fields['manufacturer'].queryset = Manufacturer.objects.none()
        self.fields['model'].queryset = Model.objects.none()

        # If there is a manufacturer specified, then load in the associated models
        if 'manufacturer' in self.data:
            try:
                manufacturer = int(self.data.get('manufacturer'))
                # Populate the model field with models offered by the specified manufacturer
                self.fields['model'].queryset = Model.objects.filter(manufacturer=manufacturer).order_by('id')
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty model queryset

        # If there is an equipment type specified, then load in the associated manufacturers of this equipment type
        if 'type' in self.data:
            try:
                equipment_type_id = int(self.data.get('type'))
                self.fields['manufacturer'].queryset = Manufacturer.objects.filter(
                    equipment_type_id=equipment_type_id).order_by('name')
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty equipment type queryset


# Form used to specify the name, description, location, and timezone for a new site
class SiteRegistrationForm(forms.ModelForm):
    class Meta:
        # The model which the form will pull fields from
        model = Site
        # Specify the fields to be excluded from the form
        exclude = ['uuid']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Name of Site'})
        }

# Form used to specify the name, description, location, and timezone for a new site
class ThermalLoadForm(forms.ModelForm):
    class Meta:
        # The model which the form will pull fields from
        model = ThermalLoad
        # Specify the fields to be excluded from the form
        exclude = ['uuid']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': '[Site Name] - Thermal Load'})
        }

class SourceLoadForm(forms.ModelForm):
    class Meta:
        # The model which the form will pull fields from
        model = Source
        # Specify the fields to be excluded from the form
        exclude = ['uuid']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': '[Site Name] - Source [N]'})
        }

class SiteSourceMapForm(forms.ModelForm):
    class Meta:
        # The model which the form will pull fields from
        model = SiteSourceMap
        fields = '__all__'


class SourceSpecLoadForm(forms.ModelForm):
    type = forms.ChoiceField(label="Type", choices=[("","")]+[(spec.__name__, spec.__name__) for spec in SourceSpec.__subclasses__()])

    class Meta:
        # The model which the form will pull fields from
        model = SourceSpec
        # Specify the fields to be excluded from the form
        exclude = ['uuid']

class AirSourceSpecForm(forms.ModelForm):
    class Meta:
        # The model which the form will pull fields from
        model = AirSourceSpec
        # Specify the fields to be excluded from the form
        exclude = ['uuid', 'id', 'type_id']

class StandingColumnSpecForm(forms.ModelForm):
    class Meta:
        # The model which the form will pull fields from
        model = StandingColumnSpec
        # Specify the fields to be excluded from the form
        exclude = ['uuid', 'id', 'type_id']

class OpenLoopSpecForm(forms.ModelForm):
    class Meta:
        # The model which the form will pull fields from
        model = OpenLoopSpec
        # Specify the fields to be excluded from the form
        exclude = ['uuid', 'id', 'type_id']

class VerticalLoopSpecForm(forms.ModelForm):
    class Meta:
        # The model which the form will pull fields from
        model = VerticalLoopSpec
        # Specify the fields to be excluded from the form
        exclude = ['uuid', 'id', 'type_id']

class HorizontalLoopSpecForm(forms.ModelForm):
    class Meta:
        # The model which the form will pull fields from
        model = HorizontalLoopSpec
        # Specify the fields to be excluded from the form
        exclude = ['uuid', 'id', 'type_id']

class PondSpecForm(forms.ModelForm):
    class Meta:
        # The model which the form will pull fields from
        model = PondSpec
        # Specify the fields to be excluded from the form
        exclude = ['uuid', 'id', 'type_id']

# Form used for the creation of a new monitoring system
class MeasurementSpecForm(forms.ModelForm):
    class Meta:
        # The model which the form will pull fields from
        model = MeasurementSpec
        # Specify the fields to be excluded from the form
        fields = ['name', 'type', 'accuracy', 'location']
        # Add placeholder text for the name and description fields


# Define a new form for MeasurementSpecAdmin to allow the autopopulation of the 'type' dropdown
class AdminMeasurementSpecForm(forms.ModelForm):

    # Override default init to set initial value for 'type' from kwargs
    def __init__(self, *args, **kwargs):
        super(AdminMeasurementSpecForm, self).__init__(*args, **kwargs)
        # Check that the 'initial' dictionary is present and has '_type'
        # 'initial' is only present when the add or change is a popup in admin
        if 'initial' in kwargs and '_type' in kwargs['initial']:
            # Retrieve the id for type and set the type dropdown
            measure_type = kwargs['initial']['_type']
            self.fields['type'].initial = measure_type


# Form used for the creation of a new monitoring system
class MonitoringSystemForm(forms.ModelForm):
    class Meta:
        # The model which the form will pull fields from
        model = MonitoringSystem
        # Specify the fields to be excluded from the form
        exclude = ['uuid']
        # Add placeholder text for the name and description fields
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'System Name'}),
            'description': forms.Textarea(
                attrs={'placeholder': 'A description of the system being registered'}),
        }


# Form that queries the influxdb to retrieve weather data for a specified site in the date range
class WeatherDataDisplayForm(forms.Form):
    # Define the fields to be displayed on the form
    site = forms.CharField(label="Site")
    # The added attribute makes it so that today is the last date that can be selected
    start_date = forms.DateField(label="Start Date", widget=forms.TextInput(attrs={'data-date-end-date': '0d'}))
    end_date = forms.DateField(label="End Date", widget=forms.TextInput(attrs={'data-date-end-date': '0d'}))

    # This function goes to the influxdb to retrieve the data requested
    def query_database(self):
        # After the form has been validated we access the cleaned data to work with
        site_name = self.cleaned_data.get('site').upper()
        start_date = self.cleaned_data.get('start_date')
        end_date = self.cleaned_data.get('end_date')

        # Create a place to store the data to pass back to the view to be displayed
        datapoints = []

        # Set the date as 12am on the start date and 11:59pm on the end date
        # This helps to cover the case when the start date and end date are the same
        new_start_date = start_date.strftime("%Y-%m-%d") + "T00:00:00.000Z"
        new_end_date = end_date.strftime("%Y-%m-%d") + "T23:59:59.000Z"

        # Set the influxdb we are going to query
        client = InfluxDBClient(host='influxdb', port=8086, username=os.environ.get('INFLUXDB_ADMIN_USER'), password=os.environ.get('INFLUXDB_ADMIN_PASSWORD'))

        # Define the parameters used in the query and construct the query
        fields = '"temperature_c", "humidity_percent", "pressure_kpa", "time"'
        table = '"otherm"."autogen".' + site_name
        conditions = f'time > \'{new_start_date}\'AND time < \'{new_end_date}\''
        query = (f"SELECT {fields} "
                 f"FROM {table} "
                 f"WHERE {conditions}")

        results = client.query(query)
        points = results.get_points()

        for point in points:
            datapoints.append({
                'temperature_c': point['temperature_c'],
                'humidity_percent': point['humidity_percent'],
                'pressure_kpa': point['pressure_kpa'],
                'time': point['time'],
            })
        return datapoints

class ModelUploadForm(forms.Form):
    files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))

class FileUploadForm(forms.Form):
    client = InfluxDBClient(host='influxdb', port=8086, username=os.environ.get('INFLUXDB_ADMIN_USER'), password=os.environ.get('INFLUXDB_ADMIN_PASSWORD'))
    db_list = client.get_list_database()
    DATABASES = []

    for i in range(len(db_list)):
        if db_list[i]['name'] != '_internal':
            db_tuple = (db_list[i]['name'], db_list[i]['name'])
            DATABASES.append(db_tuple)
    DATABASES = tuple(DATABASES)

    database = forms.ChoiceField(choices=DATABASES)
    influx_files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))


class TextUploadForm(forms.Form):
    client = InfluxDBClient(host='influxdb', port=8086, username=os.environ.get('INFLUXDB_ADMIN_USER'), password=os.environ.get('INFLUXDB_ADMIN_PASSWORD'))
    db_list = client.get_list_database()
    DATABASES = []
    TIME_PRECISIONS = (
        ("n", "Nanoseconds"),
        ("u", "Microseconds"),
        ("ms", "Miliseconds"),
        ("s", "Seconds")
    )

    for i in range(len(db_list)):
        if db_list[i]['name'] != '_internal':
            db_tuple = (db_list[i]['name'], db_list[i]['name'])
            DATABASES.append(db_tuple)
    DATABASES = tuple(DATABASES)

    database = forms.ChoiceField(choices=DATABASES)
    time_precision = forms.ChoiceField(choices=TIME_PRECISIONS)
    influx_text = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'cols': 40}))


# Form that queries the influxdb to retrieve weather data for a specified site in the date range
class DataDownloadForm(forms.Form):
    client = InfluxDBClient(host='influxdb', port=8086, username=os.environ.get('INFLUXDB_ADMIN_USER'), password=os.environ.get('INFLUXDB_ADMIN_PASSWORD'))
    db_list = client.get_list_database()
    client.switch_database('otherm')
    # TODO: Make the measurement a dependent dropdown
    measurement_list = client.get_list_measurements()
    DATABASES = []
    MEASUREMENTS = []

    for i in range(len(db_list)):
        if db_list[i]['name'] != '_internal':
            db_tuple = (db_list[i]['name'], db_list[i]['name'])
            DATABASES.append(db_tuple)
    DATABASES = tuple(DATABASES)

    for i in range(len(measurement_list)):
        if measurement_list[i]['name'] != '_internal':
            measurement_tuple = (measurement_list[i]['name'], measurement_list[i]['name'])
            MEASUREMENTS.append(measurement_tuple)
    MEASUREMENTS = tuple(MEASUREMENTS)

    database = forms.ChoiceField(choices=DATABASES)
    measurement = forms.ChoiceField(choices=MEASUREMENTS)

    # The added attribute makes it so that today is the last date that can be selected
    start_date = forms.DateField(label="Start Date", widget=forms.TextInput(attrs={'data-date-end-date': '0d'}))
    end_date = forms.DateField(label="End Date", widget=forms.TextInput(attrs={'data-date-end-date': '0d'}))

    # This function goes to the influxdb to retrieve the data requested
    def query_database(self):
        # After the form has been validated we access the cleaned data to work with
        database = self.cleaned_data.get('database')
      #  measurement = forms.cleaned_data.get('measurement')
        measurement = "weather"
        start_date = self.cleaned_data.get('start_date')
        end_date = self.cleaned_data.get('end_date')

        # Set the date as 12am on the start date and 11:59pm on the end date
        # This helps to cover the case when the start date and end date are the same
        new_start_date = start_date.strftime("%Y-%m-%d") + "T00:00:00.000Z"
        new_end_date = end_date.strftime("%Y-%m-%d") + "T23:59:59.000Z"

        # Set the influxdb we are going to query
        client = InfluxDBClient(host='influxdb', port=8086, username=os.environ.get('INFLUXDB_ADMIN_USER'), password=os.environ.get('INFLUXDB_ADMIN_PASSWORD'))

        # Define the parameters used in the query and construct the query
        fields = '*'
        table = f'"{database}"."autogen"."{measurement}"'
        conditions = f'time > \'{new_start_date}\'AND time < \'{new_end_date}\''
        query = (f"SELECT {fields} "
                 f"FROM {table} "
                 f"WHERE {conditions}")

        results = client.query(query)
        points = results.get_points()

        return points


class MonitoringSystemSpecForm(forms.Form):
    measurement_spec = forms.ModelMultipleChoiceField(queryset=MeasurementSpec.objects.all(),
                                                      widget=FilteredSelectMultiple("verbose name", is_stacked=True))
