from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a superuser admin account'

    def handle(self, *args, **options):
        username = 'admin'
        email = 'admin@findit.com'
        password = 'admin123'
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'Admin user "{username}" already exists!')
            )
        else:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                full_name='System Administrator',
                phone='+1234567890',
                college='FindIt System'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created admin user!')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Admin Credentials:')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Username: {username}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Password: {password}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Admin URL: http://localhost:8000/admin/')
        )
