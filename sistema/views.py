import glob, re
from django.contrib import auth
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.hashers import make_password
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from sistema.models import *
from unioftalt.settings import BASE_DIR
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from turno_digital.models import *


def index(request):
    if request.method == 'GET':
        request.session['empresa'] = Empresa.objects.filter(id=1).values()[0]
        return render(request, 'general/index.html', {})


def login(request):
    if request.method == 'GET':
        request.session['empresa'] = Empresa.objects.filter(id=1).values()[0]

        if 'aviso' in request.session:
            ind = request.session['aviso']['ind']
            aviso = request.session['aviso']['aviso']
            del request.session['aviso']
        else:
            ind = 1
            aviso = 'Bienvenido, por favor ingrese su usuario y contraseña para continuar'
        return render(request, 'general/login.html', {'ind': ind, 'aviso': aviso})

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        acceso = auth.authenticate(username=username, password=password)

        if acceso is not None:
            file = glob.glob(str(BASE_DIR) + '/static/img/avatar/' + request.user.username + ".png", recursive=True)
            if file:
                avatar = '/static/img/avatar/' + request.user.username + ".png"
            else:
                avatar = '/static/img/avatar/logo.png'
            if 'avatar' in request.session:
                del request.session['avatar']
            request.session['avatar'] = avatar

            auth_login(request, acceso)

            return redirect(menu)
        else:
            request.session['aviso'] = {'aviso': "Usuario o contraseña invalido", 'ind': 0}
            return redirect(login)


@login_required(login_url="/unioftalt")
def logout(request):
    if request.method == 'GET':
        auth_logout(request)
        return HttpResponseRedirect('/')


@login_required(login_url="/unioftalt")
def menu(request):
    if request.method == 'GET':
        empresa = Empresa.objects.get(id=1)
        if 'aviso' in request.session:
            ind = request.session['aviso']['ind']
            aviso = request.session['aviso']['aviso']
            del request.session['aviso']
        else:
            ind = 1
            aviso = 'Bienvenido, por favor ingrese su usuario y contraseña para continuar'
        return render(request, 'general/menu.html', {'ind': ind, 'aviso': aviso, 'empresa': empresa})


@login_required(login_url="/unioftalt")
def busq_persona(request):
    if request.method == 'GET':
        t_id = request.GET['tp_id_pcte']
        no_id = request.GET['no_id_pcte']
        pcte = Paciente.objects.filter(numero_id=no_id, tipo_id=t_id)

        if pcte:
            paciente = pcte[0]
            if paciente.municipio_residencia is not None:
                departamento = paciente.municipio_residencia.departamento_id
                municipio = {'id':paciente.municipio_residencia.id, 'municipio':paciente.municipio_residencia.municipio}
            else:
                municipio = ""
                departamento = ""

            if paciente.grupo_s is not None:
                grupo = re.sub("[-+ ]", "", paciente.grupo_s)
                rh = paciente.grupo_s[-1]
            else:
                grupo = ""
                rh = ""

            output = {'ind': 2,
                      'paciente': {
                          'id': paciente.id,
                          'p_nombre': str(paciente.p_nombre).title(),
                          's_nombre': str(paciente.s_nombre).title(),
                          'p_apellido': str(paciente.p_apellido).title(),
                          's_apellido': str(paciente.s_apellido).title(),
                          'f_nacimiento': paciente.f_nacimiento.strftime("%Y-%m-%d"),
                          'documento': paciente.tipo_id.tipo_id + ". " + paciente.numero_id,
                          'tel': paciente.telefono_movil,
                          'departamento': departamento,
                          'municipio': municipio,
                          'sexo': paciente.sexo_id,
                          'grupo_pcte': grupo,
                          'rh_pcte': rh,
                          'other_tel': paciente.telefono_fijo,
                          'dir': paciente.direccion_residencia,
                          'email': paciente.email
                        }
                      }
        else:
            output = {'ind': 0}
        return JsonResponse(output)



def save_persona(request):
    if request.POST['tp_id'] and request.POST['no_id'] != "":
        pcte = Paciente.objects.filter(tipo_id_id=request.POST['tp_id'], numero_id=request.POST['no_id'])
        if not pcte:
            new = Paciente()
        else:
            new = pcte[0]

        if 'tp_id' and 'no_id' in request.POST:
            try:
                id_pcte = save_pcte(request, new)
                output = {'idPcte': id_pcte, 'ind': 2}
            except:
                output = {'ind': 0}
        else:
            output = {'ind': 0}
    else:
        output = {'ind': 0}

    return output


def save_pcte(request, new_pcte):
    new_pcte.tipo_id_id = request.POST['tp_id']
    new_pcte.numero_id = request.POST['no_id']
    if 'p_nombre' in request.POST:
        if request.POST['p_nombre'] != "":
            new_pcte.p_nombre = str(request.POST['p_nombre']).upper()
    if 's_nombre' in request.POST:
        if request.POST['s_nombre'] != "":
            new_pcte.s_nombre = str(request.POST['s_nombre']).upper()
    if 'p_apellido' in request.POST:
        if request.POST['p_apellido'] != "":
            new_pcte.p_apellido = str(request.POST['p_apellido']).upper()
    if 's_apellido' in request.POST:
        if request.POST['s_apellido'] != "":
            new_pcte.s_apellido = str(request.POST['s_apellido']).upper()
    if 'f_nacimiento' in request.POST:
        if request.POST['f_nacimiento'] != "":
            new_pcte.f_nacimiento = request.POST['f_nacimiento']
    if 'sexo' in request.POST:
        if request.POST['sexo'] != "":
            new_pcte.sexo_id = request.POST['sexo']
    if 'municipio' in request.POST:
        if request.POST['municipio'] != "":
            new_pcte.municipio_residencia_id = request.POST['municipio']
    if 'dir_pcte' in request.POST:
        if request.POST['dir_pcte'] != "":
            new_pcte.direccion_residencia = str(request.POST['dir_pcte']).upper()
    if 'other_tel_pcte' in request.POST:
        if request.POST['other_tel_pcte'] != "":
            new_pcte.telefono_fijo = request.POST['other_tel_pcte'][0:10]
    new_pcte.telefono_movil = request.POST['tel_pcte'][0:10]
    if 'grupo_pcte' and 'rh_pcte' in request.POST:
        if request.POST['grupo_pcte'] != "" and request.POST['rh_pcte'] != "":
            new_pcte.grupo_s = request.POST['grupo_pcte'] + " " + request.POST['rh_pcte']
    if 'email_pcte' in request.POST:
        if request.POST['email_pcte'] != "":
            new_pcte.email = str(request.POST['email_pcte']).lower()
    if 'envio_inf' in request.POST:
        if request.POST['envio_inf'] != "":
            if request.POST['envio_inf'] == "NO":
                new_pcte.envio_inf = False
    if 'observacion_pcte' in request.POST:
        if request.POST['observacion_pcte'] != "":
            new_pcte.observacion = request.POST['observacion_pcte']
    new_pcte.save()

    return new_pcte.id


def obtener_municipio(request):
    if request.method == 'POST':
        departamento = request.POST['departamento']
        if departamento != "":
            lista = Municipio.objects.filter(departamento__id=departamento).order_by('municipio')
            municipio = []
            for l in lista:
                municipio.append({'id': l.id, 'municipio': l.municipio})

            return JsonResponse({'ind': 2, 'municipio': municipio})
        else:
            return JsonResponse({'ind': 0})


@login_required(login_url="/healthClinic")
def usuario_sistema(request):
    if request.method == "GET":
        if 'aviso' in request.session:
            ind = request.session['aviso']['ind']
            aviso = request.session['aviso']['aviso']
            del request.session['aviso']
        else:
            ind = 1
            aviso = "Bienvenido, diligencie los datos para continuar"

        grupos = Group.objects.all().order_by('name')

        return render(request, 'sistema/usuario_sistema.html', {'ind': ind, 'aviso': aviso, 'grupos':grupos})

    if request.method == "POST":
        if request.POST['password'] == request.POST['rpassword']:
            crear = User()
            crear.username = str(request.POST['nombre']).lower()[0] + str(request.POST['apellido']).lower().split(' ')[0]
            crear.first_name = str(request.POST['nombre']).title()
            crear.last_name = str(request.POST['apellido']).title()
            crear.email = str(str(crear.username) + '@example.com').lower()
            crear.password = make_password(request.POST['password'])
            crear.is_active = True
            crear.save()

            for g in request.POST.getlist('grupos'):
                crear.groups.add(g)
            crear.save()

            request.session['aviso'] = {'ind': 2, 'aviso':""}
        else:
            request.session['aviso'] = {'ind': 0, 'aviso':""}

        return redirect(usuario_sistema)
