from django.core.management import BaseCommand

BASE_URL = "https://raw.githubusercontent.com/pyhub-kr/dump-data/main/django-shopping-with-iamport/product-list.json"


class Command(BaseCommand):
    help = "Load products from JSON file"

    def handle(self, *args, **options):
        print("handle!")
        pass
