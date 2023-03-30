from sistema.models import Paciente, Tipo_id, Sexo, Municipio
from celery import shared_task


@shared_task
def obtener_data_pcte(tp_id, no_id, tel):
    try:
        pcte_local = Paciente.objects.filter(tipo_id__tipo_id=tp_id, numero_id=no_id)
        if not pcte_local:
            new_pcte = Paciente()
        else:
            new_pcte = pcte_local[0]

        pcte = TPacientes.objects.using('esalud').filter(tp_id_pcte__t_tp_id=tp_id, num_id_pcte=no_id)
        if pcte:
            pt = pcte[0]
            if tel == '0000000000' or tel == "":
                telefono = str(pt.tel_pcte)
            else:
                telefono = str(tel)

            municipio = ""
            if pt.id_barrio_pcte is not None or pt.id_barrio_pcte != "":
                munic = Municipio.objects.filter(municipio__contains=str(pt.id_barrio_pcte.consec_mpio.nom_mpio))
                if munic:
                    for d in munic:
                        if d.municipio.upper() == str(pt.id_barrio_pcte.consec_mpio.nom_mpio):
                            municipio = d.id

            if pt.id_grupo_abo is not None and pt.id_rh is not None:
                grupo = pt.id_grupo_abo.desc_grupo_abo
                rh = pt.id_rh.desc_rh
            else:
                grupo = ""
                rh = ""

            new_pcte.tipo_id = Tipo_id.objects.get(tipo_id=tp_id)
            new_pcte.numero_id = no_id
            new_pcte.p_nombre = str(pt.pri_nom_pcte).upper()
            new_pcte.s_nombre = str(pt.seg_nom_pcte).upper()
            new_pcte.p_apellido = str(pt.pri_apell_pcte).upper()
            new_pcte.s_apellido = str(pt.seg_apell_pcte).upper()
            new_pcte.f_nacimiento = pt.fech_ncto_pcte
            new_pcte.sexo = Sexo.objects.get(sexo=pt.sexo.upper())
            new_pcte.telefono_movil = telefono
            new_pcte.municipio_residencia_id = municipio
            new_pcte.direccion_residencia = pt.dir_pcte
            new_pcte.grupo_s = grupo+rh
            new_pcte.email = str(pt.mail_pcte).lower()
            new_pcte.envio_inf = True
            new_pcte.save()
    except:
        print('Error al guardar paciente')
