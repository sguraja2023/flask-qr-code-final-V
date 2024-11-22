document.getElementById('premiumBtn').addEventListener('click', function() {
    document.getElementById('premiumOptions').style.display = 'block';
    document.getElementById('premiumBtn').style.display = 'none';

    // Show the image upload button and RGB color picker
    document.getElementById('uploadImageBtn').style.display = 'inline-block';
    document.getElementById('rgbColor').style.display = 'inline-block';
});

// Update the text input when a color is picked from the color wheel
document.getElementById('rgbColor').addEventListener('input', function() {
    // Get the value from the color wheel and set it in the color input field
    document.getElementById('color').value = this.value;
});
