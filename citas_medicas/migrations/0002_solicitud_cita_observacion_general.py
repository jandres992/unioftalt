# Generated by Django 4.1.7 on 2023-03-18 21:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('citas_medicas', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='solicitud_cita',
            name='observacion_general',
            field=models.TextField(blank=True, default='', null=True),
        ),
    ]
