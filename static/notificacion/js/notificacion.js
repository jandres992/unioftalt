function notificacion(ind,aviso) {
    if (ind == 1) {
        var tp = 'info';
        var icon = 'icofont-info-circle';
    } else if (ind == 2) {
        var tp = 'success';
        var icon = 'icofont-check-circled';
    } else if (ind == 0) {
        var tp = 'danger';
        var icon = 'icofont-close-circled';
    } else if (ind == 3) {
        var tp = 'warning';
        var icon = "icofont-warning";
    }

    $.notify({
        icon: icon,
        message:  aviso,
    }, {
        type: tp,
        animate: {
            enter: 'animated bounceInDown',
            exit: 'animated bounceOutUp'
        },
        placement: {
            from: "top",
            align: "right"
        }
    });
}