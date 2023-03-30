import json, os, datetime, random, glob, time
from asgiref.sync import async_to_sync
from django.db.models import Count
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.contrib import auth
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from sistema.models import *
from turno_digital.models import *
from unioftalt.settings import BASE_DIR, SOUNDS_ROOT
from turno_digital.consumers import TurnoObject as consumer_turno
from channels.layers import get_channel_layer
from gtts import gTTS
from moviepy.editor import concatenate_audioclips, AudioFileClip


def login_dig(request):
    request.session['empresa'] = Empresa.objects.filter(id=1).values()[0]
    modulo = Modulo.objects.all().order_by('modulo')
    if request.method == 'GET':
        if 'aviso' in request.session:
            ind = request.session['aviso']['ind']
            aviso = request.session['aviso']['aviso']
            del request.session['aviso']
        else:
            ind = 1
            aviso = 'Bienvenido, por favor ingrese su usuario y contraseña para continuar'
        return render(request, 'digiturno/login.html',
                      {'ind': ind, 'aviso': aviso, 'modulos': modulo})

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        acceso = auth.authenticate(username=username, password=password)

        if acceso is not None:
            auth_login(request, acceso)
            request.session['modulo'] = request.POST['modulo']
            modulo = Modulo.objects.get(modulo=request.POST['modulo'])

            file = glob.glob(str(BASE_DIR) + '/static/img/avatar/' + request.user.username + ".png", recursive=True)
            if file:
                avatar = '/static/img/avatar/' + request.user.username + ".png"
            else:
                avatar = '/static/img/avatar/logo.png'
            if 'avatar' in request.session:
                del request.session['avatar']
            request.session['avatar'] = avatar

            if not modulo.habilitado or modulo.usuario_id == request.user.id:
                modulo.usuario_id = request.user.id
                modulo.turno = "----"
                modulo.habilitado = True
                modulo.save()
                return redirect(digiturno_dig)
            else:
                request.session['aviso'] = {
                    'aviso': 'El módulo seleccionado ya esta habilitado, seleccione otro módulo disponible',
                    'ind': 0}
                return redirect(login_dig)
        else:
            request.session['aviso'] = {'aviso': "Usuario o contraseña invalido", 'ind': 0}
            return redirect(login_dig)


def login_consult_dig(request):
    request.session['empresa'] = Empresa.objects.filter(id=1).values()[0]
    consultorio = Consultorio.objects.all().order_by('consultorio')
    if request.method == 'GET':
        if 'aviso' in request.session:
            ind = request.session['aviso']['ind']
            aviso = request.session['aviso']['aviso']
            del request.session['aviso']
        else:
            ind = 1
            aviso = 'Bienvenido, por favor ingrese su usuario y contraseña para continuar'
        return render(request, 'digiturno/login_consult.html',
                      {'ind': ind, 'aviso': aviso, 'consultorio': consultorio})

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        acceso = auth.authenticate(username=username, password=password)

        if acceso is not None:
            auth_login(request, acceso)
            consultorio = Consultorio.objects.get(id=request.POST['consultorio'])
            request.session['consultorio'] = consultorio.consultorio

            if not consultorio.habilitado or consultorio.usuario_id == request.user.id:
                consultorio.habilitado = True
                consultorio.usuario = request.user
                consultorio.save()

                file = glob.glob(str(BASE_DIR) + '/static/img/avatar/' + request.user.username + ".png", recursive=True)
                if file:
                    avatar = '/static/img/avatar/' + request.user.username + ".png"
                else:
                    avatar = '/static/img/avatar/logo.png'
                if 'avatar' in request.session:
                    del request.session['avatar']
                request.session['avatar'] = avatar

                return HttpResponseRedirect('/digiturno/llamadoConsult')
            else:
                request.session['aviso'] = {
                    'aviso': 'El consultorio ya esta habilitado, comuniquese con el área de sistemas', 'ind': 0}
                return redirect(login_consult_dig)
        else:
            request.session['aviso'] = {'aviso': "Usuario o contraseña invalido", 'ind': 0}
            return redirect(login_dig)


@login_required(login_url="/digiturno")
def logout_dig(request):
    if 'modulo' in request.session:
        mod = Modulo.objects.get(modulo=request.session['modulo'])
        mod.usuario = None
        mod.habilitado = False
        mod.turno = "----"
        mod.save()
        del request.session['modulo']
    auth_logout(request)
    return HttpResponseRedirect('/')


@login_required(login_url="/digiturno")
def reportes_dig(request):
    if request.method == 'GET':
        ini = datetime.date.today().strftime("%Y-%m-%d 00:00:00")
        fin = datetime.date.today().strftime("%Y-%m-%d 23:59:59")
        registros = Registro_digiturno.objects.filter(fecha__range=(ini, fin), llamado=True)
        resultados = registros.filter(usuario_id=request.user.id)
        t_resultados = registros.values('servicio__servicio').annotate(dcount=Count('servicio_id')).order_by()
        list_result = {}
        if resultados:
            for r in resultados:
                if r.atencion:
                    turno_a = 1
                    turno_r = 0
                else:
                    turno_a = 0
                    turno_r = 1

                if not r.servicio.servicio in list_result:
                    list_result[r.servicio.servicio] = {'t_aten': turno_a, 't_rech': turno_r}
                else:
                    list_result[r.servicio.servicio]['t_aten'] = list_result[r.servicio.servicio]['t_aten'] + turno_a
                    list_result[r.servicio.servicio]['t_rech'] = list_result[r.servicio.servicio]['t_rech'] + turno_r

            for s in t_resultados:
                if s['servicio__servicio'] in list_result:
                    parcial = int(list_result[s['servicio__servicio']]['t_aten']) + int(
                        list_result[s['servicio__servicio']]['t_rech'])
                    list_result[s['servicio__servicio']]['total'] = str(s['dcount'])
                    if parcial != 0:
                        list_result[s['servicio__servicio']]['porcentaje'] = "{0:.2f}".format(
                            float((parcial * 100) / int(s['dcount'])))
                    else:
                        list_result[s['servicio__servicio']]['porcentaje'] = 0
            ind = 2
        else:
            ind = 0

        data = {'ind': ind, 'datos': list_result}
        return JsonResponse(data)


@login_required(login_url="/digiturno/logconsult")
def llamado_consult_dig(request):
    if request.method == 'GET':
        if 'consultorio' in request.session:
            tipo_id = Tipo_id.objects.all().order_by('tipo_id')
            if 'aviso' in request.session:
                ind = request.session['aviso']['ind']
                aviso = request.session['aviso']['aviso']
            else:
                ind = 1
                aviso = ('Bienvenido, ' + request.user.first_name + ' ' + request.user.last_name).title()

            return render(request, 'digiturno/llamado_consultorio.html', {'ind': ind, 'aviso': aviso,'tipo_id':tipo_id})
        else:
            request.session['aviso'] = {'ind': 0,
                                        'aviso': "Debe loguearse primero en llamado de consultorio para usar esta función especial"}
            return redirect(login_consult_dig)


def pantalla_dig(request):
    if request.method == "GET":
        empresa = Empresa.objects.get(id=1)
        modulos = Modulo.objects.filter(habilitado=True).order_by('modulo')

        return render(request, 'digiturno/pantalla.html', {'modulos': modulos, 'empresa': empresa})


def pantalla_consult_dig(request):
    if request.method == "GET":
        empresa = Empresa.objects.get(id=1)
        return render(request, 'digiturno/pantalla_consult.html', {'empresa': empresa})

    if request.method == "POST":
        pcte = Reg_consul_digiturno.objects.filter(aviso=False, llamado=True,
                                                   fecha__gt=datetime.date.today()).order_by('id')[:1]

        lista_turnos = []
        ind = 1
        # tts = gTTS(str("Llamado de consultorio"), lang='es-us')
        # tts.save(os.path.join(SOUNDS_ROOT, "llamado consultorio.mp3"))
        for p in pcte:
            try:
                text = ""
                if p.id_pcte.p_nombre != "" and p.id_pcte.p_apellido != "" and p.id_pcte.sexo != "":
                    if p.u_llamado:
                        text = "Ultimo llamado, "

                    if p.id_pcte.sexo.sexo == "M":
                        text = "Señor "
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
                    r = mezclar_audios(audios, os.path.join(SOUNDS_ROOT, out_ruta))

                    if r:
                        lista_turnos.append(
                            {'id': p.id, 'consultorio': p.consultorio.consultorio, 'piso': p.consultorio.piso,
                             'pcte': str(
                                 p.id_pcte.p_nombre + " " + p.id_pcte.s_nombre + " " + p.id_pcte.p_apellido + " " + p.id_pcte.s_apellido).title(),
                             'audio': "/static/sound/" + out_ruta})
                        p.aviso = True
                        p.save()
                        ind = 2
                    else:
                        ind = 0
                else:
                    lista_turnos.append(
                        {'id': p.id, 'consultorio': p.consultorio.consultorio, 'piso': p.consultorio.piso,
                         'pcte': str(
                             p.id_pcte.p_nombre + " " + p.id_pcte.s_nombre + " " + p.id_pcte.p_apellido + " " + p.id_pcte.s_apellido).title(),
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
                         'pcte': str(
                             p.id_pcte.p_nombre + " " + p.id_pcte.s_nombre + " " + p.id_pcte.p_apellido + " " + p.id_pcte.s_apellido).title(),
                         'audio': "/static/sound/" + out_ruta})
                    p.aviso = True
                    p.save()
                    ind = 2

        return JsonResponse({'ind': ind, 'lista': lista_turnos})


@login_required(login_url="/digiturno")
def digiturno_dig(request):
    if request.method == 'GET':
        empresa = Empresa.objects.get(id=1)
        servicios_list = []
        servicios = Servicio.objects.all().order_by('id')
        tipo_id = Tipo_id.objects.all().order_by('tipo_id')
        sexo = Sexo.objects.all().order_by('descripcion')
        for s in servicios:
            for g in request.user.groups.all():
                if s.servicio == g.name:
                    servicios_list.append({'id': s.id, 'servicio': s.servicio})

        modulo = ""
        if 'modulo' in request.session:
            modulo = request.session['modulo']

        if modulo == "":
            return redirect(logout_dig)
        else:
            return render(request, 'digiturno/modulo.html',
                          {'servicios': servicios_list, 'modulo': modulo, 'empresa': empresa,
                           'tipo_id': tipo_id, 'sexo': sexo})


def llamado_turno_dig(request):  # si se usa ok
    if request.method == 'GET':
        settings = Settings.objects.get(id=1)
        digiturno = Registro_digiturno.objects.filter(aviso=False, llamado=True,
                                                      fecha__gt=datetime.date.today()).order_by('id')
        lista_turnos = []
        for d in digiturno:
            pcte_txt = ""
            try:
                text_r = ""

                if settings.letra:
                    letra = d.servicio.letra
                    letra_text = d.servicio.letra
                else:
                    letra = ""
                    letra_text = ""

                if d.preferencial:
                    t_turno = "PREFERENCIAL"
                    letra = "P," + letra
                    letra_text = "P" + d.servicio.letra
                else:
                    t_turno = "GENERAL"

                if d.r_llamado:
                    if settings.datos_pcte:
                        pcte = Paciente.objects.filter(tipo_id=d.tp_id_id, numero_id=d.no_id)
                        if pcte:
                            pac = pcte[0]
                            if pac.p_nombre != "" and pac.p_apellido != "" and pac.sexo != "":
                                if pac.sexo.sexo == "M":
                                    text_r = "Señor "
                                else:
                                    text_r = text_r + "Señora "

                                pcte_txt = str(
                                    pac.p_nombre + " " + pac.s_nombre + " " + pac.p_apellido + " " + pac.s_apellido).upper()
                                text_r = text_r + pac.p_nombre + " " + pac.p_apellido + ", "

                    if text_r == "":
                        text_r = str(letra) + "-" + str(d.no_turno)

                    out_ruta = str("tmp/" + text_r + "-" + str(d.modulo.modulo) + ".mp3").lower()
                else:
                    out_ruta = str(
                        "tmp/" + str(letra) + "-" + str(d.no_turno) + "-" + str(d.modulo.modulo) + ".mp3").lower()

                if not os.path.exists(os.path.join(SOUNDS_ROOT, out_ruta)):
                    if text_r == "":
                        text = "turno "
                        if d.preferencial:
                            text = text + "preferencial, "
                        text = text + letra + "," + str(d.no_turno) + ","
                    else:
                        text = text_r

                    text = text + "módulo " + str(d.modulo.modulo) + "."

                    audios = []
                    for t in text.split(","):
                        txt = t.lower()
                        ruta = os.path.join(SOUNDS_ROOT, "grabacion/", txt + ".mp3")
                        if txt != " ":
                            if not os.path.exists(ruta):
                                tts = gTTS(str(txt), lang='es-us')
                                tts.save(ruta)
                            audios.append(ruta)
                    r = mezclar_audios(audios, os.path.join(SOUNDS_ROOT, out_ruta))

                    if r:
                        lista_turnos.append(
                            {'id': d.id, 'servicio': d.servicio.servicio, 't_turno': t_turno, 'modulo': d.modulo.modulo,
                             'pcte': pcte_txt,
                             'turno': letra_text + str(d.no_turno), 'audio': "/static/sound/" + out_ruta})
                        d.aviso = True
                        d.save()
                        ind = 2
                    else:
                        ind = 0
                else:
                    lista_turnos.append(
                        {'id': d.id, 'servicio': d.servicio.servicio, 't_turno': t_turno, 'modulo': d.modulo.modulo,
                         'pcte': pcte_txt,
                         'turno': letra_text + str(d.no_turno), 'audio': "/static/sound/" + out_ruta})
                    d.aviso = True
                    d.save()
                    ind = 2
            except:
                if settings.letra:
                    letra = d.servicio.letra
                else:
                    letra = ""

                if d.preferencial:
                    t_turno = "PREFERENCIAL"
                    letra = "P," + letra
                    letra_text = "P," + letra
                else:
                    letra_text = letra
                    t_turno = "GENERAL"

                out_ruta = str(
                    "tmp/" + str(letra) + "-" + str(d.no_turno) + "-" + str(d.modulo.modulo) + ".mp3").lower()

                if not os.path.exists(os.path.join(SOUNDS_ROOT, out_ruta)):
                    audios = []
                    if not d.preferencial:
                        audios.append(os.path.join(SOUNDS_ROOT, "static/turno.mp3"))
                    else:
                        audios.append(os.path.join(SOUNDS_ROOT, "static/turno preferencial.mp3"))
                        audios.append(os.path.join(SOUNDS_ROOT, "static/letras/p.mp3"))

                    if settings.letra:
                        audios.append(
                            os.path.join(SOUNDS_ROOT, "static/letras/" + str(d.servicio.letra).lower() + ".mp3"))

                    audios.append(os.path.join(SOUNDS_ROOT, "static/numeros/" + str(d.no_turno) + ".mp3"))
                    if os.path.exists(
                            os.path.join(SOUNDS_ROOT, "static/modulos/módulo " + str(d.modulo.modulo) + ".mp3")):
                        audios.append(
                            os.path.join(SOUNDS_ROOT, "static/modulos/módulo " + str(d.modulo.modulo) + ".mp3"))
                    else:
                        audios.append(os.path.join(SOUNDS_ROOT, "static/módulo " + str(d.modulo.modulo) + ".mp3"))
                        audios.append(os.path.join(SOUNDS_ROOT, "static/numeros/" + str(d.modulo.modulo) + ".mp3"))

                    r = mezclar_audios(audios, os.path.join(SOUNDS_ROOT, out_ruta))

                    if r:
                        lista_turnos.append(
                            {'id': d.id, 'servicio': d.servicio.servicio, 't_turno': t_turno, 'modulo': d.modulo.modulo,
                             'pcte': pcte_txt,
                             'turno': letra_text + str(d.no_turno), 'audio': "/static/sound/" + out_ruta})
                        d.aviso = True
                        d.save()
                        ind = 2
                    else:
                        ind = 0
                else:
                    lista_turnos.append(
                        {'id': d.id, 'servicio': d.servicio.servicio, 't_turno': t_turno, 'modulo': d.modulo.modulo,
                         'pcte': pcte_txt,
                         'turno': letra_text + str(d.no_turno), 'audio': "/static/sound/" + out_ruta})
                    d.aviso = True
                    d.save()
                    ind = 2

            cont = 0
            while True:
                r_audio = Settings.objects.get(id=1)
                if not r_audio.repr_audio_turno:
                    r_audio.repr_audio_turno = True
                    r_audio.save()

                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        "pantalla",
                        {
                            "type": "send_pantalla_message",
                            'tipo': "proyeccion",
                            'ind': ind,
                            'lista': lista_turnos
                        },
                    )

                    time.sleep(5.5)
                    r_audio.repr_audio_turno = False
                    r_audio.save()
                    break
                else:
                    cont += 1
                    time.sleep(1)
                    if cont > 5:
                        r_audio.repr_audio_turno = False
                        r_audio.save()

        return JsonResponse({'data': "ok"})


def mezclar_audios(audios, ruta):
    try:
        clips = [AudioFileClip(c) for c in audios]
        final_clip = concatenate_audioclips(clips)
        final_clip.write_audiofile(ruta)
        return True
    except:
        return False


@login_required(login_url="/digiturno")
def asignar_turno_preferencial(request):
    if request.method == "GET":
        id_turno = request.GET['id_turno']
        modulo = request.GET['modulo']
        turno = Registro_digiturno.objects.get(id=id_turno)
        update = Modulo.objects.get(modulo=modulo)

        update_modulo = update
        update_modulo.turno = turno.no_turno
        update_modulo.hora = datetime.datetime.now()
        update_modulo.save()

        updated = turno
        updated.modulo = update
        updated.llamado = True
        updated.atencion = True
        updated.fecha_atendido = timezone.now()
        updated.usuario = request.user
        updated.save()

        id_turno = updated.id
        no_turno = updated.no_turno
        output = {'ind': "ok", 'id_turno': id_turno, 'no_turno': no_turno}

        return HttpResponse(json.dumps(output), content_type="application/json")


def consulta_modulo(request):
    if request.method == "GET":
        modulos = Modulo.objects.filter(habilitado=True).order_by("-hora")
        lista = []
        for m in modulos:
            lista.append({'id': m.id, 'modulo': m.modulo, 'turno': m.turno})
        output = {'ind': 2, 'lista': lista}

        return JsonResponse(output)


@login_required(login_url="/digiturno")
def consulta_turno_dig(request):  # reemplazada
    if request.method == "GET":
        servicio = Servicio.objects.all()
        turnos = Registro_digiturno.objects.filter(fecha__gt=datetime.date.today()).order_by('id', 'fecha')
        lista = []
        conteo = []
        for s in servicio:
            conteo.append(
                {'servicio': s.id, 'valor': len(turnos.filter(llamado=False, servicio_id=s.id, general=True))})

        for t in turnos:
            dic = {'id': t.id, 'turno': t.no_turno, 'fecha': datetime.datetime.strftime(t.fecha, "%I:%M %p"),
                   'servicio': t.servicio.id,
                   'letra': t.servicio.letra, 'llamado': t.llamado, 'general': t.general,
                   'preferencial': t.preferencial,
                   'servicio_text': t.servicio.servicio,
                   'pcte': t.tp_id.tipo_id + ' - ' + t.no_id}
            lista.append(dic)

        output = {'lista': lista, 'conteo': conteo}
        return JsonResponse(output)


@login_required(login_url="/digiturno")
def admin_dig(request):
    if request.user.groups.filter(name="digiturno reporte diario").exists():
        if request.method == 'GET':
            empresa = Empresa.objects.get(id=1)
            query = None
            servicios = Registro_digiturno.objects.filter(llamado=False, fecha__gt=datetime.date.today())
            fecha_turnos = None

            if 'f_ini' and 'f_fin' in request.GET:
                if request.GET['f_ini'] != datetime.date.today().strftime("%Y-%m-%d"):
                    query = Registro_digiturno.objects.filter(fecha__range=(request.GET['f_ini'] + " 00:00:00.000",
                                                                            request.GET[
                                                                                'f_fin'] + " 23:59:59.000")).order_by(
                        'fecha')
                    fecha_turnos = " desde el {}, al {}".format(
                        datetime.datetime.strptime(request.GET['f_ini'], "%Y-%m-%d").strftime("%-d de %B de %Y"),
                        datetime.datetime.strptime(request.GET['f_fin'], "%Y-%m-%d").strftime("%-d de %B de %Y"))
                    r = True
                else:
                    r = False
            else:
                r = False

            if not r:
                fecha = datetime.date.today()
                query = Registro_digiturno.objects.filter(fecha__gt=fecha).order_by('fecha')
                fecha_turnos = fecha.strftime("%d de %B, de %Y")

            atenciones = query.filter(llamado=True, aviso=True).exclude(usuario=None).order_by('fecha')

            if 'aviso' in request.session:
                ind = request.session['aviso']['ind']
                aviso = request.session['aviso']['aviso']
            else:
                ind = 1
                aviso = ('Bienvenido, ' + request.user.first_name + ' ' + request.user.last_name).title()

            lista_colors = ['primary', 'success', 'info', 'secondary', 'warning', 'danger', 'dark']
            lista_servicios = dict()

            ind_t = 0
            for s in servicios:
                if not s.servicio.servicio in lista_servicios:
                    lista_servicios[s.servicio.servicio] = {'valor': 1, 'color': random.choice(lista_colors),
                                                            'icon': s.servicio.icon,
                                                            'fecha': s.fecha.strftime("%I:%M %p")}
                else:
                    lista_servicios[s.servicio.servicio]['valor'] = int(
                        lista_servicios[s.servicio.servicio]['valor']) + 1
                ind_t = 1
            modulos = Servicio.objects.filter(habilitado=True).order_by('servicio')

            lista_atenciones = {}
            for a in atenciones:
                at_vl = 1
                re_vl = 0
                if not a.usuario.username in lista_atenciones:
                    lista_atenciones[a.usuario.username] = {}
                    for m in modulos:
                        lista_atenciones[a.usuario.username][m.servicio] = {'rechazado': 0, 'atendido': 0}
                lista_atenciones[a.usuario.username][a.servicio.servicio]['rechazado'] += re_vl
                lista_atenciones[a.usuario.username][a.servicio.servicio]['atendido'] += at_vl

            return render(request, 'digiturno/funcionario.html',
                          {'ind_t': ind_t, 'aviso': aviso, 'ind': ind, 'empresa': empresa,
                           'servicios': lista_servicios, 'atenciones': lista_atenciones,
                           'modulos': modulos, 'fecha_turnos': fecha_turnos})
        else:
            return redirect(login_dig)
    else:
        return HttpResponseRedirect('/unioftalt/menu')


def generacion_turno_dig(request):
    empresa = Empresa.objects.get(id=1)
    settings = Settings.objects.get(id=1)
    if request.method == 'GET':
        if 'aviso' in request.session:
            aviso = request.session['aviso']['aviso']
            ind = request.session['aviso']['ind']
            del request.session['aviso']
        else:
            aviso = "Bienvenido"
            ind = 1

        tipo_id = Tipo_id.objects.filter(estado=True).order_by('tipo_id')
        servicios = Servicio.objects.all().order_by('id')
        return render(request, 'digiturno/turno.html',
                      {'aviso': aviso, 'ind': ind, 'servicios': servicios, 'empresa': empresa, 'conf': settings,
                       'tipo_id': tipo_id})

    if request.method == 'POST':
        tp_id = request.POST['tp_id']
        no_id = request.POST['no_id']
        tel = request.POST['tel']
        tp_turno = request.POST['tp_turno']
        servicio_id = request.POST['servicio']

        servicio_act = Servicio.objects.get(id=servicio_id)
        horario_fin = servicio_act.horario_fin
        actual = timezone.now().time()

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
            new_digiturno.tel = tel
            new_digiturno.no_turno = new_turno
            new_digiturno.fecha = datetime.datetime.now()
            new_digiturno.servicio_id = servicio_id
            new_digiturno.aviso = False
            new_digiturno.llamado = False
            new_digiturno.atencion = False
            if tp_turno == "general":
                tipo_turno_text = "TURNO GENERAL:"
                new_digiturno.general = True
                new_digiturno.preferencial = False
            else:
                tipo_turno_text = "TURNO PREFERENCIAL:"
                new_digiturno.general = False
                new_digiturno.preferencial = True
            new_digiturno.save()

            act_turno = turno
            act_turno.turno = new_turno
            act_turno.save()

            request.session['ticket_turno'] = new_digiturno.id
            request.session['aviso'] = {'aviso': "El turno ha sido generado", 'ind': 2}

            if settings.letra:
                turno = str(new_digiturno.servicio.letra) + str(new_digiturno.no_turno)
            else:
                turno = str(new_digiturno.no_turno)

            if new_digiturno.preferencial:
                turno = "P" + turno

            output = {'ind': 2,
                      't_persona': new_digiturno.tp_id.tipo_id + " - " + str(new_digiturno.no_id),
                      't_turno': turno,
                      't_rango': str(rango_ini) + ' - ' + str(rango_fin),
                      't_fecha': new_digiturno.fecha.strftime("%d-%m-%Y %I:%M %p"),
                      't_servicio': servicio_act.servicio.upper(),
                      't_tp_turno': tipo_turno_text}

            message = consumer_turno.get_turnos(request)
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "llamado",
                {
                    "type": "send_consumer_message",
                    'ind': message['ind'],
                    'data': message['data']
                },
            )
        else:
            output = {'ind': 1, 'aviso': "Fuera de Horario"}
        # except:
        #    request.session['aviso'] = {'aviso': "El turno no ha podido ser generado", 'ind': 0}
        #    output = {'ind': 0, 'aviso': "Error de sistema, actualice la página"}

        return JsonResponse(output)


def ticket_turno_dig(request):
    empresa = Empresa.objects.get(id=1)
    settings = Settings.objects.get(id=1)
    if 'ticket_turno' in request.session or 'id_turno' in request.GET:
        if 'id_turno' in request.GET:
            turno = Registro_digiturno.objects.get(id=request.GET['id_turno'])
        else:
            turno = Registro_digiturno.objects.get(id=request.session['ticket_turno'])
            del request.session['ticket_turno']

        if settings.letra:
            t = str(turno.servicio.letra) + str(turno.no_turno)
        else:
            t = str(turno.no_turno)

        if turno.preferencial:
            t = "P" + t

        ticket_turno = t
        ticket_rango = str(turno.servicio.rango_ini) + ' - ' + str(turno.servicio.rango_fin)
        ticket_fecha = turno.fecha.strftime("%d-%m-%Y %I:%M %p")
        ticket_servicio = turno.servicio.servicio.upper()
        if turno.general == False:
            ticket_tp_turno = "TURNO PREFERENCIAL"
        else:
            ticket_tp_turno = "TURNO GENERAL"

        return render(request, 'digiturno/ticket_turno.html', {'empresa': empresa,
                                                               'ticket_persona': turno.tp_id.tipo_id + ' - ' + str(
                                                                   turno.no_id),
                                                               'ticket_turno': ticket_turno,
                                                               'ticket_rango': ticket_rango,
                                                               'ticket_fecha': ticket_fecha,
                                                               'ticket_servicio': ticket_servicio,
                                                               'ticket_tp_turno': ticket_tp_turno})
    else:
        return redirect(generacion_turno_dig)
