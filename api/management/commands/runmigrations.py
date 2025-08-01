from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
import sys
import os

class Command(BaseCommand):
    help = 'Run database migrations programmatically and promote first user to superuser'

    def handle(self, *args, **kwargs):
        # Add project root to sys.path for imports
        sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../../')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.backend.settings')

        self.stdout.write('Starting migrations...')
        call_command('migrate')
        self.stdout.write('Migrations completed successfully.')

        User = get_user_model()
        try:
            user = User.objects.first()
            if user and not user.is_superuser:
                user.is_superuser = True
                user.is_staff = True
                user.save()
                self.stdout.write(f'User {user.username} promoted to superuser.')
            else:
                self.stdout.write('No user found or user already superuser.')
        except Exception as e:
            self.stdout.write(f'Error promoting user: {e}')
