const qrData = "{{ request.build_absolute_uri }}";  // URL de la page du produit
    new QRCode(document.getElementById("qrcode"), {
        text: qrData,
        width: 100,
        height: 100
    });