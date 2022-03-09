from django.core.management import BaseCommand
from othermdbapp.daily_summaries import get_daily_summaries

class Command(BaseCommand):
    help = 'Fetch daily summary data from the InfluxDB instance.'

    def add_arguments(self, parser):
        parser.add_argument('equipment_uuid', type=str, help="The UUID of the equipment of interest.")
        parser.add_argument('start_date', type=str, help="The start date of interest format: \"YYYY-MM-DD\"")
        parser.add_argument('end_date', nargs="?", default=None, type=str, help="The end date of interest format: \"YYYY-MM-DD\"")

    def handle(self, *args, **kwargs):
        equip = kwargs['equipment_uuid']
        start_date = kwargs['start_date']
        end_date = kwargs['end_date']
    
        df = get_daily_summaries(equip, start_date, end_date)
        print(f"\n{df}\n")
