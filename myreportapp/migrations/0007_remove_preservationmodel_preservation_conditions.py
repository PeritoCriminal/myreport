# Generated by Django 5.1.4 on 2025-01-28 18:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myreportapp', '0006_rename_vehicle_preservationmodel_official_vehicle'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='preservationmodel',
            name='preservation_conditions',
        ),
    ]
