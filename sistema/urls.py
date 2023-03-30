from django.contrib import admin
from django.urls import path
from sistema.views import *

urlpatterns = [
    path('', login, name='general_login'),
    path('logout', logout, name='general_logout'),
    path('menu', menu, name='general_menu'),
    path('usr', usuario_sistema, name='system_user'),
    path('busq_pcte', busq_persona, name='busq_persona'),
    path('s_pcte', save_persona, name='save_persona'),
    path('s_municipio', obtener_municipio, name='search_municipio'),

]