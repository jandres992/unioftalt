from django.urls import path
from turno_digital.views import *

urlpatterns = [
    path('', login_dig, name='dig_login'),
    path('logconsult/', login_consult_dig, name='dig_login_consult'),
    path('logout', logout_dig, name='dig_logout'),
    path('rep_ind/', reportes_dig, name='dig_reporte'),
    path('pantalla/', pantalla_dig, name='dig_pantalla'),
    path('pant_cons/', pantalla_consult_dig, name='dig_pantalla_consult'),

    path('digiturno/', digiturno_dig, name='dig_digiturno'),
    path('turnos/', consulta_turno_dig, name='dig_consulta_turnos'),

    path('proyeccion/', consulta_modulo, name='proyeccion_turnos'),

    path('llamado/', llamado_turno_dig, name='dig_llamado_turno'),
    path('llamadoConsult/', llamado_consult_dig, name='dig_llamado_consultorio'),
    path('adm_digiturno/', admin_dig, name='dig_admin'),
    path('generacion_turnos/', generacion_turno_dig, name='dig_turno'),
    path('ticket_turno/', ticket_turno_dig, name='dig_ticket_turno'),
]