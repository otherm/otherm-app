from import_export import resources

from .models import WeatherData


class WeatherResource(resources.ModelResource):
    class Meta:
        model = WeatherData
