from django.db import migrations

DEFAULT_CATEGORIES = [
    ("Food", "🍔"),
    ("Rent", "🏠"),
    ("Transport", "🚗"),
    ("Utilities", "💡"),
    ("Entertainment", "🎬"),
    ("Shopping", "🛍️"),
    ("Other", "📦"),
]


def seed_categories(apps, schema_editor):
    Category = apps.get_model("api", "Category")
    for name, icon in DEFAULT_CATEGORIES:
        Category.objects.get_or_create(name=name, defaults={"icon": icon})


def reverse_seed(apps, schema_editor):
    Category = apps.get_model("api", "Category")
    Category.objects.filter(name__in=[n for n, _ in DEFAULT_CATEGORIES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0001_initial"),
    ]
    operations = [
        migrations.RunPython(seed_categories, reverse_seed),
    ]
