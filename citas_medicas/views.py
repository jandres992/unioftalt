import datetime, numpy as np, re, json, locale
from time import sleep
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from citas_medicas.models import *
from sistema.models import *
from sistema.views import save_persona as systemSavePerson

locale.setlocale(locale.LC_ALL, '')


@login_required(login_url="/healthClinic")
def recordatorio_citas(request):
    if request.method == 'GET':
        f_ini = datetime.date.today() + datetime.timedelta(1)
        f_fin = (datetime.date.today() + datetime.timedelta(2))
        cita_h = THistoCitas.objects.using('esalud').filter(id_cita__fecha_ini__range=(f_ini, f_fin), estado=0).order_by('id_cita__id_esp_cita__nom_esp', 'id_cita__fecha_ini')

        if 'aviso' in request.session:
            ind = request.session['aviso']['ind']
            aviso = request.session['aviso']['aviso']
            del request.session['aviso']
        else:
            ind = 1
            aviso = "Envio de registro de cita a usuario"

        data = []
        for c in cita_h:
            data.append(dict(
                fecha_cita=c.id_cita.fecha_ini.strftime("%Y-%m-%d %I:%M %p"),
                identificacion=c.id_cita.id_pcte.tp_id_pcte.t_tp_id + ". " + c.id_cita.id_pcte.num_id_pcte,
                nombre=c.id_cita.id_pcte.pri_nom_pcte + " " + c.id_cita.id_pcte.seg_nom_pcte + " " + c.id_cita.id_pcte.pri_apell_pcte + " " + c.id_cita.id_pcte.seg_apell_pcte,
                entidad=c.id_cita.id_conv_cita.nom_conv,
                especialidad=c.id_cita.id_esp_cita.nom_esp,
                servicio=c.id_cita.cod_ser.nom_ser,
                id_cita=c.id_cita_id
            ))

        return render(request, 'citas_medicas/recordatorio_citas.html', {'aviso': aviso, 'ind': ind, 'citas_h': data})


@login_required(login_url="/healthClinic")
def solicitudes_cita(request):
    if request.method == 'GET':
        tipo_id = Tipo_id.objects.all().order_by('tipo_id')
        if 'l_espera' in request.GET:
            data = Solicitud_cita.objects.filter(atendido=False, descartar=False, l_espera=True).order_by('fecha_s')
            titulo_proceso = "Listado de espera"
        else:
            data = Solicitud_cita.objects.filter(atendido=False, descartar=False, l_espera=False).order_by('fecha_s')
            titulo_proceso = "Solicitudes"

        if 'aviso' in request.session:
            ind = request.session['aviso']['ind']
            aviso = request.session['aviso']['aviso']
            del request.session['aviso']
        else:
            ind = 1
            aviso = "Citas Medicas solicitadas"

        return render(request, 'citas_medicas/solicitud_citas.html',
                      {'aviso': aviso, 'ind': ind, 'data': data, 'tipo_id': tipo_id, 'titulo_proceso': titulo_proceso})


@login_required(login_url="/healthClinic")
def sol_gen_cita(request):
    if request.method == 'GET':
        if 'aviso' in request.session:
            ind = request.session['aviso']['ind']
            aviso = request.session['aviso']['aviso']
            del request.session['aviso']
        else:
            ind = 1
            aviso = "Envio de registro de cita a usuario"

        if 'f_ini' in request.GET and 'f_fin' in request.GET:
            f_ini = datetime.datetime.strptime(request.GET['f_ini'], "%Y-%m-%d")
            f_fin = datetime.datetime.strptime(request.GET['f_fin'], "%Y-%m-%d")
            list_citas = Notificacion_msg_cita.objects.filter(
                fecha__range=(f_ini.strftime("%Y-%m-%d 00:00:00"), f_fin.strftime("%Y-%m-%d 23:59:00"))).order_by('-fecha')
            f_queryset = "{0} al {1}".format(f_ini.strftime("%-d de %B, de %Y"), f_fin.strftime("%-d de %B, de %Y"))
        else:
            list_citas = Notificacion_msg_cita.objects.filter(fecha__range=(
            datetime.date.today().strftime("%Y-%m-%d 00:00:00"),
            datetime.date.today().strftime("%Y-%m-%d 23:59:59"))).order_by('-fecha')
            f_queryset = datetime.date.today().strftime("%-d de %B, de %Y")

        return render(request, 'citas_medicas/solicitud_citas_realizadas.html', {'aviso': aviso, 'ind': ind,
                                                                                 'data': list_citas,
                                                                                 'fecha_queryset': f_queryset})

@login_required(login_url="/healthClinic")
def solicitudes_cita_descartada(request):
    if request.method == 'GET':
        tipo_id = Tipo_id.objects.all().order_by('tipo_id')
        if 'f_ini' and 'f_fin' in request.GET:
            f_ini = datetime.datetime.strptime(request.GET['f_ini'], "%Y-%m-%d")
            f_fin = datetime.datetime.strptime(request.GET['f_fin'], "%Y-%m-%d")

            f_queryset = "{0} al {1}".format(f_ini.strftime("%-d de %B, de %Y"),
                                             f_fin.strftime("%-d de %B, de %Y"))
        else:
            f_ini = datetime.date.today()
            f_fin = datetime.date.today()
            f_queryset = datetime.date.today().strftime("%-d de %B, de %Y")

        data = Solicitud_cita.objects.filter(fecha_aten__range=(f_ini.strftime("%Y-%m-%d 00:00:00"),
                                                                f_fin.strftime("%Y-%m-%d 23:59:59")), descartar=True)

        if 'aviso' in request.session:
            ind = request.session['aviso']['ind']
            aviso = request.session['aviso']['aviso']
            del request.session['aviso']
        else:
            ind = 1
            aviso = "Citas Medicas solicitadas"
        return render(request, 'citas_medicas/solicitud_citas_descartadas.html',
                      {'aviso': aviso, 'ind': ind, 'data': data, 'tipo_id': tipo_id, "fecha_queryset": f_queryset})


@login_required(login_url="/healthClinic")
def form_cita(request):
    if request.method == "GET":
        sexo, tp_id, tramite, servicio, regimen, eps, especialidad, ind, aviso, empresa, departamento = get_data_form(request)
        return render(request, 'citas_medicas/solicitud_cita_form.html', {'aviso': aviso, 'ind': ind, 'tp_id': tp_id, 'tramite': tramite,
                                                                          'regimen': regimen, 'especialidad': especialidad, 'eps': eps,
                                                                          'servicio': servicio, 'sexo':sexo, 'departamento':departamento})

    if request.method == "POST":
        pcte = systemSavePerson(request)
        if pcte['ind'] == 2:
            n = Solicitud_cita()
            post_data_form(request, n, pcte['idPcte'])
        else:
            request.session['aviso'] = {'ind': pcte['ind'],
                                        'aviso': "No se pudo realizar ala operación solicitada, por favor intentelo mas tarde"}

        return HttpResponseRedirect('/cmedicas/form_aten_cita')


def form_cita_ext(request):
    if request.method == "GET":
        sexo, tp_id, tramite, servicio, regimen, eps, especialidad, ind, aviso, empresa, departamento = get_data_form(request)
        return render(request, 'citas_medicas/solicitud_cita_form_ext.html', {'aviso': aviso, 'ind': ind, 'tp_id': tp_id, 'tramite': tramite,
                                                                              'regimen': regimen, 'especialidad': especialidad, 'eps': eps,
                                                                              'servicio': servicio, 'sexo':sexo,
                                                                              'empresa': empresa, 'departamento':departamento})

    if request.method == "POST":
        pcte = systemSavePerson(request)
        if pcte['ind'] == 2:
            n = Solicitud_cita()
            post_data_form(request, n, pcte['idPcte'])
        else:
            request.session['aviso'] = {'ind': pcte['ind'], 'aviso': "No se pudo realizar ala operación solicitada, por favor intentelo mas tarde"}

        return HttpResponseRedirect('/cmedicas/form_aten_cita_ext')


def post_data_form(request, n, pcte):
    if 'tramite' in request.POST:
        n.pcte_id = pcte
        if 'entidad' in request.POST:
            n.eps_id = request.POST['entidad']
        if 'entidad_text' in request.POST:
            n.observacion_eps = request.POST['entidad_text']
        if 'regimen' in request.POST:
            n.regimen_id = request.POST['regimen']
        if 'especialidad' in request.POST:
            n.especialidad_id = request.POST['especialidad']
        if 'no_aut' in request.POST:
            n.no_aut = request.POST['no_aut']
        if 'tramite' in request.POST:
            n.tramite_id = request.POST['tramite']
        if 'servicio' in request.POST:
            n.servicio_id = request.POST['servicio']
        if 'f_cita' in request.POST:
            n.fecha_cita = request.POST['f_cita']
        if 'observacion_g' in request.POST:
            if request.POST['observacion_g'] != "":
                n.observacion_general = request.POST['observacion_g']
        if 'orden' in request.FILES:
            if request.FILES['orden'] != "":
                n.orden_img = request.FILES['orden']
        if 'aut' in request.FILES:
            if request.FILES['aut'] != "":
                n.aut_img = request.FILES['aut']

        n.fecha_s = datetime.datetime.now()
        n.fecha_reg = datetime.datetime.now()
        n.save()
        request.session['aviso'] = {'ind': 2, 'aviso': "La solicitud ha sido realizada, en un periodo no mayor a 72 horas habiles estaremos comunicandonos por los datos de contacto suministrados. Gracias"}
    else:
        request.session['aviso'] = {'ind': 0, 'aviso': "los datos suministrados no son suficientes, por favor actualice la página"}


def get_data_form(request):
    empresa = Empresa.objects.get(id=1)
    sexo = Sexo.objects.all()
    tp_id = Tipo_id.objects.all()
    tramite = Tipo_tramite.objects.filter(visible=True, activo=True).order_by('tramite')
    servicio = Tipo_servicio_cita.objects.all()
    regimen = Regimen_eps.objects.all()
    eps = Eps_ref_cita.objects.all().order_by('orden')
    departamento = Departamento.objects.all().order_by('departamento')
    especialidad = Especialidad_ref_cita.objects.all().order_by('orden')

    if 'aviso' in request.session:
        ind = request.session['aviso']['ind']
        aviso = request.session['aviso']['aviso']
        del request.session['aviso']
    else:
        ind = 1
        aviso = "Bienvenido, diligencie los datos para continuar"
    return sexo, tp_id, tramite, servicio, regimen, eps, especialidad, ind, aviso, empresa, departamento


def data_pcte(request):
    if request.method == "POST":
        if 'tp_id' and 'no_id' in request.POST:
            no_id = request.POST['no_id']
            pcte = Paciente.objects.filter(tipo_id_id=request.POST['tp_id'], numero_id=no_id)

            if pcte:
                p = pcte[0]

                try:
                    if p.municipio_residencia is not None:
                        if p.municipio_residencia != "":
                            departamento = str(p.municipio_residencia.departamento.id)
                            municipio = str(p.municipio_residencia.id)
                        else:
                            departamento = ""
                            municipio = ""
                    else:
                        departamento = ""
                        municipio = ""
                except:
                    departamento = ""
                    municipio = ""

                try:
                    if p.grupo_s is not None:
                        grupo_pcte = re.sub("[-+ ]", "", p.grupo_s)
                        rh_pcte = p.grupo_s[-1]
                    else:
                        grupo_pcte = ""
                        rh_pcte = ""
                except:
                    grupo_pcte = ""
                    rh_pcte = ""

                data = dict(p_nombre=p.p_nombre, s_nombre=p.s_nombre,
                            p_apellido=p.p_apellido, s_apellido=p.s_apellido,
                            f_nacimiento=p.f_nacimiento.strftime("%Y-%m-%d"), telefono=p.telefono_movil,
                            email=p.email, sexo=p.sexo.id, direccion=p.direccion_residencia,
                            departamento=departamento, grupo_pcte=grupo_pcte,
                            rh_pcte=rh_pcte,
                            municipio=municipio)

                ind = 2
                aviso = "Actualice y diligencie los datos solicitados"
            else:
                ind = 1
                data = {}
                aviso = "Por favor diligencie los datos solicitados"
        else:
            ind = 0
            data = {}
            aviso = "Por favor actualice la página, en caso de persistir el porblema comuniquese con el área de " \
                    "sistemas "

        return JsonResponse({'data': data, 'ind': ind, 'aviso': aviso})