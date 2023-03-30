from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from personal.models import *
from sistema.models import *


@login_required(login_url="/unioftalt")
def personal(request):
    if request.method == 'GET':
        tipo_id = Tipo_id.objects.all().order_by('tipo_id')
        area = Area.objects.all().order_by('area')
        cargo = Cargo.objects.all().order_by('cargo')
        sexo = Sexo.objects.all().order_by('sexo')
        dependencia = Dependencia.objects.all().order_by('dependencia')
        personal = Personal.objects.filter(activo=True).order_by('persona__p_nombre')

        if 'aviso' in request.session:
            aviso = request.session['aviso']['aviso']
            ind = request.session['aviso']['ind']
            del request.session['aviso']
        else:
            aviso = 'Bienvenido, Gestión de información de personal'
            ind = 1

        return render(request, 'personal/personal.html',
                      {'personal': personal, 'tipo_id': tipo_id, 'area': area, 'cargo': cargo,
                       'dependencia': dependencia, 'sexo':sexo,
                       'aviso': aviso, 'ind': ind})

    if request.method == 'POST':
        personal = Personal.objects.filter(persona__id=request.POST['id_pcte'])

        if not personal:
            reg = Personal()
            resp = savePersonal(request, reg)
            if resp:
                request.session['aviso'] = {'aviso': 'El empleado ha sido creado exitosamente', 'ind': 2}
            else:
                request.session['aviso'] = {'aviso': 'El empleado no pudo ser registrado', 'ind': 0}
        else:
            request.session['aviso'] = {'aviso': 'El empleado ya existe', 'ind': 0}

        return HttpResponseRedirect('/pers/princ')


def savePersonal(request, reg):
    #try:
    reg.persona_id = request.POST['id_pcte']
    reg.lugar_exp = request.POST['lugar_exp']
    reg.fecha_ingreso = request.POST['f_ingr']
    reg.area_id = request.POST['area']
    reg.cargo_id = request.POST['cargo']
    reg.acudiente = request.POST['acudiente']
    reg.tel_acudiente = request.POST['tel_acudiente']
    reg.eps = request.POST['eps']
    if 'imagen' in request.FILES:
        if request.FILES['imagen'] != "":
            reg.imagen = request.FILES['imagen']
        else:
            reg.imagen = "img/photo/generic.png"
    else:
        reg.imagen = "img/photo/generic.png"
    reg.activo = True
    reg.save()
    return True
    #except:
    #    return False


@login_required(login_url="/unioftalt")
def carnet_personal(request):
    if request.method == 'GET':
        if 'id' in request.GET:
            p = Personal.objects.filter(id=request.GET['id'])
            if personal:
                pers = {'nombre': str(p[0].persona.p_nombre + " " + p[0].persona.s_nombre).upper(),
                        'apellido': str(p[0].persona.p_apellido + " " + p[0].persona.s_apellido).title(),
                        'tipo_id': p[0].persona.tipo_id.tipo_id,
                        'numero_id': p[0].persona.numero_id,
                        'lugar_exp': str(p[0].lugar_exp).title(),
                        'cargo': p[0].cargo.cargo,
                        'imagen': p[0].imagen,
                        'rh': p[0].persona.grupo_s,
                        'acudiente':str(p[0].acudiente).upper(),
                        'tel_acudiente':p[0].tel_acudiente,
                        'eps': str(p[0].eps).upper()}
                plta = 'personal/carnets.html'
            else:
                pers = {}
                plta = 'error404.html'
        else:
            pers = {}
            plta = 'error404.html'
        return render(request, plta, pers)

