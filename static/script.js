document.getElementById('premiumBtn').addEventListener('click', function() {
    // Display premium options when clicking the 'Sign Up for Premium Features' button
    document.getElementById('premiumOptions').style.display = 'block';
    document.getElementById('premiumBtn').style.display = 'none';

    // Show the image upload button and RGB color picker
    document.getElementById('uploadImageBtn').style.display = 'inline-block';
    document.getElementById('rgbColor').style.display = 'inline-block';
});

function updateColorValue(event) {
    // Update the value in the color input field to send it with the form
    const colorInput = document.getElementById('color');
    colorInput.value = event.target.value; // Get the selected color from the picker and set it in the color input
}

// Trigger the file upload when the user clicks the 'Upload Image/Logo for Center' button
function triggerFileUpload() {
    document.getElementById('image').click();
}