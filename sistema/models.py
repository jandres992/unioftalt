from django.contrib.auth.models import User
from django.db import models

class Empresa(models.Model):
    nombre = models.CharField(max_length=180)
    razon_social = models.CharField(max_length=180)
    nit = models.CharField(max_length=80)
    dir = models.CharField(max_length=200)
    tel = models.CharField(max_length=20)
    web = models.CharField(max_length=60)
    email = models.EmailField()
    estado = models.BooleanField(default=True)
    n_app = models.CharField(max_length=60)

    class Meta:
        db_table = 'empresa_sistema'


class Tipo_id(models.Model):
    tipo_id = models.CharField(max_length=3)
    detalle = models.CharField(max_length=180)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = 'tipo_id_sistema'


class Sexo(models.Model):
    sexo = models.CharField(max_length=1)
    descripcion = models.CharField(max_length=20)

    class Meta:
        db_table = 'sexo_sistema'


class Paciente(models.Model):
    tipo_id = models.ForeignKey('Tipo_id', models.DO_NOTHING)
    numero_id = models.CharField(max_length=20)
    p_nombre = models.CharField(max_length=60, blank=True, null=True, default="")
    s_nombre = models.CharField(max_length=60, blank=True, null=True, default="")
    p_apellido = models.CharField(max_length=60, blank=True, null=True, default="")
    s_apellido = models.CharField(max_length=60, blank=True, null=True, default="")
    f_nacimiento = models.DateField(blank=True, null=True)
    sexo = models.ForeignKey('Sexo', models.DO_NOTHING, blank=True, null=True, default="")
    municipio_residencia = models.ForeignKey('Municipio', models.DO_NOTHING, blank=True, null=True, default="")
    direccion_residencia = models.CharField(max_length=250, blank=True, null=True, default="")
    telefono_fijo = models.CharField(max_length=12, blank=True, null=True, default="")
    telefono_movil = models.CharField(max_length=12)
    grupo_s = models.CharField(max_length=5, blank=True, null=True, default="")
    email = models.EmailField(blank=True, null=True, default="")
    envio_inf = models.BooleanField(default=True)
    envio_publ = models.BooleanField(default=True)
    observacion = models.TextField(blank=True, null=True, default="")

    class Meta:
        db_table = 'paciente_sistema'


class Municipio(models.Model):
    codigo = models.CharField(max_length=30)
    municipio = models.CharField(max_length=60)
    departamento = models.ForeignKey('Departamento', models.DO_NOTHING)

    class Meta:
        db_table = 'municipio_sistema'


class Departamento(models.Model):
    codigo = models.CharField(max_length=30)
    departamento = models.CharField(max_length=60)

    class Meta:
        db_table = 'departamento_sistema'


class Lista_negra_msg(models.Model):
    fecha = models.DateTimeField()
    id_pcte = models.ForeignKey('Paciente', models.DO_NOTHING)

    class Meta:
        db_table = 'lista_negra_msg_sistema'


class Settings_msg_sms(models.Model):
    linea_goip_linea = models.CharField(max_length=5, default="")
    linea_goip_ip = models.CharField(max_length=20, default="")
    linea_goip_user = models.CharField(max_length=10, default="")
    linea_goip_password = models.CharField(max_length=30, default="")
    linea_goip = models.BooleanField(default=False)
    linea_issabel_nomb = models.CharField(max_length=10, default="")
    linea_issabel_ip = models.CharField(max_length=30, default="")
    linea_issabel_user = models.CharField(max_length=10, default="")
    linea_issabel_password = models.CharField(max_length=20, default="")
    linea_issabel = models.BooleanField(default=False)
    usage = models.BooleanField(default=False)

    class Meta:
        db_table = 'settings_msg_sms_sistema'


class Settings_msg_whatsapp(models.Model):
    dir = models.CharField(max_length=30, default="")
    port = models.CharField(max_length=7, default="")
    whatsapp = models.BooleanField(default=False)
    usage = models.BooleanField(default=False)

    class Meta:
        db_table = 'settings_msg_whatsapp_sistema'


class Settings_msg_email(models.Model):
    habilitado = models.BooleanField(default=False)
    dir = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    dir_server = models.CharField(max_length=100)
    port_server = models.CharField(max_length=5)
    usage = models.BooleanField(default=False)

    class Meta:
        db_table = 'settings_msg_email_sistema'


class Msg_whatsapp(models.Model):
    habilitado = models.BooleanField(default=False)
    tipo = models.ForeignKey('Tipo_tramite', models.DO_NOTHING, null=True, default=None)
    saludo = models.CharField(max_length=180, default="")
    mensaje = models.TextField(default="")
    detalle = models.TextField(default="")
    observacion = models.TextField(default="")

    class Meta:
        db_table = 'msg_whatsapp_sistema'


class Msg_sms(models.Model):
    habilitado = models.BooleanField(default=False)
    tipo = models.ForeignKey('Tipo_tramite', models.DO_NOTHING, null=True, default=None)
    mensaje = models.TextField(default="")

    class Meta:
        db_table = 'msg_sms_sistema'


class Msg_email(models.Model):
    habilitado = models.BooleanField(default=False)
    tipo = models.ForeignKey('Tipo_tramite', models.DO_NOTHING, null=True, default=None)
    titulo = models.CharField(max_length=100, default="")
    mensaje = models.TextField(default="")
    detalle = models.TextField(default="")
    recomendacion = models.TextField(default="")

    class Meta:
        db_table = 'msg_email_sistema'


class Tipo_tramite(models.Model):
    tramite = models.CharField(max_length=100)
    activo = models.BooleanField(default=False)
    visible = models.BooleanField(default=False)
    txt = models.CharField(max_length=100, blank=True, default="")

    class Meta:
        db_table = 'tipo_tramite_sistema'
