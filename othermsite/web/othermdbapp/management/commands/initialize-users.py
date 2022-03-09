from django.core.management import BaseCommand
from django.contrib.auth.models import User
from django.contrib.auth.models import Group, Permission
import os

class Command(BaseCommand):
    help = 'Initializes the admin user, default "otherm user", and creates the permisisons group.'
    
    def handle(self, *args, **kwargs):
        # admin and otherm user are pulled from environment variable
        admin = User.objects.create_superuser('admin', 'admin@localhost.localhost', os.environ.get("DJANGO_SUPERUSER_PASSWORD"))
        user  = User.objects.create_user(username=os.environ.get("DJANGO_OTHERM_USER_USERNAME"), password=os.environ.get("DJANGO_OTHERM_USER_PASSWORD"))

        # create new group for otherm perms
        otherm_group, created = Group.objects.get_or_create(name='otherm_user')
        
        # add perms to group 
        perm_strings = [
            'add_equipment',
            'add_equipmentmonitoringsystemspec',
            'add_monitoringsystem',
            'add_site',
            'add_sitesourcemap',
            'add_source',
            'add_sourcespec',
            'add_thermalload',
        ]
        for perm in perm_strings:
            try:
                otherm_group.permissions.add(Permission.objects.get(codename=perm))
            except:
                print(f"There was a problem adding permssion '{perm}' to group.")   
        
        # add user (and admin) to group
        otherm_group.user_set.add(user)
        otherm_group.user_set.add(admin)