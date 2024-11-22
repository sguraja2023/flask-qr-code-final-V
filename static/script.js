document.getElementById('premiumBtn').addEventListener('click', function() {
    document.getElementById('premiumOptions').style.display = 'block';
    document.getElementById('premiumBtn').style.display = 'none';

    // Show the image upload button and RGB color picker
    document.getElementById('uploadImageBtn').style.display = 'inline-block';
    document.getElementById('rgbColor').style.display = 'inline-block';
});

function updateColorValue(event) {
    // Update the value in the color input field to send it with the form
    const colorInput = document.getElementById('color');
    colorInput.value = event.target.value;
}

function triggerFileUpload() {
    document.getElementById('image').click();
}