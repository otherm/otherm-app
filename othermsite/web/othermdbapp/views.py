from yaml.loader import SafeLoader
from .utils.model_factory import ModelFactory, ModelFactoryException
from django import template
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, FormView, ListView, DeleteView, UpdateView
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, ListModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from django.forms import ModelForm
import os
import yaml

from .forms import EquipmentRegistrationForm, MonitoringSystemForm, EquipmentMonitoringSystemSpecForm, \
    WeatherDataDisplayForm, SiteRegistrationForm, ModelUploadForm, FileUploadForm, TextUploadForm, DataDownloadForm, \
    ChangeMonitoringSystemForm, ThermalLoadForm, SourceLoadForm, SourceSpecLoadForm, AirSourceSpecForm, StandingColumnSpecForm, \
    OpenLoopSpecForm, VerticalLoopSpecForm, HorizontalLoopSpecForm, PondSpecForm, SiteSourceMapForm

from .models import MonitoringSystem, Equipment, EquipmentMonitoringSystemSpec, Manufacturer, Model, Site, \
    MonitoringSystemSpec, MeasurementSpec, WeatherStation, ThermalLoad, Source, SourceSpec, AirSourceSpec, \
    StandingColumnSpec, OpenLoopSpec, VerticalLoopSpec, HorizontalLoopSpec, PondSpec, SiteSourceMap, EquipmentSpec

from .serializers import EquipmentSerializer, WeatherStationSerializer, SiteSerializer, MonSysSerializer, \
    EquipmentMonitoringSystemSerializer, SiteSourceMapSerializer, EquipmentInfoSerializer, SiteThermalLoadSerializer, \
    EquipmentDataSerializer

from .daily_summaries import create_daily_summaries, get_daily_summaries

register = template.Library()

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        if user.groups.filter(name='otherm_user').exists():
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key})
        return Response({'msg':"Error: user is not part of the 'otherm_user' group.", 'token': None})

class DailySummariesViewSet(GenericViewSet, RetrieveModelMixin, ListModelMixin):
    serializer_class = EquipmentSerializer
    queryset = Equipment.objects.all()
    filterset_fields = ('site',)

    #def get(self, request):
    #    df = get_daily_summaries()
    #    return Response({'equipment': df.to_json)

class EquipmentViewSet(GenericViewSet, RetrieveModelMixin, ListModelMixin):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = EquipmentSerializer
    queryset = Equipment.objects.all()
    filterset_fields = ('site',)
    
    def get(self, request):
        queryset = Equipment.objects.first()
        return Response({'equipment': queryset})


class EquipmentDataViewSet(GenericViewSet, RetrieveModelMixin, ListModelMixin):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = EquipmentDataSerializer
    queryset = Equipment.objects.all()
    filterset_fields = ('site',)

    def get(self, request):
        queryset = Equipment.objects.first()
        return Response({'equipment': queryset})

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["start_date"] = self.request.query_params.get('start_date')
        context["end_date"] = self.request.query_params.get('end_date')
        return context

class SiteSourceMapViewSet(GenericViewSet, RetrieveModelMixin, ListModelMixin):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = SiteSourceMapSerializer
    queryset = SiteSourceMap.objects.all()
    filterset_fields = ('site',)

    def get(self, request):
        queryset = SiteSourceMap.objects.first()
        return Response({'site_source_map': queryset})

class SiteViewSet(GenericViewSet, RetrieveModelMixin, ListModelMixin):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = SiteSerializer
    queryset = Site.objects.all()
    filterset_fields = ('id', 'name', 'city')

class SiteThermalLoadViewSet(GenericViewSet, RetrieveModelMixin, ListModelMixin):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = SiteThermalLoadSerializer
    queryset = Site.objects.all()
    filterset_fields = ('id', 'name',)

class EquipmentMonitoringViewSet(GenericViewSet, RetrieveModelMixin, ListModelMixin):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = EquipmentMonitoringSystemSerializer
    queryset = EquipmentMonitoringSystemSpec.objects.all()
    filterset_fields = ('equip_id', )

class EquipmentModelViewSet(GenericViewSet, RetrieveModelMixin, ListModelMixin):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = EquipmentInfoSerializer
    queryset = EquipmentSpec.objects.all()
    filterset_fields = ('model', )

class WeatherStationViewSet(GenericViewSet, RetrieveModelMixin, ListModelMixin):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = WeatherStationSerializer
    queryset = WeatherStation.objects.all()
    filterset_fields = ('nws_id',)

    def get(self, request):
        queryset = WeatherStation.objects.first()
        return Response({'weather_station': queryset})

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["start_date"] = self.request.query_params.get('start_date')
        context["end_date"] = self.request.query_params.get('end_date')
        return context


class MonSysViewSet(GenericViewSet, RetrieveModelMixin, ListModelMixin):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = MonSysSerializer
    queryset = MonitoringSystem.objects.all()
    filterset_fields = ('id', 'name')


def index(request):
    return render(request, "index.html")

def sites(request):
    return render(request, "sites.html")

def site_forms(request):
    return render(request, "site-forms.html")

def admin_forms(request):
    return render(request, "admin-forms.html")

class SiteCreate(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    permission_required = 'othermdbapp.add_site'
    # The model that this view corresponds with
    model = Site
    # The form that this view will display
    form_class = SiteRegistrationForm
    # Specify the template for the view
    template_name = 'site-registration.html'
    success_url = reverse_lazy('site-registration')
    success_message = "Site Registered Successfully"

class ThermalLoadCreate(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    permission_required = 'othermdbapp.add_thermalload'
    # The model that this view corresponds with
    model = ThermalLoad
    # The form that this view will display
    form_class = ThermalLoadForm
    # Specify the template for the view
    template_name = 'thermal-load.html'
    # On a successful registration, redirect user the following
    success_url = reverse_lazy('thermal-load')
    success_message = "Information Registered Successfully"

class SiteSourceMapCreate(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    permission_required = 'othermdbapp.add_sitesourcemap'
    model = SiteSourceMap
    form_class = SiteSourceMapForm
    template_name = 'site-source-registration.html'
    success_url = reverse_lazy('site-source-registration')
    success_message = "Source Successfully Registered"

class SourceCreate(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    permission_required = 'othermdbapp.add_source'
    # The model that this view corresponds with
    model = Source
    # The form that this view will display
    form_class = SourceLoadForm
    # Specify the template for the view
    template_name = 'source-registration.html'
    # On a successful registration, redirect user the following
    success_url = reverse_lazy('source-registration')
    success_message = "Information Registered Successfully"

class SourceSpecCreate(PermissionRequiredMixin, TemplateView):
    permission_required = 'othermdbapp.add_sourcespec'
    # Specify the template for the view
    template_name = 'source-spec-registration.html'

class AirSourceSpecCreate(SuccessMessageMixin, CreateView):
    # The model that this view corresponds with
    model = AirSourceSpec
    # The form that this view will display
    form_class = AirSourceSpecForm
    # Specify the template for the view
    template_name = 'air-source-spec-form.html'
    # On a successful registration, redirect user the following
    success_url = reverse_lazy('source-spec-registration')
    success_message = "AirSourceSpec Registered Successfully"
    
    def post(self, request, *args, **kwargs):
        print("smc")
        print(self)
        form = self.form_class(request.POST)
        if not form.is_valid():
            msgs = []
            for key,val in form.errors.items():
                errs = "\n".join(val)
                msgs.append(f"Error with field \"{key}\": {errs}")
            return render(request, SourceSpecCreate.template_name, {'messages': msgs})
        return super().post(request, *args, **kwargs)


class StandingColumnSpecCreate(SuccessMessageMixin, CreateView):
    # The model that this view corresponds with
    model = StandingColumnSpec
    # The form that this view will display
    form_class = StandingColumnSpecForm
    # Specify the template for the view
    template_name = 'standing-column-spec-form.html'
    # On a successful registration, redirect user the following
    success_url = reverse_lazy('source-spec-registration')
    success_message = "StandingColumnSpec Registered Successfully"

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if not form.is_valid():
            msgs = []
            for key,val in form.errors.items():
                errs = "\n".join(val)
                msgs.append(f"Error with field \"{key}\": {errs}")
            return render(request, self.template_name, {'messages': []})
        return super().post(request, *args, **kwargs)    

class OpenLoopSpecCreate(SuccessMessageMixin, CreateView):
    # The model that this view corresponds with
    model = OpenLoopSpec
    # The form that this view will display
    form_class = OpenLoopSpecForm
    # Specify the template for the view
    template_name = 'open-loop-spec-form.html'
    # On a successful registration, redirect user the following
    success_url = reverse_lazy('source-spec-registration')
    success_message = "OpenLoopSpec Registered Successfully"

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if not form.is_valid():
            msgs = []
            for key,val in form.errors.items():
                errs = "\n".join(val)
                msgs.append(f"Error with field \"{key}\": {errs}")
            return render(request, self.template_name, {'messages': []})
        return super().post(request, *args, **kwargs)    

class VerticalLoopSpecCreate(SuccessMessageMixin, CreateView):
    # The model that this view corresponds with
    model = VerticalLoopSpec
    # The form that this view will display
    form_class = VerticalLoopSpecForm
    # Specify the template for the view
    template_name = 'vertical-loop-spec-form.html'
    # On a successful registration, redirect user the following
    success_url = reverse_lazy('source-spec-registration')
    success_message = "VerticalLoopSpec Registered Successfully"

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if not form.is_valid():
            msgs = []
            for key,val in form.errors.items():
                errs = "\n".join(val)
                msgs.append(f"Error with field \"{key}\": {errs}")
            return render(request, self.template_name, {'messages': []})
        return super().post(request, *args, **kwargs)    

class HorizontalLoopSpecCreate(SuccessMessageMixin, CreateView):
    # The model that this view corresponds with
    model = HorizontalLoopSpec
    # The form that this view will display
    form_class = HorizontalLoopSpecForm
    # Specify the template for the view
    template_name = 'horizontal-loop-spec-form.html'
    # On a successful registration, redirect user the following
    success_url = reverse_lazy('source-spec-registration')
    success_message = "HorizontalLoopSpec Registered Successfully"

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if not form.is_valid():
            msgs = []
            for key,val in form.errors.items():
                errs = "\n".join(val)
                msgs.append(f"Error with field \"{key}\": {errs}")
            return render(request, self.template_name, {'messages': []})
        return super().post(request, *args, **kwargs)    

class PondSpecCreate(SuccessMessageMixin, CreateView):
    # The model that this view corresponds with
    model = PondSpec
    # The form that this view will display
    form_class = PondSpecForm
    # Specify the template for the view
    template_name = 'pond-spec-form.html'
    # On a successful registration, redirect user the following
    success_url = reverse_lazy('source-spec-registration')
    success_message = "PondSpec Registered Successfully"

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if not form.is_valid():
            msgs = []
            for key,val in form.errors.items():
                errs = "\n".join(val)
                msgs.append(f"Error with field \"{key}\": {errs}")
            return render(request, self.template_name, {'messages': []})
        return super().post(request, *args, **kwargs)    

def ChangeMonitoringSystemSpecRedirect(request, pk):
    # check if there are multiple equipmentmonitoringsystemspec entries for this equipment
    equip = Equipment.objects.get(pk=pk)
    specs = EquipmentMonitoringSystemSpec.objects.filter(equip_id=equip).filter(end_date=None)
    # if we have more than 1
    if specs.count() != 1:
        # redirect to choice page
        return redirect("/change-monitoring-system-choice/" + str(equip.pk))
    return redirect("/change-monitoring-system/" + str(specs.first().pk))

class ChangeMonitoringSystem(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    permission_required = 'othermdbapp.add_equipmentmonitoringsystemspec'
    model = EquipmentMonitoringSystemSpec
    form_class = ChangeMonitoringSystemForm
    template_name = 'change-monitoring-system.html'
    success_url = reverse_lazy('change-monitoring-system-eq-list')

    # Called once the form is valid and takes care of saving the forms contents
    def form_valid(self, form):
        f = super().form_valid(form)
        # Get the data from the form to be worked with but don't save anything to the database
        data = form.save(commit=False)

        # Create a custom success message to be displayed to the user once they are redirected to the success_url
        success_message = f'Added {data.monitoring_system_spec.name} to {data.equip_id}'
        messages.add_message(self.request, messages.SUCCESS, success_message)
        return f

    def get_form_kwargs(self):
        kwargs = super(ChangeMonitoringSystem, self).get_form_kwargs()
        # We access the equipment's id and save it for the forms kwargs
        kwargs['id'] = self.kwargs['pk']
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get the EquipmentMonitoringSystemSpec whose end_date we'll set
        context['spec'] = EquipmentMonitoringSystemSpec.objects.get(pk=self.kwargs['pk'])
        context['equipment'] = context['spec'].equip_id
        return context

class ChangeMonitoringSystemChoice(ListView):
    model = EquipmentMonitoringSystemSpec
    template_name = 'change-monitoring-system-choice.html'
    paginate_by = 10

    def get_queryset(self):
        return EquipmentMonitoringSystemSpec.objects.filter(equip_id=self.kwargs['pk']).filter(end_date=None).order_by('start_date')

class EquipmentCreate(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    permission_required = 'othermdbapp.add_equipment'
    # The model that this view corresponds with
    model = Equipment
    # The form that this view will display
    form_class = EquipmentRegistrationForm
    # Specify the template for the view
    template_name = 'equipment-registration.html'
    success_message = ''
    # On a successful registration, redirect user the following
    success_url = reverse_lazy('site-list')

    # Called once the form is valid and takes care of saving the forms contents
    def form_valid(self, form):
        f = super().form_valid(form)
        # Get the data from the form to be worked with but don't save anything to the database
        data = form.save(commit=False)

        # Create a custom success message to be displayed to the user once they are redirected to the success_url
        success_message = f'Added {data.manufacturer} {data.model} to {data.site}'
        messages.add_message(self.request, messages.SUCCESS, success_message)
        return f

    def get_form_kwargs(self):
        kwargs = super(EquipmentCreate, self).get_form_kwargs()
        # We access the site's id and save it for the forms kwargs
        kwargs['id'] = self.kwargs['pk']
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get the site associated with the URL slug
        site = Site.objects.get(id=self.kwargs['pk'])
        # Add all equipment that is at this site to the context of the page
        context['equipment_list'] = Equipment.objects.filter(site=self.kwargs['pk']).order_by('uuid')
        context['site_name'] = site.name
        return context


class EquipmentDelete(SuccessMessageMixin, DeleteView):
    model = Equipment

    template_name = 'equipment-confirm-delete.html'
    success_url = reverse_lazy('site-list')
    success_message = "Equipment Deleted Successfully"


# View to create a new monitoring system specification
class MonitorSystemCreate(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    permission_required = 'othermdbapp.add_monitoringsystem'
    # The model that this view corresponds with
    model = MonitoringSystem
    # The form that this view will display
    form_class = MonitoringSystemForm
    # Specify the template for the view
    template_name = 'monitoring-system-registration.html'
    # On a successful creation, redirect user the following
    success_url = reverse_lazy('system-registration')

    success_message = "Monitoring System Registered Successfully"


# View to create a new monitoring system specification
class EquipmentMonitoringSystemSpecCreate(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    permission_required = 'othermdbapp.add_equipmentmonitoringsystemspec'
    # The model that this view corresponds with
    model = EquipmentMonitoringSystemSpec
    # The form that this view will display
    form_class = EquipmentMonitoringSystemSpecForm
    # Specify the template for the view
    template_name = 'add-monitoring-system.html'
    # On a successful creation, redirect user the following
    success_url = reverse_lazy('add-monitoring-system')
    success_message = "Equipment Monitoring System Specification Registered Successfully"


class WeatherFormView(FormView):
    template_name = 'weather-form.html'
    form_class = WeatherDataDisplayForm
    success_url = '/weather-form/'

    def form_valid(self, form):
        context = self.get_context_data()
        try:
            context['data'] = form.query_database()
        except:
            print("Error occurred while querying the database")
        return self.render_to_response(context)


class AuditDataView(TemplateView):
    template_name = 'audit.html'

    def get_context_data(self, *args, **kwargs):
        client = InfluxDBClient(host='influxdb', port=8086)
        # Query the database
        results = client.query(
            'SELECT "count", "percentage" FROM "weather"."autogen"."audit" WHERE time > now() - 30d AND '
            '("field"=\'properties.relativeHumidity.value\' OR "field"=\'properties.temperature.value\' '
            'OR "field"=\'properties.barometricPressure.value\' OR "field"=\'properties.dewpoint.value\''
            'OR "field"=\'properties.heatIndex.value\' OR "field"=\'properties.maxTemperatureLast24Hours.qualityControl\' '
            'OR "field"=\'properties.maxTemperatureLast24Hours.value\' OR "field"=\'properties.minTemperatureLast24Hours.qualityControl\' '
            'OR "field"=\'properties.minTemperatureLast24Hours.value\' OR "field"=\'properties.precipitationLast3Hours.value\' '
            'OR "field"=\'properties.precipitationLast6Hours.value\' OR "field"=\'properties.precipitationLastHour.value\' '
            'OR "field"=\'properties.rawMessage\' OR "field"=\'properties.seaLevelPressure.value\' '
            'OR "field"=\'properties.visibility.value\' OR "field"=\'properties.windChill.value\' '
            'OR "field"=\'properties.windDirection.value\' OR "field"=\'properties.windGust.value\' '
            'OR "field"=\'properties.windSpeed.value\')')
        # Get the data points for the site
        points = results.get_points()
        datapoints = []
        fields = ["Relative Humidity", "Temperature", "Biometric Pressure", "Dewpoint", "Heat Index",
                  "QC Max Temperature Last 24", "Value Max Temperature Last 24", "QC Min Temperature Last 24",
                  "Value Min Temperature Last 24", "Value Precipitation Last 3", "Value Precipitation Last 6",
                  "Value Precipitation Hour", "Raw Message", "Value Sea Level Pressure", "Value Visibility",
                  "Value Wind Chill", "Value Wind Direction", "Value Wind Gust", "Value Wind Speed"]
        count = 0
        # For each data point in the original points, add necessary labels and save to the datapoints list
        for point in points:
            print(count)
            print(fields[count])
            datapoints.append({
                'field': fields[count],
                'count': str(point['count']),
                'percentage': str(point['percentage']) + "%",
            })
            count += 1

        context = super(AuditDataView, self).get_context_data(*args, **kwargs)
        context['data'] = datapoints
        return context


# loads all the equipment corresponding to a site
def load_equipment_from_site(request):
    # get the site
    site = request.GET.get('site')
    # get whether or not we should exclude those with monitoring systems
    exclude_mons = request.GET.get('exclude_monitoring_systems').lower() == "true"
    # if we exclude monitoring systems
    if exclude_mons:
        equips = Equipment.objects.filter(site=site).filter(equipmentmonitoringsystemspec=None)
        return render(request, 'equipment-dropdown-options.html', {'equipment': equips})
    # if we don't
    else:
        equips = Equipment.objects.filter(site=site)
        return render(request, 'equipment-dropdown-options.html', {'equipment': equips})

def load_models(request):
    # Get the manufacturer
    manufacturer = request.GET.get('manufacturer')
    models = Model.objects.filter(manufacturer=manufacturer).order_by('id')
    # Render the model dropdown with the models that match the manufacturer
    return render(request, 'model-dropdown-list-options.html', {'models': models})

def load_source_types(request):
    # Get the manufacturer
    source_type = request.GET.get('source_type')
    models = Model.objects.filter(source_type=source_type).order_by('id')
    # Render the model dropdown with the models that match the souce type
    return render(request, 'source-type-dropdown-list-options.html', {'models': models})

@permission_required('othermdbapp.add_sourcespec')
def load_source_spec_form(request):
    spec_type = request.GET.get('spec_type')
    # find the form for this spec
    msgs,spec_form,spec_view = [], None, None
    for sub in ModelForm.__subclasses__():
        if sub._meta.model and sub._meta.model.__name__ == spec_type:
            spec_form = sub
    for sub in CreateView.__subclasses__():
        if sub.model and sub.model.__name__ == spec_type:
            spec_view = sub

    if spec_form and spec_view:
        # Render the form for this particular sourcespec type
        return render(request, spec_view.template_name, {'form': spec_form()})

    # handle errors
    if not spec_form:
        msgs.append(f"No form found for class {spec_type}")
    if not spec_view:
        msgs.append(f"No view found for class {spec_type}")
    return render(request, 'danger-message.html', {"messages": msgs})



def load_manufacturers(request):
    # Get the equipment type
    type_id = request.GET.get('equipment_type')
    manufacturers = Manufacturer.objects.filter(equipment_type_id=type_id).order_by('name')
    # Render the model dropdown with the manufacturers that match the equipment type
    return render(request, 'equipment_type_dropdown_list_options.html', {'manufacturers': manufacturers})

class ChangeMonitoringSystemEQlistView(PermissionRequiredMixin, ListView):
    permission_required = 'othermdbapp.add_equipmentmonitoringsystemspec'
    model = Equipment
    template_name = 'change-monitoring-system-eq-list.html'
    paginate_by = 10

    def get_queryset(self):
        return Equipment.objects.exclude(equipmentmonitoringsystemspec=None).filter(equipmentmonitoringsystemspec__end_date=None).order_by('site__name', 'uuid').distinct()


class EquipmentSiteListView(PermissionRequiredMixin, ListView):
    permission_required = 'othermdbapp.add_equipment'
    model = Site
    template_name = 'equipment-site-list.html'
    ordering = ['name']
    paginate_by = 25

class SiteListView(ListView):
    model = Site
    template_name = 'site-list.html'
    ordering = ['name']
    paginate_by = 25

class SitePageView(ListView):
    model = Site
    template_name = 'sites.html'
    ordering = ['name']
    paginate_by = 25

class MonitoringSystemListView(PermissionRequiredMixin, ListView):
    permission_required = 'othermdbapp.add_monitoringsystem'
    model = MonitoringSystem
    template_name = 'monitoring-system-spec-list.html'
    ordering = ['name']
    paginate_by = 50

def model_upload_view(request):
    # when we post the form
    if request.method == 'POST':
        file_form = ModelUploadForm(request.POST, request.FILES)
        files = request.FILES.getlist('files')
        if file_form.is_valid():
            for f in files:
                # create yaml loader
                loader = yaml.load_all(f, Loader=SafeLoader)
                for dict in loader:
                    # if we don't have a "models" section
                    if "models" not in dict:
                        # throw error and return normal render
                        msg = "No \"models\" section found in file"
                        messages.add_message(request, messages.ERROR, msg)
                        return render(request, 'model-upload.html', {'fileForm': file_form})
                    else:
                        # unpack results
                        (saved_models, exceptions) = ModelFactory.create_models(dict["models"], save=True)
                        # show errors as messages
                        for e in exceptions:
                            messages.add_message(request, messages.ERROR, str(e))
                        # add the values for every field for each saved model 
                        return render(request, 'model-upload-result.html', {"savedModels": saved_models})
    else:
        file_form = ModelUploadForm()
    return render(request, 'model-upload.html', {'fileForm': file_form})

def process_influx_protocol(request):
    client = InfluxDBClient(host='influxdb', port=8086, username=os.environ.get('INFLUXDB_ADMIN_USER'), password=os.environ.get('INFLUXDB_ADMIN_PASSWORD'))
    if request.method == 'POST':
        if 'fileForm' in request.POST:
            file_form = FileUploadForm(request.POST, request.FILES, prefix='file')
            files = request.FILES.getlist('file-influx_files')
            text_form = TextUploadForm(prefix='text')
            if file_form.is_valid():
                database = file_form.cleaned_data['database']
                time_precision = 's'
                for f in files:
                    string_data = ""
                    messages.add_message(request, messages.DEBUG, f)
                    for chunk in f.chunks():
                        data = str(chunk, 'utf-8')
                        partial_data = data.replace('\r', '')
                        string_data = string_data + partial_data
                    try:
                        all_data = []
                        all_data = string_data.split('\n')
                        client.write_points(all_data, database=database, time_precision=time_precision,
                                            batch_size=10000, protocol='line')
                        messages.add_message(request, messages.SUCCESS, "Points successfully written")
                    except InfluxDBClientError as e:
                        e = str(e)
                        messages.add_message(request, messages.ERROR, e)

        elif 'textForm' in request.POST:
            text_form = TextUploadForm(request.POST, prefix='text')
            file_form = FileUploadForm(prefix='file')
            if text_form.is_valid():
                all_data = []
                database = text_form.cleaned_data['database']
                time_precision = 's'

                text = text_form.cleaned_data['influx_text']

                all_data = text.replace('\r', '').split('\n')

                try:
                    client.write_points(all_data, database=database, time_precision=time_precision, batch_size=10000,
                                        protocol='line')
                    messages.add_message(request, messages.SUCCESS, "Points successfully written")
                except InfluxDBClientError as e:
                    e = str(e)
                    if len(e) > 300:
                       e = e[:300] + '...'
                    messages.add_message(request, messages.ERROR, e)
    else:
        file_form = FileUploadForm(prefix='file')
        text_form = TextUploadForm(prefix='text')

    return render(request, 'data_upload.html', {'fileForm': file_form, 'textForm': text_form})

class DataDownloadFormView(FormView):
    form_class = DataDownloadForm
    template_name = 'data_download.html'
    def form_valid(self, form):
        try:
            data = form.query_database()
            response = HttpResponse(data, content_type='text/plain')
        except:
            print("Error occurred while querying the database")
        return response

def monitoring_system_spec(request, system_id):
    # Query the database for all necessary data for the form
    monitoring_system = MonitoringSystem.objects.get(id=system_id)
    context ={}

    # Check if the form was submitted
    if request.method == "POST":
        if request.POST.get("save"):
            # For all measurement specs that are to be associated with the monitoring system
            # create a new entry if one does not already exist
            for measurement_spec in request.POST.getlist("to"):
                m_spec = MeasurementSpec.objects.get(name=measurement_spec)
                spec_exists = MonitoringSystemSpec.objects.filter(monitoring_system=monitoring_system,
                                                                  measurement_type=m_spec.type,
                                                                  measurement_spec=m_spec).exists()
                # Save the new monitoring system spec if it doesn't exist
                if not spec_exists:
                    m_spec = MeasurementSpec.objects.get(name=measurement_spec)
                    new_ms_spec = MonitoringSystemSpec.objects.create()
                    new_ms_spec.monitoring_system = monitoring_system
                    new_ms_spec.measurement_type = m_spec.type
                    new_ms_spec.measurement_spec = m_spec
                    new_ms_spec.save()

            # For all measurement specs that shouldn't be associated with the monitoring system,
            # delete them if they exist
            for measurement_spec in request.POST.getlist("from"):
                m_spec = MeasurementSpec.objects.get(name=measurement_spec)
                spec_exists = MonitoringSystemSpec.objects.filter(monitoring_system=monitoring_system,
                                                                  measurement_type=m_spec.type,
                                                                  measurement_spec=m_spec).exists()
                # Delete the monitoring system spec if it exists
                if spec_exists:
                    to_be_deleted = MonitoringSystemSpec.objects.filter(monitoring_system=monitoring_system,
                                                                        measurement_type=m_spec.type,
                                                                        measurement_spec=m_spec)
                    to_be_deleted.delete()
            # Prepare success message to be displayed on redirect
            success_message = f'Successfully updated monitoring system specs for {monitoring_system.name}'
            messages.add_message(request, messages.SUCCESS, success_message)
            return redirect(reverse_lazy('system-spec-list'))

    else:
        monitoring_system_specs = MonitoringSystemSpec.objects.filter(monitoring_system_id=system_id)
        current_specs_list = monitoring_system_specs.values_list('measurement_spec', flat=True)
        measurement_specs_to_exclude = [spec for spec in current_specs_list]
        available_specs = MeasurementSpec.objects.exclude(id__in=measurement_specs_to_exclude)
        current_specs = MeasurementSpec.objects.filter(pk__in=measurement_specs_to_exclude)
        all_specs = MeasurementSpec.objects.all()

        # Create variables to pass as context to the template
        context = {
            "monitoring_system": monitoring_system,
            "current_specs": current_specs,
            "available_specs": available_specs,
            "all_specs": all_specs,
        }
    return render(request, "monitor-system-spec-update.html", context)

