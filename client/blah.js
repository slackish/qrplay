function update_qr() {
    try {
        text = "";
        text += document.getElementsByName("hash")[0].value;
        text += ":";
        text += document.getElementsByName("program")[0].value;
        console.log(text);

        document.getElementById("qrcode").textContent = "";
        new QRCode(document.getElementById("qrcode"), text);
    }
    catch(err) {
        console.log(err)
    }
}

(function update() {

    update_qr();
    setTimeout( update, 1000 );
})();
