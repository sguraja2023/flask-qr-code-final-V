from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import qrcode
from PIL import Image, ImageDraw, ImageColor, ImageOps
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
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Dummy user data
USER_DATA = {
    "admin@example.com": {"password": "password123", "role": "admin", "is_premium": False},
    "user@example.com": {"password": "user123", "role": "user", "is_premium": False},
}

PREMIUM_PRICE = 3  # Monthly cost for premium users

# Helper functions
def is_valid_url(url):
    try:
        result = urlparse(url)
        return result.scheme in ['http', 'https'] and result.netloc
    except ValueError:
        return False

def is_valid_hex_color(color):
    return bool(re.match(r'^#[0-9a-fA-F]{6}$', color))

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in USER_DATA and USER_DATA[username]['password'] == password:
            session['user'] = username
            session['role'] = USER_DATA[username].get('role', 'user')
            session['is_premium'] = USER_DATA[username].get('is_premium', False)
            flash('Login successful!', 'success')

            if session['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif session['is_premium']:
                return redirect(url_for('premium'))
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

        USER_DATA[email] = {"password": password, "role": "user", "is_premium": False}
        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/logout')
def logout():
    if 'user' in session:
        session.clear()
        flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'user' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))
    return render_template('index.html', is_premium=session.get('is_premium', False))

@app.route('/premium', methods=['GET'])
def premium():
    if 'user' not in session:
        flash('Please log in to access premium features.', 'warning')
        return redirect(url_for('login'))

    if session.get('role') == 'admin':
        flash('Admins do not need premium upgrades.', 'info')
        return redirect(url_for('admin_dashboard'))

    current_user = session.get('user')
    if current_user and current_user in USER_DATA:
        USER_DATA[current_user]['is_premium'] = True
        session['is_premium'] = True
        flash('You have successfully upgraded to premium!', 'success')

    return render_template('premium.html', is_premium=True)

@app.route('/admin', methods=['GET'])
def admin_dashboard():
    if 'user' not in session:
        flash('Please log in to access the admin dashboard.', 'warning')
        return redirect(url_for('login'))
    if session.get('role') != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('home'))

    users = [
        {"email": email, "role": details["role"], "is_premium": details.get("is_premium", False)}
        for email, details in USER_DATA.items()
    ]
    total_users = len(users)
    premium_users = sum(1 for user in users if user["is_premium"])
    monthly_revenue = premium_users * PREMIUM_PRICE

    return render_template(
        'admin_dashboard.html',
        users=users,
        total_users=total_users,
        premium_users=premium_users,
        monthly_revenue=monthly_revenue,
    )

@app.route('/update_user', methods=['POST'])
def update_user():
    if 'user' not in session or session.get('role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))

    email = request.form.get('email')
    role = request.form.get('role')
    is_premium = 'is_premium' in request.form

    if email in USER_DATA:
        USER_DATA[email]['role'] = role
        USER_DATA[email]['is_premium'] = is_premium
        flash(f"User {email} updated successfully.", 'success')
    else:
        flash('User not found.', 'danger')

    return redirect(url_for('admin_dashboard'))

@app.route('/delete_user', methods=['POST'])
def delete_user():
    if 'user' not in session or session.get('role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))

    email = request.form.get('email')

    if email in USER_DATA:
        del USER_DATA[email]
        flash(f"User {email} deleted successfully.", 'success')
    else:
        flash('User not found.', 'danger')

    return redirect(url_for('admin_dashboard'))

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    if 'user' not in session:
        flash('Please log in to access this feature.', 'warning')
        return redirect(url_for('login'))

    # Get form data
    url = request.form['url']
    color = request.form.get('color', 'black').strip().lower()
    gradient_color = request.form.get('gradient', 'none')
    background_color = request.form.get('background_color', 'white').strip().lower()
    shape = request.form.get('shape', 'square')
    size = request.form.get('size', 'standard').lower()
    image_file = request.files.get('image', None)

    # Validate URL
    if not is_valid_url(url):
        flash('Invalid URL. Please provide a valid URL.', 'danger')
        return redirect(request.referrer)

    # Validate colors and default to black if invalid
    if not (is_valid_hex_color(color) or color in matplotlib.colors.CSS4_COLORS):
        color = "black"

    # Handle gradient or circle pattern input
    if gradient_color != "none":
        background_color = "white"  # Background color is ignored for gradients

    if shape == "circle":
        gradient_color = "none"  # Gradient is ignored for circles
        background_color = "white"  # Background is ignored for circles
        color = "black"  # Default color for circle pattern

    # QR code customization
    gradient_mapping = {
        "red-yellow": ["#FF0000", "#FFFF00"],
        "blue-green": ["#0000FF", "#00FF00"],
        "purple-pink": ["#800080", "#FFC0CB"],
        "orange-teal": ["#FFA500", "#008080"],
        "black-white": ["#000000", "#FFFFFF"]
    }
    gradient_colors = gradient_mapping.get(gradient_color, None)
    size_mapping = {'small': 5, 'standard': 10, 'medium': 15, 'large': 20}
    box_size = size_mapping.get(size, 10)

    qr = qrcode.QRCode(
        version=1, box_size=box_size, border=4, error_correction=qrcode.constants.ERROR_CORRECT_H
    )
    qr.add_data(url)
    qr.make(fit=True)

    if gradient_colors:
        img = create_gradient_qr(qr, gradient_colors, background_color, shape)
    elif shape == "circle":
        img = qr.make_image(
            fill_color=color,
            back_color=background_color,
            image_factory=StyledPilImage,
            module_drawer=CircleModuleDrawer()
        )
    else:
        img = qr.make_image(fill_color=color, back_color=background_color)

    img = img.convert("RGBA")

    if image_file and image_file.filename != '':
        img = add_image_to_qr(img, image_file)

    filename = 'qr_code.png'
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    img.save(file_path, format='PNG')

    session['last_qr_file'] = filename  # Save the last generated QR code filename
    flash('QR Code generated successfully!', 'success')
    return redirect(url_for('display_qr', filename=filename))

@app.route('/display_qr/<filename>')
def display_qr(filename):
    if 'user' not in session:
        flash('Please log in to access this feature.', 'warning')
        return redirect(url_for('login'))

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        flash('QR Code not found.', 'danger')
        return redirect(url_for('home'))

    # Determine the appropriate "Back Home" link
    if session.get('role') == 'admin':
        back_url = url_for('admin_dashboard')
    elif session.get('is_premium'):
        back_url = url_for('premium')
    else:
        back_url = url_for('home')

    return render_template(
        'display_qr.html',
        filename=filename,
        back_url=back_url,
        timestamp=os.path.getmtime(file_path)
    )

@app.route('/generate_business_card', methods=['GET', 'POST'])
def generate_business_card():
    if 'user' not in session:
        flash('Please log in to access this feature.', 'warning')
        return redirect(url_for('login'))

    qr_code_path = url_for('static', filename=f'uploads/{session.get("last_qr_file", "qr_code.png")}')

    if request.method == 'POST':
        company_name = request.form.get('company_name', '').strip()
        name = request.form.get('name', '').strip()
        position = request.form.get('position', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        website = request.form.get('website', '').strip()

        return render_template(
            'display_business_card.html',
            company_name=company_name,
            name=name,
            position=position,
            phone=phone,
            email=email,
            website=website,
            qr_code_path=qr_code_path,
            back_url=url_for('generate_business_card'),
        )

    # Determine the appropriate "Back Home" link
    if session.get('role') == 'admin':
        back_url = url_for('admin_dashboard')
    elif session.get('is_premium'):
        back_url = url_for('premium')
    else:
        back_url = url_for('home')

    return render_template('business_card_form.html', back_url=back_url)

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash('File not found.', 'danger')
        return redirect(url_for('home'))

def create_gradient_qr(qr, gradient_colors, background_color, shape):
    qr_image = qr.make_image(fill_color="black", back_color=background_color).convert("RGBA")
    qr_width, qr_height = qr_image.size

    gradient = Image.new("RGBA", (qr_width, qr_height))
    draw = ImageDraw.Draw(gradient)

    for y in range(qr_height):
        ratio = y / qr_height
        r1, g1, b1 = ImageColor.getrgb(gradient_colors[0])
        r2, g2, b2 = ImageColor.getrgb(gradient_colors[1])
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        draw.line([(0, y), (qr_width, y)], fill=(r, g, b))

    gradient_qr = Image.new("RGBA", (qr_width, qr_height))
    for x in range(qr_width):
        for y in range(qr_height):
            pixel = qr_image.getpixel((x, y))
            if pixel[0] == 0:
                gradient_pixel = gradient.getpixel((x, y))
                gradient_qr.putpixel((x, y), gradient_pixel)
            else:
                gradient_qr.putpixel((x, y), (255, 255, 255, 0))

    if shape == "circle":
        mask = Image.new("L", (qr_width, qr_height), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse([(0, 0), (qr_width, qr_height)], fill=255)
        gradient_qr = ImageOps.fit(gradient_qr, mask.size, centering=(0.5, 0.5))
        gradient_qr.putalpha(mask)

    return gradient_qr

def add_image_to_qr(qr_image, image_file):
    overlay = Image.open(image_file).convert("RGBA")
    qr_width, qr_height = qr_image.size

    overlay_size = int(qr_width * 0.3)
    overlay = overlay.resize((overlay_size, overlay_size), Image.Resampling.LANCZOS)

    position = ((qr_width - overlay.width) // 2, (qr_height - overlay.height) // 2)

    qr_image_with_overlay = qr_image.convert("RGBA")
    qr_image_with_overlay.paste(overlay, position, overlay)

    return qr_image_with_overlay

if __name__ == "__main__":
    app.run(debug=True)