document.getElementById('qr-form').addEventListener('submit', function(event) {
    event.preventDefault();

    const url = document.getElementById('url').value;
    const color = document.getElementById('color').value;
    const shape = document.getElementById('shape').value;

    const formData = new FormData();
    formData.append('url', url);
    formData.append('color', color);
    formData.append('shape', shape);

    fetch('/generate_qr', {
        method: 'POST',
        body: formData
    })
    .then(response => response.blob())
    .then(blob => {
        const qrResult = document.getElementById('qr-result');
        qrResult.innerHTML = '';
        const img = document.createElement('img');
        img.src = URL.createObjectURL(blob);
        qrResult.appendChild(img);
    })
    .catch(error => alert('An error occurred: ' + error));
});
