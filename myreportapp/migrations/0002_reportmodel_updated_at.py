# Generated by Django 5.1.4 on 2025-01-21 18:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myreportapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportmodel',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Data de Atualização'),
        ),
    ]
