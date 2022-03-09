from django.core.management import BaseCommand
from othermdbapp.daily_summaries import get_equipment_data, create_daily_summaries

class Command(BaseCommand):
    help = 'Create daily summaries for an equipment and data range, and upload to the InfluxDB instance.'

    def add_arguments(self, parser):
        parser.add_argument('equipment_uuid', type=str, help="The UUID of the equipment of interest.")
        parser.add_argument('start_date', type=str, help="The start date of interest format: \"YYYY-MM-DD\"")
        parser.add_argument('end_date', type=str, help="The end date of interest format: \"YYYY-MM-DD\"")
        parser.add_argument('--dry-run', action="store_true", help="If provided, fetch and calculate the summaries with saving them to Influx.")

    def handle(self, *args, **kwargs):
        equip = kwargs['equipment_uuid']
        start_date = kwargs['start_date']
        end_date = kwargs['end_date']
        dry_run = kwargs['dry_run']

        ds = create_daily_summaries(equip, start_date, end_date, dry_run)
        print(f"\n{ds}\n")