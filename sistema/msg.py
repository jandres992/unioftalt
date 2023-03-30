import smtplib
import socket, datetime, time, requests, json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from sistema.models import *


def send_sms(msg_str, telefono):
    resp_sms_goip = False
    resp_sms_issabel = False
    error = ""

    while True:
        sms = Settings_msg_sms.objects.get(id=1)
        if not sms.linea_goip:
            if not sms.linea_issabel:
                break
        if not sms.usage:
            break
        else:
            time.sleep(2)
    sms.usage = True
    sms.save()

    try:
        line = False
        if sms.linea_goip:
            #### goip ###
            resp_q = requests.get("http://" + str(sms.linea_goip_ip) +
                                "/default/en_US/send.html?u=" + str(sms.linea_goip_user) +
                                "&p=" + str(sms.linea_goip_password) + "&l=" + str(sms.linea_goip_linea) +
                                "&n=" + str(telefono) +
                                "&m=" + str(msg_str))
            resp_txt = resp_q.content.decode("utf-8")
            i_r = resp_txt.index('ID')
            id_resp = resp_txt[i_r:].replace("ID:", "").replace("\n", "")

            cont = 0
            while True:
                veri = requests.get("http://" + str(sms.linea_goip_ip) +
                                    "/default/en_US/send_status.xml?u="+ str(sms.linea_goip_user) +
                                    "&p=" + str(sms.linea_goip_password))
                veri_txt = veri.content.decode("utf-8")
                i_v = veri_txt.index('<id' + str(sms.linea_goip_linea) + '>')
                f_v = veri_txt.index('</id' + str(sms.linea_goip_linea) + '>')
                id_veri = veri_txt[i_v:f_v].replace("<id" + str(sms.linea_goip_linea) + ">", "")

                if id_resp == id_veri:
                    i_v_s = veri_txt.index('<status' + str(sms.linea_goip_linea) + '>')
                    f_v_s = veri_txt.index('</status' + str(sms.linea_goip_linea) + '>')
                    status = veri_txt[i_v_s:f_v_s].replace("<status" + str(sms.linea_goip_linea) + ">", "")
                    if status == "DONE":
                        resp_sms_goip = True
                        line = True
                        break
                    else:
                        cont += 1
                else:
                    cont += 1

                time.sleep(2)
                if cont > 7:
                    i_v_e = veri_txt.index('<error' + str(sms.linea_goip_linea) + '>')
                    f_v_e = veri_txt.index('</error' + str(sms.linea_goip_linea) + '>')
                    error = veri_txt[i_v_e:f_v_e].replace("<error" + str(sms.linea_goip_linea) + ">", "")
                    line = True
                    break
            ### fin goip ###

        if sms.linea_issabel:
            if not resp_sms_goip or not sms.linea_goip:
                #### isabelPBX ###
                cont = 0
                while True:
                    ssh = paramiko.SSHClient()
                    ssh.load_system_host_keys()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(str(sms.linea_issabel_ip), username=str(sms.linea_issabel_user), password=str(sms.linea_issabel_password))
                    cmd_to_execute = "asterisk -rx 'dongle sms " + str(sms.linea_issabel_nomb) + " +57" + str(telefono) + " " + str(msg_str) + "'"
                    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd_to_execute)
                    lines = ssh_stdout.readlines()

                    '''
                    errors = ssh_stderr.readlines()
                    for l in lines:
                        print('line', l)
                    for e in errors:
                        print('line', e)
                    '''

                    if "[" + str(sms.linea_issabel_nomb) + "] Device disconnected\n" == lines[0]:
                        ssh.exec_command('dongle stop now MODEM_1')
                        time.sleep(2)
                        ssh.exec_command('dongle start MODEM_1')
                        time.sleep(2)

                        cont += 1
                        if cont > 7:
                            error = lines[0]
                            line = True
                            break
                    else:
                        resp_sms_issabel = True
                        line = True
                        break
                ### fin isabelPBX ###

        if resp_sms_goip or resp_sms_issabel:
            resp = {'resp': True}
        else:
            resp = {'resp': False, 'error': "Error sms:" + error}

        if not line:
            resp = {'resp': False, 'error': "Las lineas de SMS no estan habilitadas"}
    except:
        resp = {'resp': False, 'error': "Error en el servidor, por favor comuniquese con el área de desarrollo"}

    sms.usage = False
    sms.save()
    return resp


def send_whatsapp(data):
    cont = 0
    aut_msg = False

    while True:
        wt = Settings_msg_whatsapp.objects.get(id=1)
        if not wt.whatsapp:
            break
        if not wt.usage:
            aut_msg = True
            break
        else:
            time.sleep(2)
            cont += 1
            if cont > 10:
                break
    try:
        con = 0
        if wt.whatsapp:
            while True:
                if aut_msg:
                    wt.usage = True
                    wt.save()

                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    server_address = (str(wt.dir), int(wt.port))
                    sock.settimeout(100)
                    try:
                        sock.connect(server_address)
                        send_data = json.dumps(data)
                        sock.sendall(bytes(send_data, encoding="utf-8"))

                        amount_received = 0
                        amount_expected = len([data])

                        recv_data = None
                        while amount_received < amount_expected:
                            recv_data = sock.recv(10240)
                            amount_received += len(recv_data)

                        data_json = json.loads(recv_data)
                        datos = data_json[0]

                        resp = {'resp': datos['resp'], 'msg_status': datos['msg_status'] + " - " + datos['aviso']}
                    except (socket.timeout, socket.gaierror) as error:
                        resp = {'resp': False, 'error': error}
                    finally:
                        sock.close()
                else:
                    resp = {'ind': 0, 'resp': False, 'error': "No se pude enviar el mensaje, proceso ocupado"}

                if resp['resp']:
                    break
                else:
                    con += 1

                if con > 2:
                    break
        else:
            resp = {'ind': 0, 'resp': False, 'error': "El envio de mensajes de Whatsapp no esta habilitado"}
    except:
        resp = {'ind': 0, 'resp': False, 'error': "Error en el servidor, comuniquese con el área de desarrollo"}

    wt.usage = False
    wt.save()

    return resp


def send_email_cita(li):
    while True:
        mail = Settings_msg_email.objects.get(id=1)
        if not mail.habilitado:
            break
        if not mail.usage:
            break
        else:
            time.sleep(2)
    mail.usage = True
    mail.save()

    try:
        if mail.habilitado:
            if str(li['email']) is not None or str(li['email']) != "":
                try:
                    validate_email(li['email'])
                    email = True
                except ValidationError as e:
                    email = False

                aut_mail = False
                msg_text = None

                if email:
                    email = li['email']
                    mes = datetime.datetime.strftime(datetime.datetime.now(), '%B')
                    year = datetime.datetime.now().year
                    if li['tp_opc'] == "Agendar Cita":
                        msg_text = str('<p class="info" style="margin-bottom: 0px;"><b>Nombre del Paciente:</b></p> \
                                        <p class="info" style="margin-bottom: 8px;">{nombre}</p> \
                                        <p class="info" style="margin-bottom: 0px;"><b>Tipo de tramite de Cita Médica:</b></p> \
                                        <p class="info" style="margin-bottom: 8px;font-size:14pt;">{titulo}</p> \
                                        <p class="info" style="margin-bottom: 0px;"><b>Fecha y hora de la Cita:</b></p> \
                                        <p class="info" style="margin-bottom: 8px;font-size:14pt;"> {fecha} {hora}</p> \
                                        <p class="info" style="margin-bottom: 0px;"><b>Especialidad:</b></p> \
                                        <p class="info" style="margin-bottom: 8px;">{especialidad}</p> \
                                        <p class="info" style="margin-bottom: 0px;"><b>Especialista:</b></p> \
                                        <p class="info" style="margin-bottom: 8px;"> Dr(a). {especialista}</p> \
                                        <p class="info" style="margin-bottom: 0px;"><b>Lugar:</b></p> \
                                        <p class="info" style="margin-bottom: 8px;">Sociedad de Especialistas de Girardot S.A.S</p> \
                                        <p class="info" style="margin-bottom: 0px;"><b>Dirección:</b></p> \
                                        <p class="info" style="margin-bottom: 8px;">Calle 13 No. 10 - 49 B/ San Miguel.<br>Girardot.</p>'). \
                            format(nombre=str(li['nombre_pcte']).upper(),
                                   fecha=li['fecha'], hora=li['hora'],
                                   especialidad=str(li['especialidad']).upper(),
                                   especialista=str(li['especialista']).upper(),
                                   titulo=str(li['titulo']))
                        aut_mail = True

                    else:
                        msg_text = str('<p class="info" style="margin-bottom: 0px;"><b>Nombre del Paciente:</b></p> \
                                            <p class="info" style="margin-bottom: 8px;">{nombre}</p> \
                                            <p class="info" style="margin-bottom: 0px;"><b>Tipo de tramite de Cita Médica:</b></p> \
                                            <p class="info" style="margin-bottom: 8px;font-size:12pt;">{titulo}</p> \
                                            <p class="info" style="margin-bottom: 0px;"><b>Fecha y hora de notificación:</b></p> \
                                            <p class="info" style="margin-bottom: 8px;font-size:12pt;"> {fecha} {hora}</p> \
                                            <p class="info" style="margin-bottom: 0px;"><b>Especialidad:</b></p> \
                                            <p class="info" style="margin-bottom: 8px;">{especialidad}</p> \
                                            <p class="info" style="margin-bottom: 0px;"><b>Observación:</b></p> \
                                            <p class="info" style="margin-bottom: 8px;">{observacion}</p>'). \
                            format(nombre=str(li['nombre_pcte']).upper(),
                                   fecha=datetime.date.today().strftime("%d-%m-%Y"),
                                   hora=datetime.datetime.now().strftime("%H:%M"),
                                   especialidad=str(li['especialidad']).upper(),
                                   observacion=str(li['recomendacion']).lower(),
                                   titulo=str(li['titulo']))
                        aut_mail = True

                    if aut_mail and msg_text is not None:
                        observacion = li['recomendacion']
                        html = '''
                            <!DOCTYPE html>
                                <html>
                                    <head>
                                        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
                                        <title>Información de Cita Médica - Clinica de Especialistas Gdot</title>
                                        <style type="text/css">
                                            a {color: #03b3e8;}
                                            body, #header h1, #header h2, p {margin: 0; padding: 0;}
                                            #main {border: 1px solid #cfcece;}
                                            img {display: block;}
                                            #top-message p, #bottom p {color: #3f4042; font-size: 12px; font-family: Arial, Helvetica, sans-serif;}
                                            #header h1 {color: #ffffff !important; font-family: "Lucida Grande", sans-serif; font-size: 24px; margin-bottom: 0!important; padding-bottom: 0;}
                                            #header p { color: #ffffff !important; font-family: "Lucida Grande", "Lucida Sans", "Lucida Sans Unicode", sans-serif; font-size: 12px;}
                                            h5 {margin: 0 0 0.8em 0;}
                                            h5 {font-size: 18px; color: #444444 !important; font-family: Arial, Helvetica, sans-serif;}
                                            p {font-size: 12px;color: #444444 !important;font-family: "Lucida Grande", "Lucida Sans", "Lucida Sans Unicode", sans-serif;line-height: 1.5;}
                                            .info{font-size: 12pt !important;}
                                        </style>
                                    </head>
        
                                    <body>
                                        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: white !important;">
                                            <tr>
                                                <td>
                                                    <table id="top-message" cellpadding="20" cellspacing="0" width="600" align="center">
                                                        <tr>
                                                          <td align="center" style="margin: 0px;padding: 0px; background-color: white !important;">
                                                              <img src="http://clinicadeespecialistasgirardot.com/images/logo2_extendido.png" width="400" height="90">
                                                          </td>
                                                        </tr>
                                                    </table>
        
                                                    <table id="main" width="600" align="center" cellpadding="0" cellspacing="15" style="background-color: #ffffff;">
                                                        <tr>
                                                            <td>
                                                                <table id="header" cellpadding="10" cellspacing="0" align="center" style="background-color: #8fb3e9">
                                                                    <tr>
                                                                        <td width="570" align="center"  style="background-color: #0070b1;color:white;border-color:#0070b1;"><h1>Notificación de cita médica</h1></td>
                                                                    </tr>
                                                                    <tr>
                                                                        <td width="570" align="right" style="color:white;background-color: #0070b1; border-color:#0070b1;"><p>''' + str(mes) + ' ' + str(year) + '''</p></td>
                                                                    </tr>
                                                                </table>
                                                            </td>
                                                        </tr>
        
                                                        <tr>
                                                            <td>
                                                                <table style="margin: 0px;" cellpadding="0" cellspacing="0" align="center">
                                                                    <tr>
                                                                        <td width="330" valign="top">
                                                                            <h5></h5>
                                                                            ''' + msg_text + '''
                                                                        </td>
                                                                        <td width="10"></td>
                                                                        <td width="220" valign="top" style="padding:5px; padding-top: 50px;" align="center">
                                                                            <img src="http://clinicadeespecialistasgirardot.com/images/doctor.png" width="250">
                                                                        </td>
                                                                    </tr>
                                                                </table>
                                                            </td>
                                                        </tr>
                                                        <tr>
                                                            <td>
                                                                <p style="font-size: 12pt;"><b>Recomendaciones:</b></p>
                                                                <p>''' + observacion + '''</p>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                    <table id="bottom" cellpadding="20" cellspacing="0" width="600" align="center">
                                                        <tr>
                                                            <td align="center">
                                                                <p>
                                                                    La Información suministrada a nuestra entidad sera tratada bajo nuestra politica de protección de datos que podra encontrar en el
                                                                    siguente enlace (<a href="https://www.clinicadeespecialistasgirardot.com/webpage/web/politica_datos">Politica de protección de datos personales</a>). En caso de no aceptar puede realizar la solicitud a
                                                                    traves de nuestra pagina web.
                                                                </p>
                                                                <p><a href="https://www.clinicadeespecialistasgirardot.com/webpage/web/contacto">clinicadeespecialistasgirardot.com</a></p>
                                                            </td>
                                                        </tr>
                                                    </table><!-- top message -->
                                                </td>
                                            </tr>
                                        </table><!-- wrapper -->
                                    </body>
                                </html>
                            '''
                        msg = MIMEMultipart('alternative')
                        msg['Subject'] = str(li['titulo']).title() + " - SEG"
                        msg['From'] = mail.dir
                        msg['To'] = str(email)
                        text = MIMEText(html, 'html')
                        msg.attach(text)
                        s = smtplib.SMTP(mail.dir_server + ":" + str(mail.port_server))
                        s.starttls()

                        s.login(msg['From'], mail.password)
                        s.sendmail(mail.dir, str(email), msg.as_string())
                        s.quit()

                        resp = {'resp': True, 'email': li['email']}
                    else:
                        resp = {'resp': False, 'error': 'Error en el servidor, por favor comuniquese con el administrador del sistema'}
                else:
                    resp = {'resp': False, 'error': 'Error en el servidor, la dirección de email no es valida'}
            else:
                resp = {'resp': False, 'error': 'Error en el servidor, no se encuentra dirección de correo'}
        else:
            resp = {'resp': False, 'error': 'El envio de correo electronico no esta habilitado'}
    except:
        resp = {'resp': False, 'error': 'Error, comuniquese con el área de desarrollo'}
    mail.usage = False
    mail.save()

    return resp