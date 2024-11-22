document.getElementById('premiumBtn').addEventListener('click', function() {
    document.getElementById('premiumOptions').style.display = 'block';
    document.getElementById('premiumBtn').style.display = 'none';

    // Show the image upload button and RGB color picker
    document.getElementById('uploadImageBtn').style.display = 'inline-block';
    document.getElementById('rgbColor').style.display = 'inline-block';
});
