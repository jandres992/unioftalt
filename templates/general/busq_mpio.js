function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function busq_municipio() {
    $("#municipio").empty();
    $("#gifModal").modal('show');
    $.ajax({
        url: '{% url "search_municipio" %}',
        type: 'post',
        data: {
            departamento: $("#departamento").val(),
            csrfmiddlewaretoken: '{{ csrf_token }}'
        },
        success: function (data) {
            try {
                if ($("#municipio").find('option[value=""]').length === 0) {
                    $("#municipio").append($("<option>", {
                        value: "",
                        text: "Seleccione"
                    }));
                }
                for (var i = 0; i < (data.municipio).length; i++) {
                    if ($("#municipio").find('option[value="' + data.municipio[i]['id'] + '"]').length === 0) {
                        $("#municipio").append($("<option>", {
                            value: data.municipio[i]['id'],
                            text: data.municipio[i]['municipio']
                        }));
                    }
                }
                setTimeout(() => {
                    $("#gifModal").modal("hide");
                }, 1000);
            } catch (e) {
                console.log("Error en busqueda de municipio")
            }
        },
        /*error: function (e){
            window.location.reload()
        }*/
    });
    return false;
}

$("#departamento").change(function (e) {
    if ($(this).val() != ""){
       $("#municipio").empty();
       busq_municipio();
    }
});