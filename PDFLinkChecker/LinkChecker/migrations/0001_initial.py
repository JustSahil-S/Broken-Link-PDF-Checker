# Generated by Django 5.0.3 on 2024-04-01 19:20

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Links",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("url", models.URLField(max_length=1000)),
                ("statusCode", models.IntegerField()),
                ("dismiss", models.BooleanField()),
                ("ignore", models.BooleanField()),
                ("pdfSource", models.CharField(max_length=1000)),
                ("finalurl", models.URLField(max_length=1000)),
                ("urlText", models.CharField(max_length=1000)),
                ("lastChecked", models.BooleanField()),
            ],
        ),
    ]
