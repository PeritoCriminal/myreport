# Generated by Django 5.1.4 on 2025-01-29 01:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myreportapp', '0008_preservationmodel_section'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportmodel',
            name='section_dataservice',
            field=models.CharField(default='Dados do Atendimento', max_length=255, verbose_name='Daodos do Atendimento'),
        ),
        migrations.AddField(
            model_name='reportmodel',
            name='section_datauser',
            field=models.CharField(default='Dados Gerais', max_length=255, verbose_name='Dados Gerais'),
        ),
        migrations.AddField(
            model_name='reportmodel',
            name='section_police_report',
            field=models.CharField(default='Dados do Boletim de Ocorrência', max_length=255, verbose_name='Daodos do Boletim'),
        ),
    ]
