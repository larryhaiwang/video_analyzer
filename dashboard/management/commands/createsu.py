'''
This script allows system to create a superuser without prompt input. 
python manage.py createsu
'''

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):

    def handle(self, *args, **options):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser('admin', 'founder@fractal-pi.com', '1p2o3i4u')