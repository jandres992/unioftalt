from django.urls import re_path
from turno_digital import consumers as d_consumer
from citas_medicas import consumers as c_consumer

websocket_urlpatterns = [
    re_path(r'ws/gen_turno/', d_consumer.GenTurnoConsumer.as_asgi()),
    re_path(r'ws/pantalla/', d_consumer.PantallaConsumer.as_asgi()),
    re_path(r'ws/pantalla_consult/', d_consumer.PantallaconsultConsumer.as_asgi()),
    re_path(r'ws/modulo/', d_consumer.ModuloConsumer.as_asgi()),
    re_path(r'ws/llamadoConsult/', d_consumer.LlamadoconsultConsumer.as_asgi()),
    re_path(r'ws/citasModulo/', c_consumer.CmedicasConsumer.as_asgi())
]