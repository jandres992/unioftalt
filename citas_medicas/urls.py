from django.contrib import admin
from django.urls import path
from citas_medicas.views import *

urlpatterns = [
    path('rec_citas/', recordatorio_citas, name='recordatorio_citas'),
    path('sol_what/', solicitudes_cita, name='solicitud_whatsapp'),
    path('sol_cmedicas/', sol_gen_cita, name='sol_gen_cmedicas'),
    path('sol_cmedicas_des/', solicitudes_cita_descartada, name='sol_cmedicas_des'),
    path('form_aten_cita/', form_cita, name='form_atencion_cita'),
    path('form_aten_cita_ext/', form_cita_ext, name='form_atencion_cita_ext'),
    path('data_cita/', data_pcte, name='form_data_pcte'),
]