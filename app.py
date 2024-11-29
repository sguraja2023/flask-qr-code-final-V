from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, make_response
import qrcode
from PIL import Image
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import CircleModuleDrawer, SquareModuleDrawer
import os
import re
from urllib.parse import urlparse
import matplotlib

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
    "admin@example.com": {"password": "password123", "role": "admin"},
    "user@example.com": {"password": "user123", "role": "user"}
}

# URL validation function
def is_valid_url(url):
    try:
        result = urlparse(url)
        return result.scheme in ['http', 'https'] and result.netloc
    except ValueError:
        return False

# Hex color validation function
def is_valid_hex_color(color):
    return bool(re.match(r'^#[0-9a-fA-F]{6}$', color))

# Color name validation function (from matplotlib)
def is_valid_color_name(color):
    return color.lower() in matplotlib.colors.CSS4_COLORS

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Validate credentials
        if username in USER_DATA and USER_DATA[username]['password'] == password:
            session['user'] = username
            session['role'] = USER_DATA[username].get('role', 'user')  # Set role
            flash('Login successful!', 'success')
            
            # Redirect based on user role
            if session['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('home'))  # Redirect to the homepage for regular users
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        if email in USER_DATA:
            flash('Email already exists. Please log in.', 'warning')
            return redirect(url_for('login'))

        # Save user data (dummy implementation)
        USER_DATA[email] = {"password": password, "role": "user"}
        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

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

@app.route('/')
def home():
    if 'user' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))
    
    return render_template('index.html')

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    if 'user' not in session:
        flash('Please log in to access this feature.', 'warning')
        return redirect(url_for('login'))

    url = request.form['url']
    color = request.form.get('color', 'black')  # Default color is black
    shape = request.form.get('shape', 'square')
    image_file = request.files.get('image', None)

    # Validate the input URL
    if not is_valid_url(url):
        flash('Invalid URL. Please provide a valid URL.', 'danger')
        return redirect(url_for('premium'))

    # Validate the color
    if not (is_valid_hex_color(color) or is_valid_color_name(color)):
        flash('Invalid color. Please enter a valid hex code or color name.', 'danger')
        return redirect(url_for('premium'))

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4,
        error_correction=qrcode.constants.ERROR_CORRECT_H
    )
    qr.add_data(url)
    qr.make(fit=True)

    if shape == "circle":
        img = qr.make_image(
            fill_color=color,
            back_color="white",
            image_factory=StyledPilImage,
            module_drawer=CircleModuleDrawer()
        )
    else:
        img = qr.make_image(fill_color=color, back_color="white")

    # Save the QR code image
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'qr_code.png')
    img.save(file_path, format='PNG')

    return send_file(file_path, mimetype='image/png', as_attachment=True)

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if 'user' not in session or session.get('role') != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('login'))

    users = [
        {"email": email, "role": details.get('role', 'user')}
        for email, details in USER_DATA.items()
    ]

    return render_template('admin_dashboard.html', users=users)

@app.route('/premium', methods=['GET', 'POST'])
def premium():
    if 'user' not in session:
        flash('Please log in to access premium features.', 'warning')
        return redirect(url_for('login'))
    return render_template('premium.html')

if __name__ == "__main__":
    app.run(debug=True)
