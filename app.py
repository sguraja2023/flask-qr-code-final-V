from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import qrcode
from PIL import Image
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import CircleModuleDrawer
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
    "admin@example.com": {"password": "password123", "role": "admin", "is_premium": False},
    "user@example.com": {"password": "user123", "role": "user", "is_premium": True},
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
            session['role'] = USER_DATA[username].get('role', 'user')
            flash('Login successful!', 'success')

            if session['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('home'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Invalid email address!', 'danger')
            return redirect(url_for('signup'))

        if email in USER_DATA:
            flash('Email is already registered. Please log in.', 'warning')
            return redirect(url_for('login'))

        USER_DATA[email] = {"password": password, "role": "user"}
        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/logout')
def logout():
    if 'user' in session:
        session.clear()
        flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

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
    color = request.form.get('color', 'black')
    shape = request.form.get('shape', 'square')
    image_file = request.files.get('image', None)

    if not is_valid_url(url):
        flash('Invalid URL. Please provide a valid URL.', 'danger')
        return redirect(url_for('premium'))

    if not (is_valid_hex_color(color) or is_valid_color_name(color)):
        flash('Invalid color. Please enter a valid hex code or color name.', 'danger')
        return redirect(url_for('premium'))

    qr = qrcode.QRCode(
        version=1, box_size=10, border=4, error_correction=qrcode.constants.ERROR_CORRECT_H
    )
    qr.add_data(url)
    qr.make(fit=True)

    if shape == "circle":
        img = qr.make_image(
            fill_color=color,
            back_color="white",
            image_factory=StyledPilImage,
            module_drawer=CircleModuleDrawer(),
        )
    else:
        img = qr.make_image(fill_color=color, back_color="white")

    if image_file and image_file.filename != '':
        img = add_image_to_qr(img, image_file)

    # Mark user as premium in USER_DATA
    current_user = session['user']
    if current_user in USER_DATA:
        USER_DATA[current_user]['is_premium'] = True

    # Save QR code
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'qr_code.png')
    img.save(file_path, format='PNG')

    flash('QR Code generated successfully! You are now marked as a premium user.', 'success')
    return send_file(file_path, mimetype='image/png', as_attachment=True)

def add_image_to_qr(qr_image, image_file):
    overlay = Image.open(image_file).convert("RGBA")
    qr_width, qr_height = qr_image.size

    # Increased size of overlay to make it larger on the QR code
    overlay_size = int(qr_width * 0.3)
    overlay = overlay.resize((overlay_size, overlay_size), Image.Resampling.LANCZOS)

    position = ((qr_width - overlay.width) // 2, (qr_height - overlay.height) // 2)
    qr_image.paste(overlay, position, overlay)
    return qr_image

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if 'user' not in session or session.get('role') != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('login'))

    users = [
        {"email": email, "role": details["role"], "is_premium": details.get("is_premium", False)}
        for email, details in USER_DATA.items()
    ]
    total_users = len(users)
    premium_users = sum(1 for user in users if user["is_premium"])
    
    # Update premium subscription price here
    premium_price = 3  # Changed from $10 to $3
    monthly_revenue = premium_users * premium_price

    return render_template(
        'admin_dashboard.html',
        users=users,
        total_users=total_users,
        premium_users=premium_users,
        monthly_revenue=monthly_revenue,
    )

@app.route('/premium', methods=['GET'])
def premium():
    if 'user' not in session:
        flash('Please log in to access premium features.', 'warning')
        return redirect(url_for('login'))
    return render_template('premium.html')

if __name__ == "__main__":
    app.run(debug=True)
