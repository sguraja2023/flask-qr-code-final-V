document.getElementById('premiumBtn').addEventListener('click', function() {
    document.getElementById('premiumOptions').style.display = 'block';
    document.getElementById('premiumBtn').style.display = 'none';

    // Show the image upload button and RGB color picker
    document.getElementById('uploadImageBtn').style.display = 'inline-block';
    document.getElementById('rgbColor').style.display = 'inline-block';
});

// Sync the color picker with the color input field
document.getElementById('rgbColor').addEventListener('input', function() {
    // Update the color input field with the RGB color picker value
    document.getElementById('color').value = this.value;
});
