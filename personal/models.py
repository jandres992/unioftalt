from django.db import models
from sistema.models import Tipo_id, Paciente as Persona


class Area(models.Model):
    area = models.CharField(max_length=80)

    class Meta:
        db_table = 'area_personal'


class Cargo(models.Model):
    cargo = models.CharField(max_length=180)
    dependencia = models.ForeignKey('Dependencia', models.DO_NOTHING)

    class Meta:
        db_table = 'cargo_personal'


class Dependencia(models.Model):
    dependencia = models.CharField(max_length=180)

    class Meta:
        db_table = 'dependencia_personal'


class Personal(models.Model):
    persona = models.ForeignKey(Persona, models.DO_NOTHING)
    lugar_exp = models.CharField(max_length=60, null=True, blank=True)
    fecha_ingreso = models.DateField(null=True, blank=True)
    area = models.ForeignKey('Area', models.DO_NOTHING, blank=True, null=True)
    cargo = models.ForeignKey('Cargo', models.DO_NOTHING, blank=True, null=True)
    imagen = models.ImageField(upload_to='img/photo', blank=True, null=True)
    activo = models.BooleanField(default=True)
    acudiente = models.CharField(max_length=90, blank=True, null=True)
    tel_acudiente = models.CharField(max_length=12, blank=True, null=True)
    eps = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        db_table = 'registro_personal'