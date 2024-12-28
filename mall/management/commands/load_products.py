from dataclasses import dataclass
from django.core.management import BaseCommand
from django.core.files.base import ContentFile
import requests
from tqdm import tqdm

from mall.models import Category, Product

BASE_URL = "https://raw.githubusercontent.com/pyhub-kr/dump-data/main/django-shopping-with-iamport/"


@dataclass
class Item:
    category_name: str
    name: str
    price: int
    priceUnit: str
    desc: str
    photo_path: str


class Command(BaseCommand):
    help = "Load products from JSON file"

    def handle(self, *args, **options):
        json_url = BASE_URL + "product-list.json"
        response = requests.get(json_url).json()

        item_list = []
        for item_dict in response:
            # 같은 이름으로 모든 키워드 인자가 들어가 있어 unpack 문법 이용
            item = Item(**item_dict)
            item_list.append(item)

        category_name_set = {item.category_name for item in item_list}

        category_dict = {}
        for category_name in category_name_set:
            category, _ = Category.objects.get_or_create(name=category_name or "미분류")
            category_dict[category.name] = category

        for item in tqdm(item_list):
            category: Category = category_dict[item.category_name or "미분류"]
            product, is_created = Product.objects.get_or_create(
                category=category,
                name=item.name,
                defaults={
                    "description": item.desc,
                    "price": item.price,
                },
            )

            if is_created:
                photo_url = BASE_URL + item.photo_path
                filename = photo_url.rsplit("/", 1)[-1]
                photo_data = requests.get(photo_url).content  # raw data
                product.photo.save(
                    name=filename, content=ContentFile(photo_data), save=True
                )
