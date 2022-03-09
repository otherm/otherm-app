from django.urls import path
from django.views.generic import TemplateView
from django.conf.urls import include, re_path
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views
from django.contrib.auth.decorators import user_passes_test

from . import views as otherm_views

router = DefaultRouter()
router.register(r'equipment', otherm_views.EquipmentViewSet, basename='equipment')
router.register(r'weather_station', otherm_views.WeatherStationViewSet, basename='weather_station')
router.register(r'site', otherm_views.SiteViewSet, basename='site')
router.register(r'monitoring_system', otherm_views.MonSysViewSet, basename='monitoring_system')
router.register(r'equipment_monitoring', otherm_views.EquipmentMonitoringViewSet, basename='equipment_monitoring')
router.register(r'thermal_source', otherm_views.SiteSourceMapViewSet, basename='thermal_source')
router.register(r'equipment_specs', otherm_views.EquipmentModelViewSet, basename='equipment_specs')
router.register(r'thermal_load', otherm_views.SiteThermalLoadViewSet, basename='thermal_load')
router.register(r'equipment_data', otherm_views.EquipmentDataViewSet, basename='equipment_data')

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('api-token-auth/', otherm_views.CustomAuthToken.as_view()),
    path('', otherm_views.index, name='index'),
    path('sites/', otherm_views.SitePageView.as_view(), name='sites'),
    path('site-forms/', otherm_views.site_forms, name='site-forms'),
    path('admin-forms/', otherm_views.admin_forms, name='admin-forms'),
    path('testing/', TemplateView.as_view(template_name='testing.html'), name='testing'),
    path('data-upload/', user_passes_test(lambda u: u.is_superuser, login_url='403')(otherm_views.process_influx_protocol), name='data-upload'),
    path('data-download/', otherm_views.DataDownloadFormView.as_view(), name='data-download'),
    path('model-upload/', user_passes_test(lambda u: u.is_superuser, login_url='403')(otherm_views.model_upload_view), name='model-upload'),
    path('site-list/', otherm_views.SiteListView.as_view(), name='site-list'),
    path('site-registration/', otherm_views.SiteCreate.as_view(), name='site-registration'),
    path('thermal-load/', otherm_views.ThermalLoadCreate.as_view(), name='thermal-load'),
    path('site-source-registration/', otherm_views.SiteSourceMapCreate.as_view(), name='site-source-registration'),
    path('source-registration/', otherm_views.SourceCreate.as_view(), name='source-registration'),
    path('source-spec-registration/', otherm_views.SourceSpecCreate.as_view(), name='source-spec-registration'),
    path('air-source-spec-form/', otherm_views.AirSourceSpecCreate.as_view(), name='air-source-spec-form'),
    path('standing-column-spec-form/', otherm_views.StandingColumnSpecCreate.as_view(), name='standing-column-spec-form'),
    path('open-loop-spec-form/', otherm_views.OpenLoopSpecCreate.as_view(), name='open-loop-spec-form'),
    path('vertical-loop-spec-form/', otherm_views.VerticalLoopSpecCreate.as_view(), name='vertical-loop-spec-form'),
    path('horizontal-loop-spec-form/', otherm_views.HorizontalLoopSpecCreate.as_view(), name='horizontal-loop-spec-form'),
    path('pond-spec-form/', otherm_views.PondSpecCreate.as_view(), name='pond-spec-form'),
    path('system-spec-list/', user_passes_test(lambda u: u.is_superuser, login_url='403')(otherm_views.MonitoringSystemListView.as_view()), name='system-spec-list'),
    path('system-spec-registration/<int:system_id>/', otherm_views.monitoring_system_spec,
         name='system-spec-registration'),
    path('add-monitoring-system/', otherm_views.EquipmentMonitoringSystemSpecCreate.as_view(), name='add-monitoring-system'),
    path('system-registration/', user_passes_test(lambda u: u.is_superuser, login_url='403')(otherm_views.MonitorSystemCreate.as_view()), name='system-registration'),
    path('equipment-site-list/', otherm_views.EquipmentSiteListView.as_view(), name='equipment-site-list'),
    path('add-equipment/<pk>/', otherm_views.EquipmentCreate.as_view(), name='registration'),
    path('change-monitoring-system-eq-list/', otherm_views.ChangeMonitoringSystemEQlistView.as_view(), name='change-monitoring-system-eq-list'),
    path('change-monitoring-system/<pk>/', otherm_views.ChangeMonitoringSystem.as_view(), name='change-monitoring-system'),
    path('change-monitoring-system-redirect/<int:pk>/', otherm_views.ChangeMonitoringSystemSpecRedirect, name='change-monitoring-system-redirect'),
    path('change-monitoring-system-choice/<pk>/', otherm_views.ChangeMonitoringSystemChoice.as_view(), name='change-monitoring-system-choice'),
    path('delete-equipment/<pk>/', otherm_views.EquipmentDelete.as_view(), name='equipment-delete'),
    path('weather-form/', user_passes_test(lambda u: u.is_superuser, login_url='403')(otherm_views.WeatherFormView.as_view()), name='weather'),
    path('data-audit/', otherm_views.AuditDataView.as_view(), name='audit'),
    path('ajax/load-models/', otherm_views.load_models, name='ajax_load_models'),
    path('ajax/load-manufacturers/', otherm_views.load_manufacturers, name='ajax_load_manufacturers'),
    path('ajax/load-equip-from-site/', otherm_views.load_equipment_from_site, name='ajax_load_equipment_from_site'),
    path('ajax/load_source_spec_form/', otherm_views.load_source_spec_form, name='ajax_load_source_spec_form'),
    path('403/', TemplateView.as_view(template_name='403.html'), name='403'),
]


