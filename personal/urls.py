from django.urls import path
from personal.views import *

urlpatterns = [
    path('princ/', personal, name='personal'),
    path('carnets/', carnet_personal, name='carnet_pers'),
]