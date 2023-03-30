from django.db import models
from django.contrib.auth.models import User, Group
from sistema.models import Tipo_id, Paciente


class Modulo(models.Model):
    modulo = models.CharField(max_length=30)
    usuario = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    turno = models.CharField(max_length=10, blank=True, null=True)
    hora = models.DateTimeField(blank=True, null=True)
    habilitado = models.BooleanField(default=False)

    class Meta:
        db_table = 'modulo_digiturno'


class Consultorio(models.Model):
    consultorio = models.CharField(max_length=30)
    piso = models.CharField(max_length=2)
    habilitado = models.BooleanField(default=False)
    usuario = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        db_table = 'consultorio_digiturno'


class Servicio(models.Model):
    letra = models.CharField(max_length=1, blank=True, null=True)
    servicio = models.CharField(max_length=60)
    rango_ini = models.IntegerField()
    rango_fin = models.IntegerField()
    color = models.CharField(max_length=30)
    icon = models.CharField(max_length=30)
    horario = models.CharField(max_length=250, blank=True, null=True)
    horario_fin = models.TimeField(blank=True, null=True)
    habilitado = models.BooleanField(default=True, blank=True, null=True)

    class Meta:
        db_table = 'servicio_digiturno'


class Registro_digiturno(models.Model):
    no_turno = models.IntegerField()
    tp_id = models.ForeignKey(Tipo_id, models.DO_NOTHING)
    no_id = models.CharField(max_length=20)
    tel = models.CharField(max_length=14, blank=True, null=True)
    servicio = models.ForeignKey('Servicio', models.DO_NOTHING)
    modulo = models.ForeignKey('Modulo', models.DO_NOTHING, blank=True, null=True)
    usuario = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    llamado = models.BooleanField(default=False)
    r_llamado = models.BooleanField(default=False)
    fecha = models.DateTimeField()
    fecha_atendido = models.DateTimeField(blank=True, null=True)
    aviso = models.BooleanField(default=False)
    general = models.BooleanField(default=False)
    preferencial = models.BooleanField(default=False)

    class Meta:
        db_table = 'turno_pcte_digiturno'


class Reg_consul_digiturno(models.Model):
    id_pcte = models.ForeignKey(Paciente, models.DO_NOTHING)
    consultorio = models.ForeignKey('Consultorio', models.DO_NOTHING)
    llamado = models.BooleanField(default=False)
    u_llamado = models.BooleanField(default=False)
    fecha = models.DateTimeField(blank=True, null=True)
    aviso = models.BooleanField(default=False)
    user = models.ForeignKey(User, models.DO_NOTHING)

    class Meta:
        db_table = 'llamado_pcte_consultorio_digiturno'


class Turno(models.Model):
    servicio = models.ForeignKey('Servicio', models.DO_NOTHING)
    turno = models.IntegerField()

    class Meta:
        db_table = 'turno_digiturno'


class Publicidad(models.Model):
    url = models.CharField(max_length=255)
    tema = models.TextField()
    order = models.IntegerField()
    tipo = models.CharField(max_length=10)

    class Meta:
        db_table = 'publicidad_digiturno'


class Settings(models.Model):
    datos_pcte = models.BooleanField(default=False)
    tel = models.BooleanField(default=False)
    letra = models.BooleanField(default=False)
    impresion = models.BooleanField(default=False)
    repr_audio_turno = models.BooleanField(default=False)
    repr_audio_consult = models.BooleanField(default=False)

    class Meta:
        db_table = 'settings_digiturno'