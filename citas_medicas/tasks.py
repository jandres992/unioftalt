from citas_medicas.models import *
from sistema.models import *
from sistema.msg import *
from celery import shared_task


@shared_task
def send_notificacion_cita(user, message, notificacion):
    sa = Solicitud_cita.objects.get(id=message['no_aten'])
    reg = False
    if sa.bloqueo_atencion is not None and sa.usuario_atencion is not None:
        sms_txt = None
        whatsapp_txt = None
        email_txt = None
        op = False
        id_cita = ""

        if sa.usuario_atencion.id == user:
            excl = Lista_negra_msg.objects.filter(id_pcte_id=sa.pcte.id)
            if not excl:
                if len(sa.pcte.telefono_movil) == 10:
                    op = True
                    nom_pcte = str(sa.pcte.p_nombre + " " + sa.pcte.s_nombre + " " + sa.pcte.p_apellido + " " + sa.pcte.s_apellido).upper()

                    if sa.tramite.tramite.title() == "Agendar Cita" and not notificacion and not sa.descartar:
                        cita = TInfoCitas.objects.using('esalud').get(id_cita=message['id_cita'])
                        med = TPersonal.objects.using('esalud').filter(tp_id_pers=cita.cod_md_histoc.tp_idmd_meds, identif_pers=cita.cod_md_histoc.ident_md_meds)
                        medico = str(med[0].prinom_pers + " " + med[0].segnom_pers + " " + med[0].priape_pers + " " + med[0].segape_pers).upper()
                        fecha = cita.fecha_ini.strftime("%-d/%m/%Y")
                        hora = cita.fecha_ini.strftime("%I:%M %p")
                        especialidad = str(cita.id_esp_cita.nom_esp)
                        id_cita = str(cita.id_cita)
                    else:
                        medico = ""
                        fecha = sa.fecha_s.strftime("%-d/%m/%Y")
                        hora = ""
                        especialidad = sa.especialidad.nombre.title()

                    if sa.tramite.tramite.title() == "Agendar Cita" and sa.l_espera:
                        msg_whatsapp = Msg_whatsapp.objects.get(tipo__tramite="Espera Cita")
                        msg_sms = Msg_sms.objects.get(tipo__tramite="Espera Cita")
                        msg_email = Msg_email.objects.get(tipo__tramite="Espera Cita")
                    elif sa.descartar:
                        msg_whatsapp = Msg_whatsapp.objects.get(tipo__tramite="Descartar Cita")
                        msg_sms = Msg_sms.objects.get(tipo__tramite="Descartar Cita")
                        msg_email = Msg_email.objects.get(tipo__tramite="Descartar Cita")
                    else:
                        msg_whatsapp = Msg_whatsapp.objects.get(tipo__id=sa.tramite.id)
                        msg_sms = Msg_sms.objects.get(tipo__id=sa.tramite.id)
                        msg_email = Msg_email.objects.get(tipo__id=sa.tramite.id)

                    sms_txt = msg_sms.mensaje.format(pcte=str(sa.pcte.p_nombre + " " + sa.pcte.p_apellido).title(),
                                                     especialidad=especialidad, motivo=sa.observacion_des,
                                                     tramite=sa.tramite.txt.upper(), fecha=fecha, hora=hora)

                    whatsapp_txt = dict(telefono=str(3017124716),
                                        saludo=str(msg_whatsapp.saludo).format(pcte=str(nom_pcte)),
                                        mensaje=str(msg_whatsapp.mensaje).format(especialidad=especialidad,
                                                                                 medico=medico, fecha=fecha,
                                                                                 hora=hora,
                                                                                 motivo=sa.observacion_des,),
                                        detalle=msg_whatsapp.detalle,
                                        observacion=msg_whatsapp.observacion)

                    email_txt = dict(nombre_pcte=nom_pcte, especialidad=especialidad,
                                     especialista=medico, fecha=fecha, hora=hora,
                                     email="jorgeandres992@gmail.com",
                                     telefono=str(3017124716),
                                     tp_opc=msg_email.tipo.tramite.title(),
                                     recomendacion=msg_email.recomendacion,
                                     titulo=msg_email.titulo.title())
                    reg = True

            if op:
                r_sms = send_sms(sms_txt, str(3017124716))
                if 'error' in r_sms:
                    observacion = r_sms['error']
                else:
                    observacion = "SMS enviado"

                r_whatsapp = send_whatsapp(whatsapp_txt)
                if 'error' in r_whatsapp:
                    observacion = observacion + " | " + r_whatsapp['error']
                else:
                    observacion = observacion + " | Msg de Whatsapp enviado"

                r_email_cita = send_email_cita(email_txt)
                if 'error' in r_email_cita:
                    observacion = observacion + " | " + r_email_cita['error']
                else:
                    observacion = observacion + " | Email enviado"

                if r_sms['resp'] or r_whatsapp['resp'] or r_email_cita['resp']:
                    Notificacion_msg_cita.objects.create(
                        fecha=datetime.datetime.now(),
                        id_cita=id_cita,
                        whatsapp=r_whatsapp['resp'],
                        sms=r_sms['resp'],
                        mail=r_email_cita['resp'],
                        observacion=observacion,
                        id_aten_id=sa.id,
                        user_id=user)
    if not reg:
        sa.atendido = False
        sa.save()
