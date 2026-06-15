from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from items.models import Item
from datetime import date, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Add sample lost and found items for testing'

    def handle(self, *args, **options):
        # Get the first user (admin)
        admin_user = User.objects.first()
        if not admin_user:
            self.stdout.write(
                self.style.ERROR('No users found. Please create a user first.')
            )
            return

        # Sample lost items
        lost_items = [
            {
                'title': 'Black Leather Wallet',
                'description': 'Lost my black leather wallet containing student ID and some cash. Last seen in college canteen.',
                'item_type': 'Lost',
                'category': 'Accessories',
                'location': 'College Canteen',
                'date_lost_found': date.today() - timedelta(days=2),
                'image': 'https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=400&h=300&fit=crop&crop=center'
            },
            {
                'title': 'House Keys',
                'description': 'Lost my house keys with a keychain near college park. Please help me find them.',
                'item_type': 'Lost',
                'category': 'Keys',
                'location': 'College Park',
                'date_lost_found': date.today() - timedelta(days=1),
                'image': 'https://images.unsplash.com/photo-1594736797933-d0401ba2fe65?w=400&h=300&fit=crop&crop=center'
            },
            {
                'title': 'Samsung Galaxy Phone',
                'description': 'Lost my Samsung Galaxy phone with black case in A Block. Please contact if found.',
                'item_type': 'Lost',
                'category': 'Electronics',
                'location': 'A Block',
                'date_lost_found': date.today() - timedelta(days=3),
                'image': 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400&h=300&fit=crop&crop=center'
            }
        ]

        # Sample found items
        found_items = [
            {
                'title': 'iPhone with Black Case',
                'description': 'Found an iPhone with black case and cracked screen in college auditorium.',
                'item_type': 'Found',
                'category': 'Electronics',
                'location': 'College Auditorium',
                'date_lost_found': date.today() - timedelta(days=1),
                'image': 'https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=400&h=300&fit=crop&crop=center'
            },
            {
                'title': 'Brown Leather Wallet',
                'description': 'Found a brown leather wallet in B Block. Contains some cash and student ID.',
                'item_type': 'Found',
                'category': 'Accessories',
                'location': 'B Block',
                'date_lost_found': date.today() - timedelta(days=2),
                'image': 'https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=400&h=300&fit=crop&crop=center'
            },
            {
                'title': 'Blue Backpack',
                'description': 'Found a blue backpack with books in college library. Contact to claim.',
                'item_type': 'Found',
                'category': 'Bags',
                'location': 'College Library',
                'date_lost_found': date.today() - timedelta(days=1),
                'image': 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=300&fit=crop&crop=center'
            }
        ]

        # Create items
        all_items = lost_items + found_items
        created_count = 0

        for item_data in all_items:
            item, created = Item.objects.get_or_create(
                title=item_data['title'],
                owner=admin_user,
                defaults={
                    'description': item_data['description'],
                    'item_type': item_data['item_type'],
                    'category': item_data['category'],
                    'location': item_data['location'],
                    'date_lost_found': item_data['date_lost_found'],
                    'image': item_data['image'],
                    'contact_info': admin_user.email
                }
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully added {created_count} sample items!')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Lost items: {len(lost_items)}, Found items: {len(found_items)}')
        )
