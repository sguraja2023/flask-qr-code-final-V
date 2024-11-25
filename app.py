from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file , make_response
import qrcode
from PIL import Image, ImageDraw
import os

app = Flask(__name__)

# Secret key for session management
app.secret_key = 'your_secret_key'

# Directory to save generated QR codes
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Dummy user data (for demonstration)
USER_DATA = {
    "admin@example.com": "password123"
}

# Route for login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Implement login logic here
        if username in USER_DATA and USER_DATA[username] == password:
            session['user'] = username  # Log the user in
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # Add logic to save user details securely
        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

# Route for logout
@app.route('/logout')
def logout():
    if 'user' in session:
        session.clear()
        flash('You have been logged out.', 'info')
    else:
        flash('You were not logged in.', 'warning')
    
    response = make_response(redirect(url_for('login')))
    response.delete_cookie('session')  # Clear session cookie
    return response

# Route for homepage
@app.route('/')
def home():
    if 'user' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))
    return render_template('index.html')

# Route for generating the QR code
@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    if 'user' not in session:
        flash('Please log in to access this feature.', 'warning')
        return redirect(url_for('login'))

    url = request.form['url']
    color = request.form.get('color', 'black')
    shape = request.form.get('shape', 'square')
    image_file = request.files.get('image', None)

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
    if 'user' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))
    return render_template('premium.html')

if __name__ == "__main__":
    app.run(debug=True)
