import json, datetime, os.path, time, requests

from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.utils import timezone
from turno_digital.models import *
from unioftalt.settings import SOUNDS_ROOT
from turno_digital.tasks import obtener_data_pcte
from pydub import AudioSegment
from gtts import gTTS


class GenTurnoConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.turno = TurnoObject()

    def connect(self):
        async_to_sync(self.channel_layer.group_add)(
            'gen_turnos', self.channel_name
        )
        self.accept()
        self.send(text_data=json.dumps({
            'message': 'Conexión establecida'
        }))

    def disconnect(self, close_code):
        self.close(close_code)

    def receive(self, text_data):
        message = json.loads(text_data)
        tp_id = message['tp_id']
        no_id = message['no_id']
        tp_turno = message['tp_turno']
        servicio_id = message['servicio']

        servicio_act = Servicio.objects.get(id=servicio_id)
        horario_fin = servicio_act.horario_fin
        actual = datetime.datetime.now().time()

        # try:
        if actual <= horario_fin:
            rango_ini = servicio_act.rango_ini
            rango_fin = servicio_act.rango_fin

            turno = Turno.objects.get(servicio_id=servicio_id)
            turno_act = int(turno.turno)
            if turno_act >= rango_fin:
                new_turno = rango_ini
            else:
                new_turno = turno_act + 1

            new_digiturno = Registro_digiturno()
            new_digiturno.tp_id_id = tp_id
            new_digiturno.no_id = no_id
            new_digiturno.no_turno = new_turno
            new_digiturno.fecha = datetime.datetime.now()
            new_digiturno.servicio_id = servicio_id
            new_digiturno.aviso = False
            new_digiturno.llamado = False
            new_digiturno.atencion = False
            if tp_turno == "general":
                new_digiturno.general = True
                new_digiturno.preferencial = False
            else:
                new_digiturno.general = False
                new_digiturno.preferencial = True
            new_digiturno.save()

            act_turno = turno
            act_turno.turno = new_turno
            act_turno.save()

            obtener_data_pcte.delay(new_digiturno.tp_id.tipo_id, str(new_digiturno.no_id), str())

            ind = 1
            data = {'id_turno': new_digiturno.id}
        else:
            ind = 0
            data = {'aviso': "Fuera de Horario"}

        message_get = self.turno.get_turnos()
        async_to_sync(self.channel_layer.group_send)(
            "modulo",
            {
                "type": "send_modulo_message",
                'ind': message_get['ind'],
                'tipo': message_get['tipo'],
                'data': message_get['data']
            },
        )

        self.send(text_data=json.dumps({
            'type': 'print_turn',
            'ind': ind,
            'data': data
        }))

    def send_genTurno_message(self, message):
        self.send(text_data=json.dumps({
            'type': message['type'],
            'ind': message['ind'],
            'data': message['data']
        }))


class PantallaConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.publ = PublicidadObject()
        self.mod = ModuloObject()

    def connect(self):
        async_to_sync(self.channel_layer.group_add)(
            'pantalla', self.channel_name
        )
        self.accept()

        message = self.publ.get_publicidad("0")
        self.send_pantalla_message(message)

        time.sleep(1.5)

        list_modulos = self.mod.get_turnos_mod()
        self.send_pantalla_message(list_modulos)

    def disconnect(self, close_code):
        self.close(close_code)

    def receive(self, text_data):
        message_r = json.loads(text_data)
        if message_r["tipo"] == "publicidad":
            message = self.publ.get_publicidad(message_r['order'])
            self.send_pantalla_message(message)

    def send_pantalla_message(self, message):
        self.send(text_data=json.dumps({
            'type': message['type'],
            'tipo': message['tipo'],
            'data': message
        }))


class PantallaconsultConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.publ = PublicidadObject()
        self.consult = ConsultorioObject()

    def connect(self):
        async_to_sync(self.channel_layer.group_add)(
            'pantalla_consult', self.channel_name
        )
        self.accept()
        message = self.publ.get_publicidad("0")
        self.send_pantalla_consult_message(message)

        time.sleep(1.5)

        list_consult = self.consult.get_llamado_consult()
        self.send_pantalla_consult_message(list_consult)

    def disconnect(self, close_code):
        self.close(close_code)

    def receive(self, text_data):
        message_r = json.loads(text_data)
        if message_r["tipo"] == "publicidad":
            message = self.publ.get_publicidad(message_r['order'])
            self.send_pantalla_consult_message(message)


    def send_pantalla_consult_message(self, message):
        self.send(text_data=json.dumps({
            'type': message['type'],
            'tipo': message['tipo'],
            'data': message
        }))


class ModuloConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.turno = TurnoObject()
        self.mod = ModuloObject()
        self.audio = AudioObject()

    def connect(self):
        async_to_sync(self.channel_layer.group_add)(
            'modulo', self.channel_name
        )
        self.accept()

        message = self.turno.get_turnos()
        self.send_modulo_message(message)

        list_modulos = self.mod.get_turnos_mod()
        self.send_modulo_message(list_modulos)

    def disconnect(self, close_code):
        '''
        mod = Modulo.objects.filter(usuario__username=self.scope['user']).order_by('-hora')
        if mod:
            mod[0].usuario = None
            mod[0].turno = "----"
            mod[0].hora = None
            mod[0].habilitado = False
            mod[0].save()
            sesion = Session.objects.get(session_key=self.scope['session'].session_key)
            sesion.delete()
        '''
        self.close(close_code)


    def receive(self, text_data):
        message = json.loads(text_data)
        if 'tipo' in message:
            user = self.scope['user'].id
            if message['tipo'] == "llamado":
                resp = self.turno.post_turno(message, user)
                async_to_sync(self.channel_layer.group_send)(
                    "modulo",
                    {
                        'type': "send_modulo_message",
                        'tipo': resp['tipo'],
                        'ind': resp['ind'],
                        'data': resp
                    },
                )

                resp = self.mod.get_turnos_mod()
                async_to_sync(self.channel_layer.group_send)(
                    "modulo",
                    {
                        'type': "send_modulo_message",
                        'tipo': resp['tipo'],
                        'ind': resp['ind'],
                        'data': resp
                    },
                )

                modulos = self.mod.get_turnos_mod()
                async_to_sync(self.channel_layer.group_send)(
                    "pantalla",
                    {
                        "type": "send_pantalla_message",
                        'tipo': modulos['tipo'],
                        'ind': modulos['ind'],
                        'data': modulos['data']
                    },
                )
                time.sleep(1)

    def send_modulo_message(self, message):
        self.send(text_data=json.dumps({
            'type': message['type'],
            'tipo': message['tipo'],
            'ind': message['ind'],
            'data': message['data']
        }))


class LlamadoconsultConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.audio = AudioObject()
        self.consult = ConsultorioObject()

    def connect(self):
        async_to_sync(self.channel_layer.group_add)(
            'llamadoConsult', self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        self.close(close_code)

    def receive(self, text_data):
        while True:
            r_audio = Settings.objects.get(id=1)
            if not r_audio.repr_audio_consult:
                break
            else:
                time.sleep(1)
        r_audio.repr_audio_consult = True
        r_audio.save()

        message_r = json.loads(text_data)
        reg = Reg_consul_digiturno.objects.filter(id_pcte=message_r['id_pcte'],
                                                  consultorio_id=message_r['id_consultorio'],
                                                  fecha__gt=datetime.date.today())
        if reg:
            new = reg[0]
        else:
            new = Reg_consul_digiturno()

        new.id_pcte_id = message_r['id_pcte']
        new.consultorio_id = message_r['id_consultorio']
        new.llamado = message_r['llamado']
        new.u_llamado = message_r['u_llamado']
        new.aviso = False
        new.fecha = datetime.datetime.now()
        new.user_id = message_r['id_user']
        new.save()

        resp = self.audio.get_audio_consult(new.id)
        async_to_sync(self.channel_layer.group_send)(
            "pantalla_consult",
            {
                "type": "send_pantalla_consult_message",
                'ind': 'ind',
                'tipo': "llamado_pcte",
                'data': resp
            },
        )

        time.sleep(7)
        r_audio.repr_audio_consult = False
        r_audio.save()

        resp = self.consult.get_llamado_consult()
        async_to_sync(self.channel_layer.group_send)(
            "pantalla_consult",
            {
                "type": "send_pantalla_consult_message",
                'ind': resp['ind'],
                'tipo': resp['tipo'],
                'data': resp['lista']
            },
        )

    def send_llamadoPcte_message(self, message):
        self.send(text_data=json.dumps({
            'type': message['type'],
            'ind': message['ind'],
            'data': message['data']
        }))


class TurnoObject:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = None

    def get_turnos(self):
        turnos = Registro_digiturno.objects.filter(fecha__gt=datetime.date.today(), llamado=False, aviso=False).order_by('id')
        settings = Settings.objects.get(id=1)
        list_turnos = []
        for t in turnos:
            if settings.letra:
                no_turno = t.servicio.letra + str(t.no_turno)
            else:
                no_turno = str(t.no_turno)

            if t.preferencial:
                no_turno = "P" + no_turno

            list_turnos.append({'id': t.id, 'no_turno': no_turno, 'servicio_id': t.servicio_id,
                                'pcte': t.tp_id.tipo_id + ". " + t.no_id,
                                'fecha': datetime.datetime.strftime(t.fecha, "%d-%m-%Y %H:%M:%S"), 'general': t.general,
                                'servicio_text': t.servicio.servicio})
        if list_turnos:
            message = {
                'type': "get_turno",
                'tipo': "turnos",
                'ind': 1,
                'data': list_turnos
            }
        else:
            message = {
                'type': "get_turno",
                'tipo': "turnos",
                'ind': 0,
                'data': {'aviso': 'No hay turnos por atender'}
            }
        return message

    def post_turno(self, message, user):
        servicio = message['servicio']
        settings = Settings.objects.get(id=1)

        if 'id_turno' in message:
            turno = message['id_turno']
            turnos = Registro_digiturno.objects.filter(id=turno)
        else:
            turnos = Registro_digiturno.objects.filter(llamado=False, aviso=False, general=True,
                                                       fecha__gt=datetime.date.today(),
                                                       servicio__id=servicio).order_by('fecha')[:1]
        mod_pant = Modulo.objects.all()
        for mp in mod_pant:
            if mp.hora != None:
                if mp.habilitado:
                    min = int(int((timezone.now() - mp.hora) / datetime.timedelta(seconds=1)) / 60)
                    if min > 5:
                        mp.turno = "----"
                        mp.save()

        if turnos.exists():
            t = turnos[0]
            if settings.letra:
                turno = str(t.servicio.letra) + str(t.no_turno)
            else:
                turno = str(t.no_turno)

            if t.preferencial:
                turno = "P" + turno

            up_m = Modulo.objects.get(modulo=message['modulo'])
            up_m.turno = turno
            up_m.hora = datetime.datetime.now()
            up_m.save()

            up_reg = turnos[0]
            up_reg.modulo_id = up_m.id
            up_reg.llamado = True
            if 'accion' in message:
                if message['accion'] == "r_llamado":
                    up_reg.r_llamado = True
                else:
                    up_reg.r_llamado = False
            up_reg.aviso = False
            up_reg.fecha_atendido = datetime.datetime.now()
            up_reg.usuario_id = user
            up_reg.save()

            output = {'tipo': "llamado", "ind": 2, "id_turno": str(up_reg.id), 'turno': turno, 'servicio_id': servicio, 'user': user, 'general': up_reg.general}
        else:
            output = {'tipo': "llamado", 'ind': 0, 'data': {'aviso': 'No hay turnos para atender'}}

        return output


class ModuloObject:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = None

    def get_turnos_mod(self):
        modulos = Modulo.objects.filter(habilitado=True).order_by("-hora")
        lista = []
        for m in modulos:
            lista.append({'id': m.id, 'modulo': m.modulo, 'turno': m.turno})

        if lista:
            ind = 2
        else:
            ind = 0
        output = {'ind': ind, 'type': "modulos", 'tipo': "modulos", 'data': lista}

        return output


class ConsultorioObject:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = None

    def get_llamado_consult(self):
        fin = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ini = (datetime.datetime.now() - datetime.timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        consult = Reg_consul_digiturno.objects.filter(fecha__range=(ini, fin), consultorio__habilitado=True,
                                                      llamado=True, aviso=True).order_by("-fecha")[:10]


        lista = []
        for c in consult:
            lista.append({'consultorio': c.consultorio.consultorio, 'piso': c.consultorio.piso,
                          'pcte': str(c.id_pcte.p_nombre + " " + c.id_pcte.s_nombre + " " +
                                  c.id_pcte.p_apellido + " " + c.id_pcte.s_apellido).title()})

        if lista:
            ind = 2
        else:
            ind = 0
        output = {'ind': ind, 'type': "consultorios", 'tipo': "consultorios", 'lista': lista}

        return output


class AudioObject:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.audios = None
        self.ruta = None

    def get_audio_consult(self, reg):
        pcte = Reg_consul_digiturno.objects.filter(id=reg)[:1]
        lista_turnos = []
        ind = 1

        for p in pcte:
            try:
                text = ""
                if p.id_pcte.p_nombre != "" and p.id_pcte.p_apellido != "" and p.id_pcte.sexo != "":
                    if p.u_llamado:
                        text = "Ultimo llamado. "

                    if p.id_pcte.sexo.sexo == "M":
                        text = text + "Señor "
                    else:
                        text = text + "Señora "
                    text = text + p.id_pcte.p_nombre + " " + p.id_pcte.s_nombre + " " + p.id_pcte.p_apellido + " " + p.id_pcte.s_apellido + ", " + \
                           p.consultorio.consultorio + ", piso " + p.consultorio.piso + "."

                out_ruta = str("tmp/" + str(text) + ".mp3").lower()

                if not os.path.exists(os.path.join(SOUNDS_ROOT, out_ruta)):
                    audios = []
                    for t in text.split(","):
                        txt = t.lower()
                        ruta = os.path.join(SOUNDS_ROOT, "grabacion/", txt + ".mp3")
                        if txt != " ":
                            if not os.path.exists(ruta):
                                tts = gTTS(str(txt), lang='es-us')
                                tts.save(ruta)
                            audios.append(ruta)
                    self.audios = audios
                    self.ruta = os.path.join(SOUNDS_ROOT, out_ruta)
                    r = self.mezclar_audios()

                    if r:
                        lista_turnos.append(
                            {'id': p.id, 'consultorio': p.consultorio.consultorio, 'piso': p.consultorio.piso,
                             'pcte': str(p.id_pcte.p_nombre + " " + p.id_pcte.s_nombre + " " + p.id_pcte.p_apellido + " " + p.id_pcte.s_apellido).title(),
                             'audio': "/static/sound/" + out_ruta})
                        p.aviso = True
                        p.save()
                        ind = 2
                    else:
                        ind = 0
                else:
                    lista_turnos.append(
                        {'id': p.id, 'consultorio': p.consultorio.consultorio, 'piso': p.consultorio.piso,
                         'pcte': str(p.id_pcte.p_nombre + " " + p.id_pcte.s_nombre + " " + p.id_pcte.p_apellido + " " + p.id_pcte.s_apellido).title(),
                         'audio': "/static/sound/" + out_ruta,
                         'ult_llamado': p.u_llamado})
                    p.aviso = True
                    p.save()
                    ind = 2
            except:
                ind = 0
                out_ruta = str("static/llamado consultorio.mp3")
                if not os.path.exists(os.path.join(SOUNDS_ROOT, out_ruta)):
                    lista_turnos.append(
                        {'id': p.id, 'consultorio': p.consultorio.consultorio, 'piso': p.consultorio.piso,
                         'pcte': str(p.id_pcte.p_nombre + " " + p.id_pcte.s_nombre + " " + p.id_pcte.p_apellido + " " + p.id_pcte.s_apellido).title(),
                         'audio': "/static/sound/" + out_ruta})
                    p.aviso = True
                    p.save()
                    ind = 2
        return {'ind': ind, 'lista': lista_turnos}

    def mezclar_audios(self):
        try:
            sound = None
            for a in self.audios:
                tmp_sound = AudioSegment.from_mp3(a)
                if sound is None:
                    sound = tmp_sound
                else:
                    sound = sound + tmp_sound

            sound = sound.speedup(1.25, 150, 25)
            sound.export(self.ruta, format="mp3")
            return True
        except:
            return False


class PublicidadObject:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = None

    def get_publicidad(self, order):
        try:
            publ = Publicidad.objects.filter(order=str(int(order) + 1))
            if publ:
                t_publ = publ[0].tipo
                publicidad = publ[0].url
                orden = publ[0].order
            else:
                p = Publicidad.objects.get(order=1)
                t_publ = p[0].tipo
                publicidad = p[0].url
                orden = p.order
        except:
            t_publ = ''
            publicidad = ''
            orden = ''

        return {'type': "publicidad", 'tipo': "publicidad", 'publicidad': publicidad, 'order': orden, 't_publ': t_publ}