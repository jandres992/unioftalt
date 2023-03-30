from django.db import models
from sistema.models import Tipo_id, Sexo, Paciente, Tipo_tramite
from django.contrib.auth.models import User


class Estado_cita(models.Model):
    id_esalud = models.CharField(max_length=3)
    estado = models.CharField(max_length=60)

    class Meta:
        db_table = 'estado_cita'


class Notificacion_msg_cita(models.Model):
    fecha = models.DateTimeField()
    id_cita = models.CharField(max_length=20)
    whatsapp = models.BooleanField(default=False)
    sms = models.BooleanField(default=False)
    mail = models.BooleanField(default=False)
    observacion = models.TextField()
    id_aten = models.ForeignKey('Solicitud_cita', models.DO_NOTHING)
    user = models.ForeignKey(User, models.DO_NOTHING)

    class Meta:
        db_table = 'notificacion_envio_msg_cita'


class Directorio_contactos(models.Model):
    id_usr = models.CharField(max_length=20,blank=True,null=True)
    tipo_id = models.ForeignKey(Tipo_id, models.DO_NOTHING)
    no_id = models.CharField(max_length=30)
    nombre = models.CharField(max_length=280)
    telefono = models.CharField(max_length=10)
    email = models.CharField(max_length=100)
    tipo_persona = models.CharField(max_length=100)

    class Meta:
        db_table = 'directorio_contactos_cita'


class Especialidad_ref_cita(models.Model):
    nombre = models.CharField(max_length=100)
    orden = models.IntegerField()

    class Meta:
        db_table = 'especialidad_ref_cita'


class Eps_ref_cita(models.Model):
    nombre = models.CharField(max_length=100)
    orden = models.IntegerField()

    class Meta:
        db_table = 'eps_ref_cita'


class Regimen_eps(models.Model):
    regimen = models.CharField(max_length=100)

    class Meta:
        db_table = 'regimen_eps_cita'


class Tipo_servicio_cita(models.Model):
    servicio = models.CharField(max_length=100)

    class Meta:
        db_table = 'tipo_servicio_cita'


class Solicitud_cita(models.Model):
    fecha_s = models.DateTimeField()
    fecha_cita = models.CharField(max_length=200, blank=True, null=True)
    pcte = models.ForeignKey(Paciente, models.DO_NOTHING)
    eps = models.ForeignKey('Eps_ref_cita', models.DO_NOTHING, blank=True, null=True)
    regimen = models.ForeignKey('Regimen_eps', models.DO_NOTHING, blank=True, null=True)
    especialidad = models.ForeignKey('Especialidad_ref_cita', models.DO_NOTHING,blank=True, null=True)
    servicio = models.ForeignKey('Tipo_servicio_cita', models.DO_NOTHING, blank=True, null=True)
    tramite = models.ForeignKey(Tipo_tramite, models.DO_NOTHING, blank=True, null=True)
    no_aut = models.CharField(max_length=100, blank=True, null=True)
    atendido = models.BooleanField(default=False)
    descartar = models.BooleanField(default=False)
    l_espera = models.BooleanField(default=False, blank=True, null=True)
    bloqueo_atencion = models.BooleanField(default=False, blank=True, null=True)
    usuario_atencion = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    orden_img = models.ImageField(upload_to='data_pcte/orden')
    aut_img = models.ImageField(upload_to='data_pcte/aut')
    observacion_des = models.TextField(blank=True, null=True)
    observacion_eps = models.TextField(blank=True, null=True)
    fecha_aten = models.DateTimeField(blank=True, null=True, default=None)
    observacion_general = models.TextField(blank=True, null=True, default='')

    class Meta:
        db_table = 'solicitud_cita'


class Listado_espera_cita(models.Model):
    fecha = models.DateTimeField()
    motivo = models.CharField(max_length=200,blank=True, null=True)
    id_solicitud = models.ForeignKey('Solicitud_cita', models.DO_NOTHING)
    usuario = models.ForeignKey(User, models.DO_NOTHING)
    envio_msg = models.BooleanField(default=False)

    class Meta:
        db_table = 'listado_espera_cita'