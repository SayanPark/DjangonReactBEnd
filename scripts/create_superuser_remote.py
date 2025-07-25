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

    # Add the backend directory to sys.path to fix ModuleNotFoundError
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

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
