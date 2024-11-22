document.getElementById('premiumBtn').addEventListener('click', function() {
    document.getElementById('premiumOptions').style.display = 'block';
    document.getElementById('premiumBtn').style.display = 'none';
});

// Optionally implement color wheel and image upload logic for premium users
document.getElementById('colorWheelBtn').addEventListener('click', function() {
    alert('Premium color wheel functionality');
});

document.getElementById('uploadImageBtn').addEventListener('click', function() {
    alert('Upload image functionality');
});
