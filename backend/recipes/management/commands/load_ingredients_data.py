from csv import DictReader
from typing import Any
from django.core.management import BaseCommand
from recipes.models import Ingredient

ALREADY_LOADED_ERROR_MESSAGE = """
If you need to reload the child data from the CSV file,
first delete the db.sqlite3 file to destroy the database.
Then, run `python manage.py migrate` for a new empty
database with tables"""


class Command(BaseCommand):
    help = "Loads data from category.csv"

    def handle(self, *args: Any, **options):
        if Ingredient.objects.exists():
            print('category data already loaded...exiting')
            print(ALREADY_LOADED_ERROR_MESSAGE)
            return

        for row in DictReader(open(
                              'data/ingredients.csv',
                              encoding="utf-8-sig")):
            ingredient = Ingredient(
                name=row['name'],
                measurement_unit=row['measurement_unit'])
            ingredient.save()
