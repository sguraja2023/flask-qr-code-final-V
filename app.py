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

        # Validate the inputs
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Invalid email address!', 'danger')
            return redirect(url_for('signup'))

        if email in USER_DATA:
            flash('Email is already registered. Please log in.', 'warning')
            return redirect(url_for('login'))

        # Save user data (For a real app, save to a database securely)
        USER_DATA[email] = {"password": password, "role": "user"}
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
    color = request.form.get('color', 'black')  # Default color is black
    shape = request.form.get('shape', 'square')
    image_file = request.files.get('image', None)

    # Validate the input URL
    if not is_valid_url(url):
        flash('Invalid URL. Please provide a valid URL.', 'danger')
        return redirect(url_for('premium'))

    # Validate the color (accept HEX codes and named CSS colors)
    if not (is_valid_hex_color(color) or is_valid_color_name(color)):
        flash('Invalid color. Please enter a valid hex code or color name.', 'danger')
        return redirect(url_for('premium'))

    # Create the QR code object
    qr = qrcode.QRCode(
        version=1,  # Adjust for complexity or data size
        box_size=10,
        border=4,
        error_correction=qrcode.constants.ERROR_CORRECT_H  # High error correction
    )
    qr.add_data(url)
    qr.make(fit=True)

    # Generate the QR code image with the chosen shape and color
    if shape == "circle":
        img = qr.make_image(
            fill_color=color,
            back_color="white",
            image_factory=StyledPilImage,
            module_drawer=CircleModuleDrawer()
        )
    elif shape == "triangle":
        img = qr.make_image(
            fill_color=color,
            back_color="white",
            image_factory=StyledPilImage,
            module_drawer=TriangleModuleDrawer()
        )
    else:  # Default to square
        img = qr.make_image(fill_color=color, back_color="white")

    # Add a logo/image to the center of the QR code if provided
    if image_file and image_file.filename != '':
        img = add_image_to_qr(img, image_file)

    # Save the QR code image to the uploads folder
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'qr_code.png')
    img.save(file_path, format='PNG')

    # Provide the QR code file for download
    return send_file(file_path, mimetype='image/png', as_attachment=True)

# Function to add an image to the center of the QR code
def add_image_to_qr(qr_image, image_file):
    overlay = Image.open(image_file).convert("RGBA")  # Support transparency
    qr_width, qr_height = qr_image.size
    # Resize the overlay to 20% of the QR code's width and height
    overlay_size = int(qr_width * 0.2)
    overlay = overlay.resize((overlay_size, overlay_size), Image.Resampling.LANCZOS)

    # Calculate the center position
    position = ((qr_width - overlay.width) // 2, (qr_height - overlay.height) // 2)
    # Paste the overlay onto the QR code
    qr_image.paste(overlay, position, overlay)
    return qr_image

# Define the custom TriangleModuleDrawer for premium triangle shape QR codes
class TriangleModuleDrawer:
    def __init__(self):
        self.fill_color = None

    def initialize(self, context, fill_color):
        self.fill_color = fill_color
        context.fill_color = self.fill_color  # Store the fill color in the context

    def __call__(self, context, module_size, x, y):
        # Get the top-left corner of the module square
        left = x * module_size
        top = y * module_size
        right = (x + 1) * module_size
        bottom = (y + 1) * module_size

        # Create a triangle shape
        triangle = [(left, bottom), (right, bottom), ((left + right) / 2, top)]
        context.polygon(triangle, fill=context.fill_color)  # Use the fill color from context

# Admin dashboard route
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

# Premium features route
@app.route('/premium', methods=['GET', 'POST'])
def premium():
    if 'user' not in session:
        flash('Please log in to access premium features.', 'warning')
        return redirect(url_for('login'))
    return render_template('premium.html')

if __name__ == "__main__":
    app.run(debug=True)
