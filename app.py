from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, make_response
from flask_pymongo import PyMongo
from datetime import datetime
import qrcode
from PIL import Image
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import CircleModuleDrawer, SquareModuleDrawer
import os
import re
from urllib.parse import urlparse
import matplotlib
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)

mongo_uri = os.getenv("MONGO_URI")
print(f"MONGO_URI: {mongo_uri}")

# Secret key for session management
app.secret_key = 'your_secret_key'

# MongoDB configuration
app.config["MONGO_URI"] = os.getenv("MONGO_URI")

mongo = PyMongo(app)

# Directory to save generated QR codes
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

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

        # Implement login logic here
        user = mongo.db.users.find_one({'email': username})
        if user and user['password'] == password:
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

        # Add user to MongoDB
        user_data = {
            'name': name,
            'email': email,
            'password': password,
            'is_premium': False
        }
        mongo.db.users.insert_one(user_data)

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
    color = request.form.get('color', 'black')  # Get the selected color
    shape = request.form.get('shape', 'square')
    image_file = request.files.get('image', None)

    # Validate URL
    if not is_valid_url(url):
        flash('Invalid URL', 'danger')
        return redirect(url_for('home'))

    # Validate color (either hex or named color)
    if not (is_valid_hex_color(color) or is_valid_color_name(color)):
        flash('Invalid color. Please enter a valid hex code or color name.', 'danger')
        return redirect(url_for('home'))

    # Ensure the color is properly formatted (e.g., RGB, hex, etc.)
    if color.startswith("rgb"):
        color = tuple(map(int, color[4:-1].split(", ")))  # Convert "rgb(r, g, b)" to a tuple (r, g, b)
    elif color.startswith("#"):
        color = color  # Hex color remains unchanged
    else:
        color = color  # Named colors (like 'red', 'blue') remain unchanged

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=5,
        error_correction=qrcode.constants.ERROR_CORRECT_H
    )
    qr.add_data(url)
    qr.make(fit=True)

    # Use StyledPilImage with shape (circle, square, or triangle)
    if shape == "circle":
        img = qr.make_image(
            fill_color=color,  # Color is applied here
            back_color="white",
            image_factory=StyledPilImage,
            module_drawer=CircleModuleDrawer(),
            eye_drawer=SquareModuleDrawer()  # Square eyes for the circular QR
        )
    elif shape == "triangle":
        img = qr.make_image(
            fill_color=color,  # Color is applied here
            back_color="white",
            image_factory=StyledPilImage,
            module_drawer=TriangleModuleDrawer(),  # Triangle modules
            eye_drawer=SquareModuleDrawer()  # Square eyes for the triangle QR
        )
    else:  # Default to square
        img = qr.make_image(fill_color=color, back_color="white")

    # Add image to the center if uploaded
    if image_file:
        img = add_image_to_qr(img, image_file)

    # Save QR image to file
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'qr_code.png')
    img.save(file_path, format='PNG')

    return send_file(file_path, mimetype='image/png', as_attachment=True)

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

# Define the custom TriangleModuleDrawer
class TriangleModuleDrawer:
    def __init__(self):
        self.fill_color = None

    def initialize(self, context, fill_color):
        # Initialize the color
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

# Premium features page
@app.route('/premium')
def premium():
    if 'user' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))
    return render_template('premium.html')

# Route for upgrading to premium (simulate a purchase)
@app.route('/upgrade_premium', methods=['POST'])
def upgrade_premium():
    if 'user' not in session:
        flash('Please log in to access this feature.', 'warning')
        return redirect(url_for('login'))

    user_email = session['user']
    # Update the user's premium status
    mongo.db.users.update_one({'email': user_email}, {'$set': {'is_premium': True}})

    # Record the sale
    sale_record = {
        'user_email': user_email,
        'amount': 10.0,  # Example premium cost
        'date': datetime.now()
    }
    mongo.db.sales.insert_one(sale_record)

    flash('Successfully upgraded to premium!', 'success')
    return redirect(url_for('home'))

# Route for admin page
@app.route('/admin', methods=['GET'])
def admin_dashboard():
    if 'user' not in session or session['user'] != 'admin@example.com':
        flash('Unauthorized access. Please log in as admin.', 'danger')
        return redirect(url_for('login'))

    # Retrieve user data from MongoDB
    users = list(mongo.db.users.find())
    user_count = len(users)
    premium_users = [user for user in users if user.get('is_premium')]
    premium_count = len(premium_users)

    # Retrieve sales data from MongoDB
    sales = mongo.db.sales.find()
    total_sales = sum(sale.get('amount', 0) for sale in sales)

    return render_template('admin.html', user_count=user_count, premium_count=premium_count, total_sales=total_sales)

if __name__ == "__main__":
    app.run(debug=True)
