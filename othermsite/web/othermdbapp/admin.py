import csv
import time

from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import path

from .forms import AdminMeasurementSpecForm
from .models import Equipment, State, Tzone
from .models import EquipmentMonitoringSystemSpec, MeasurementSpec, MeasurementType
from .models import EquipmentType
from .models import Manufacturer
from .models import MeasurementLocation
from .models import MeasurementUnit
from .models import Model
from .models import MonitoringSystem
from .models import MonitoringSystemSpec
from .models import Site
from .models import WeatherData
from .models import WeatherStation
from .models import SiteSourceMap
from .models import Source
from .models import SourceType
from .models import SourceSpec
from .models import AirSourceSpec
from .models import OpenLoopSpec
from .models import HorizontalLoopSpec
from .models import VerticalLoopSpec
from .models import EquipmentSpec
from .models import GSHPEquipmentSpec
from .models import ASHPEquipmentSpec
from .models import EquipmentSpecMap
from .models import GhexPipeSpecifications
from .models import Antifreeze
from .models import MaintenanceHistory
from .models import PondSpec
from .models import ThermalLoad

# Set basic attributes for the entire admin site
admin.site.site_title = "oTherm Administration"
admin.site.site_header = "oTherm Administration"


# Changes in the list display and filters on the admin site are defined below
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['site', 'name', 'model', 'uuid', 'get_monitoring_system', 'get_start_date', 'get_end_date']
    list_filter = ('type', 'site')

    # Gets the monitoring system for this equipment
    def get_monitoring_system(self, equipment):
        qs = EquipmentMonitoringSystemSpec.objects.filter(equip_id=equipment)
        qs_count = qs.count()
        str1 = ""
        for i in range(qs_count):
            if (i + 1) >= qs_count:
                str1 += f"{qs[i].monitoring_system_spec}"
            else:
                str1 += f"{qs[i].monitoring_system_spec}, "
        return str1

    # Gets the start date of the monitoring system
    def get_start_date(self, equipment):
        qs = EquipmentMonitoringSystemSpec.objects.filter(equip_id=equipment)
        str1 = ""
        qs_count = qs.count()
        for i in range(qs_count):
            if (i + 1) >= qs_count:
                str1 += f"{qs[i].start_date}"
            else:
                str1 += f"{qs[i].start_date}, "
        return str1

    # Gets the end date of the monitoring system
    def get_end_date(self, equipment):
        qs = EquipmentMonitoringSystemSpec.objects.filter(equip_id=equipment)
        str1 = ""
        qs_count = qs.count()
        for i in range(qs_count):
            if (i + 1) >= qs_count:
                str1 += f"{qs[i].end_date}"
            else:
                str1 += f"{qs[i].end_date}, "
        return str1

    get_monitoring_system.admin_order_field = 'monitoring_system'  # Allows column order sorting
    get_monitoring_system.short_description = 'Monitoring System'  # Renames column head

    get_start_date.admin_order_field = 'start_date'  # Allows column order sorting
    get_start_date.short_description = 'Start Date'  # Renames column head

    get_end_date.admin_order_field = 'end_date'  # Allows column order sorting
    get_end_date.short_description = 'End Date'  # Renames column head


class MeasurementSpecAdmin(admin.ModelAdmin):
    form = AdminMeasurementSpecForm


class ModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'manufacturer', 'equipment_type']
    list_filter = ('manufacturer', 'equipment_type')


class EquipmentMonitoringSystemSpecAdmin(admin.ModelAdmin):
    list_display = ['equip_id', 'start_date', 'end_date']


class MonitoringSystemSpecAdmin(admin.ModelAdmin):
    # Set a custom template for the change list view
    change_list_template = 'admin/custom-monitoring-spec-change-list.html'
    change_form_template = 'admin/change-monitoring-spec-override.html'
    add_form_template = 'admin/change-monitoring-spec-override.html'

    # Overrides default changelist view
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        # Retrieve all systems in the database
        systems = MonitoringSystem.objects.all()
        specs = []
        # Get all non empty Querysets of system specs for each system
        for system in systems:
            queryset = MonitoringSystemSpec.objects.filter(monitoring_system=system)
            # Ensure the Queryset is not empty
            if queryset:
                specs.append(queryset)
        # Add all retrieved system spec Querysets to the views extra context
        extra_context['specs'] = specs
        return super().changelist_view(
            request, extra_context
        )

    # Used to append custom urls to those already included in the admin urls
    def get_urls(self):
        urls = super(MonitoringSystemSpecAdmin, self).get_urls()
        custom_urls = [
            path('export-csv/', self.export_csv, name='export-csv'),
        ]
        return custom_urls + urls

    # Supports the export csv button functionality on the admin page
    def export_csv(self, request):
        # Ensure the user is someone who should have access to this info
        if not request.user.is_staff:
            raise PermissionDenied

        queryset = MonitoringSystemSpec.objects.all()

        # Prepare timestamp for file
        named_tuple = time.localtime()
        time_string = time.strftime("%m-%d-%Y", named_tuple)

        # Format the filename for the output csv
        file_name = 'MonitoringSystemSpec' + time_string

        # Prepare the response to receive the output
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{file_name}.csv"'
        writer = csv.writer(response)

        # Generate the csv file based on the queryset received
        writer.writerow(["uuid", "monitoring system", "measurement type", "measurement spec", "measurement location"])
        for s in queryset:
            writer.writerow(
                [s.uuid, s.monitoring_system, s.measurement_type, s.measurement_spec, s.measurement_spec.location])

        return response


class MonitoringSystemAdmin(admin.ModelAdmin):
    change_form_template = 'admin/change-monitoring-system-override.html'
    add_form_template = 'admin/change-monitoring-system-override.html'

    # Define variables to be used in the following functions
    redirect_url = '/admin/othermdbapp/monitoringsystemspec/add/'
    success_message = 'Successfully saved {}. You can now add a monitoring system specification.'

    # Redirect the user to the add page if they hit the 'save and go to system spec' button
    def save_redirect(self, request, obj):
        if "_save-redirect-system-spec" in request.POST:
            obj.save()
            messages.add_message(request, messages.INFO, self.success_message.format(obj.name))
            return HttpResponseRedirect(self.redirect_url)

    def response_change(self, request, obj):
        response = self.save_redirect(request, obj)
        if response is None:
            return super().response_change(request, obj)
        # Response code 302 means 'found' and redirect is valid
        return response

    def response_add(self, request, obj):
        response = self.save_redirect(request, obj)
        # Response code 302 means 'found' and redirect is valid
        if response is None:
            return super().response_change(request, obj)
        # Response code 302 means 'found' and redirect is valid
        return response


class SiteAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'timezone', 'get_quantity', 'city', 'state', 'zip_code']
    readonly_fields = ['uuid']
    # Gets the count of equipment associated with the passed site
    def get_quantity(self, site):
        return Equipment.objects.filter(site=site).count()

    get_quantity.short_description = 'Equipment Quantity'  # Renames column head

class SourceAdmin(admin.ModelAdmin):
    readonly_fields = ['uuid']

class GSHPEquipmentSpecAdmin(admin.ModelAdmin):
    readonly_fields = ['uuid']

class ASHPEquipmentSpecAdmin(admin.ModelAdmin):
    readonly_fields = ['uuid']

class EquipmentSpecMapAdmin(admin.ModelAdmin):
    readonly_fields = ['uuid']

# Any models on the admin site are registered here
admin.site.register(Equipment, EquipmentAdmin)
admin.site.register(EquipmentType)
admin.site.register(EquipmentMonitoringSystemSpec, EquipmentMonitoringSystemSpecAdmin)
admin.site.register(Manufacturer)
admin.site.register(MonitoringSystem, MonitoringSystemAdmin)
admin.site.register(MeasurementLocation)
admin.site.register(MonitoringSystemSpec, MonitoringSystemSpecAdmin)
admin.site.register(MeasurementUnit)
admin.site.register(MeasurementSpec, MeasurementSpecAdmin)
admin.site.register(MeasurementType)
admin.site.register(Model, ModelAdmin)
admin.site.register(Site, SiteAdmin)
admin.site.register(State)
admin.site.register(Tzone)
admin.site.register(WeatherData)
admin.site.register(WeatherStation)
admin.site.register(SiteSourceMap)
admin.site.register(Source, SourceAdmin)
admin.site.register(SourceType)
admin.site.register(SourceSpec)
admin.site.register(AirSourceSpec)
admin.site.register(OpenLoopSpec)
admin.site.register(HorizontalLoopSpec)
admin.site.register(VerticalLoopSpec)
admin.site.register(PondSpec)
admin.site.register(ThermalLoad)
# Because the EquipmentSpec is subclassed by GSHP and ASHP, data should be entered in the subclasses (I think)
#admin.site.register(EquipmentSpec)
admin.site.register(GSHPEquipmentSpec, GSHPEquipmentSpecAdmin)
admin.site.register(ASHPEquipmentSpec, ASHPEquipmentSpecAdmin)
admin.site.register(EquipmentSpecMap, EquipmentSpecMapAdmin)
admin.site.register(GhexPipeSpecifications)
admin.site.register(Antifreeze)
admin.site.register(MaintenanceHistory)
