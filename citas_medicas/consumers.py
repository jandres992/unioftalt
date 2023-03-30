import json, datetime
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from citas_medicas.models import *
from citas_medicas.tasks import send_notificacion_cita


class CmedicasConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.turno = ""

    def connect(self):
        async_to_sync(self.channel_layer.group_add)(
            'citas_modulo', self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        self.close(close_code)

    def receive(self, text_data):
        message = json.loads(text_data)
        if 'no_aten' in message:
            sa = Solicitud_cita.objects.get(id=message['no_aten'])
        else:
            sa = None
        av_ind = False
        data = None
        if sa is not None:
            if message['tipo'] == "seleccionar":
                user = self.scope['user'].id
                if not sa.l_espera and sa.usuario_atencion is None:
                    sa.bloqueo_atencion = True
                    sa.usuario_atencion_id = user
                    hab = True
                elif sa.bloqueo_atencion and sa.usuario_atencion_id == user and not sa.l_espera:
                    hab = True
                elif sa.l_espera:
                    sa.usuario_atencion_id = user
                    hab = True
                else:
                    hab = False

                if hab:
                    ind = 2
                    username = sa.usuario_atencion.username
                    aviso = ""
                    sa.save()
                else:
                    ind = 0
                    aviso = "El usuario ya esta siendo atendido."
                    username = ""

                data = {'ind': ind, 'tipo': message['tipo'], 'user': username, 'user_id': user,
                        'solicitud_id': sa.id, 'aviso': aviso}

                async_to_sync(self.channel_layer.group_send)(
                    "citas_modulo",
                    {
                        'type': "send_citas_modulo_message",
                        'tipo': data['tipo'],
                        'ind': data['ind'],
                        'data': data
                    },
                )
                av_ind = False

            elif message['tipo'] == "atender":
                try:
                    ayer = datetime.date.today() - datetime.timedelta(1)
                    tramite = sa.tramite.tramite.title()

                    if tramite == 'Cancelar Cita':
                        cita_h = THistoCitas.objects.using('esalud').filter(fecha_histoc__lte=ayer,
                                                                            id_cita__id_pcte__tp_id_pcte__t_tp_id=sa.pcte.tipo_id.tipo_id,
                                                                            id_cita__id_pcte__num_id_pcte=sa.pcte.numero_id,
                                                                            estado=3).order_by('-id_cita')
                        if cita_h:
                            cita = [cita_h[0].id_cita]
                        else:
                            cita = []
                    elif tramite == 'Agendar Cita':
                        cita = TInfoCitas.objects.using('esalud').filter(fecha_ini__lte=ayer,
                                                                         id_pcte__tp_id_pcte__t_tp_id=sa.pcte.tipo_id.tipo_id,
                                                                         id_pcte__num_id_pcte=sa.pcte.numero_id).order_by('-id_cita')
                    else:
                        cita = []

                    lista = []
                    for c in cita:
                        env = Notificacion_msg_cita.objects.filter(id_cita=c.id_cita)
                        if not env:
                            lista.append(dict(
                                nombre=str(c.id_pcte.pri_nom_pcte + " " + c.id_pcte.seg_nom_pcte + " " + c.id_pcte.pri_apell_pcte + " " + c.id_pcte.seg_apell_pcte).title(),
                                fecha=str(c.fecha_ini.strftime("%d/%m/%Y")) + " " + str(c.fecha_ini.strftime("%I:%M %p")),
                                convenio=c.id_conv_cita.nom_conv,
                                ids=c.id_cita,
                                especialidad=c.id_esp_cita.nom_esp,
                                telefono=c.id_pcte.tel_pcte[0:10],
                                no_aten=str(message['no_aten'])))

                    if lista:
                        ind = 2
                        aviso = "Los datos se han registrado exitosamente"
                        data = {'ind': ind, 'aviso': aviso, 'tipo': message['tipo'], 'lista': lista}
                    else:
                        ind = 1
                        aviso = "No se encontro registro en E-Salud para {}, compruebe si el número de identificación " \
                                "esta bien escrito en el cuadro e intente nuevamente".format(tramite).lower()
                        data = {'ind': ind, 'aviso': aviso, 'tipo': message['tipo']}
                except:
                    ind = 0
                    aviso = "Error en el servidor, comuniquese con el area de desarrollo"
                    data = {'ind': ind, 'aviso': aviso, 'tipo': message['tipo']}
                av_ind = True

            elif message['tipo'] == "descartar":
                sa.observacion_des = message['observacion_des']
                sa.atendido = True
                sa.l_espera = False
                sa.descartar = True
                sa.fecha_aten = datetime.datetime.now()
                sa.save()

                aviso = ""
                if 'envio_sms_des' in message:
                    if message['envio_sms_des'] == 'SI':
                        send_notificacion_cita.delay(self.scope['user'].id, message)
                        aviso = "El proceso de envio de notificación a " + str(sa.pcte.p_nombre + " " + sa.pcte.p_apellido).upper() + " ha sido iniciado"

                data = {'ind': 2, 'aviso': "La solicitud se ha descartado. " + aviso, 'tipo': "notificacion"}
                self.scope['session']['aviso'] = data
                self.scope['session'].save()
                av_ind = True

            elif message['tipo'] == "send_msg" or message['tipo'] == "espera":
                if message['tipo'] == "espera":
                    sa.atendido = False
                    sa.l_espera = True
                    sa.descartar = False
                else:
                    sa.atendido = True
                    sa.l_espera = False
                    sa.descartar = False
                sa.fecha_aten = datetime.datetime.now()
                sa.save()

                send_notificacion_cita.delay(self.scope['user'].id, message)

                data = {'ind': 2, 'aviso': "El proceso de envio de notificación a " + str(sa.pcte.p_nombre + " " + sa.pcte.p_apellido).title() + " ha sido iniciado", 'tipo': "notificacion"}
                self.scope['session']['aviso'] = data
                self.scope['session'].save()
                av_ind = True

        if av_ind:
            self.send(text_data=json.dumps({
                'type': "citas_modulo",
                'data': data
            }))

    def send_citas_modulo_message(self, message):
        self.send(text_data=json.dumps({
            'type': message['type'],
            'data': message['data']
        }))