# Generated by Django 5.1.4 on 2024-12-23 09:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accountsapp', '0005_customusermodel_hidden_posts'),
    ]

    operations = [
        migrations.AddField(
            model_name='customusermodel',
            name='dark_theme',
            field=models.BooleanField(default=True, verbose_name='Tema escuro'),
        ),
    ]