from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Run database migrations programmatically'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting migrations...')
        call_command('migrate')
        self.stdout.write('Migrations completed successfully.')
