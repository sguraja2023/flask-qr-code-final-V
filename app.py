from flask import Flask, render_template, request, send_file, redirect, url_for
import qrcode
from PIL import Image, ImageDraw
import os

app = Flask(__name__)

# Directory to save generated QR codes
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Route for homepage
@app.route('/')
def home():
    return render_template('index.html')

# Route for generating the QR code
@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    url = request.form['url']
    color = request.form.get('color', 'black')
    shape = request.form.get('shape', 'square')
    image_file = request.files.get('image', None)  # Handle image upload for premium users

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=5,
        error_correction=qrcode.constants.ERROR_CORRECT_H
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color=color, back_color="white").convert("RGBA")

    # Apply shape mask
    img_with_shape = apply_shape_mask(img, shape)

    # Add image to the center if uploaded
    if image_file:
        img_with_shape = add_image_to_qr(img_with_shape, image_file)

    # Save QR image to file
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'qr_code.png')
    img_with_shape.save(file_path, format='PNG')

    return send_file(file_path, mimetype='image/png', as_attachment=True)

# Function to apply shape mask (square, circle, triangle)
def apply_shape_mask(qr_image, shape):
    width, height = qr_image.size
    mask = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(mask)

    if shape == "square":
        draw.rectangle([0, 0, width, height], fill=255)
    elif shape == "circle":
        draw.ellipse([0, 0, width, height], fill=255)
    elif shape == "triangle":
        draw.polygon([(width // 2, 0), (width, height), (0, height)], fill=255)

    qr_image.putalpha(mask)
    return qr_image

# Function to add an image to the center of the QR code with proper transparency handling
def add_image_to_qr(qr_image, image_file):
    overlay = Image.open(image_file).convert("RGBA")  # Ensure RGBA mode for transparency handling
    qr_width, qr_height = qr_image.size
    overlay = overlay.resize((qr_width // 4, qr_height // 4))  # Resize overlay image to fit

    # Calculate position for the overlay image
    position = ((qr_width - overlay.width) // 2, (qr_height - overlay.height) // 2)
    
    # Create an image with a transparent background and paste the overlay
    qr_image.paste(overlay, position, overlay)  # Paste with transparency (alpha channel)

    return qr_image

# Premium features page
@app.route('/premium')
def premium():
    return render_template('premium.html')

if __name__ == "__main__":
    app.run(debug=True)
