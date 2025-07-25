import os
import sys
import django
from django.core.management import call_command

def main():
    # Get the remote database URL from environment variable or user input
    remote_db_url = os.environ.get('REMOTE_DATABASE_URL')
    if not remote_db_url:
        print("Please set the REMOTE_DATABASE_URL environment variable to your remote database URL.")
        sys.exit(1)

    # Set the DATABASE_URL environment variable for Django settings
    os.environ['DATABASE_URL'] = remote_db_url

    # Set the Django settings module environment variable
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

    # Setup Django
    django.setup()

    # Run the createsuperuser command
    print("Running createsuperuser command connected to remote database...")
    call_command('createsuperuser')

if __name__ == '__main__':
    main()
