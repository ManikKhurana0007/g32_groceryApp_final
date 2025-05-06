from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from flask_cors import CORS
import json


from flask import Flask, jsonify
from flask_cors import CORS




app = Flask(__name__)

app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///grocery.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(200), nullable=True)
    products = db.relationship('Product', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=True)
    stock = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    
    def __repr__(self):
        return f'<Product {self.name}>'

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    user = db.relationship('User', backref=db.backref('cart_items', lazy=True))
    product = db.relationship('Product', backref=db.backref('cart_items', lazy=True))
    
    def __repr__(self):
        return f'<CartItem {self.id}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    order_items = db.relationship('OrderItem', backref='order', lazy=True)
    
    def __repr__(self):
        return f'<Order {self.id}>'

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    product = db.relationship('Product', backref=db.backref('order_items', lazy=True))
    
    def __repr__(self):
        return f'<OrderItem {self.id}>'

# Helper functions
def get_cart_count():
    if 'user_id' in session:
        return CartItem.query.filter_by(user_id=session['user_id']).count()
    return 0

def get_cart_total():
    if 'user_id' in session:
        cart_items = CartItem.query.filter_by(user_id=session['user_id']).all()
        total = 0
        for item in cart_items:
            total += item.product.price * item.quantity
        return total
    return 0

# Routes
@app.route('/')
def home():
    categories = Category.query.all()
    featured_products = Product.query.limit(8).all()
    return render_template('index.html', 
                           categories=categories, 
                           products=featured_products, 
                           cart_count=get_cart_count())

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists!')
            return redirect(url_for('register'))
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already registered!')
            return redirect(url_for('register'))
        
        # Create new user
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html', cart_count=get_cart_count())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            flash('Login successful!')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password!')
    
    return render_template('login.html', cart_count=get_cart_count())



@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('is_admin', None)
    flash('You have been logged out.')
    return redirect(url_for('home'))

@app.route('/category/<int:category_id>')
def category(category_id):
    category = Category.query.get_or_404(category_id)
    products = Product.query.filter_by(category_id=category_id).all()
    return render_template('category.html', 
                           category=category, 
                           products=products, 
                           cart_count=get_cart_count())

@app.route('/product/<int:product_id>')
def product(product_id):
    product = Product.query.get_or_404(product_id)
    related_products = Product.query.filter_by(category_id=product.category_id).limit(4).all()
    return render_template('product.html', 
                           product=product, 
                           related_products=related_products, 
                           cart_count=get_cart_count())

@app.route('/search')
def search():
    query = request.args.get('query', '')
    products = Product.query.filter(Product.name.contains(query)).all()
    return render_template('search.html', 
                           products=products, 
                           query=query, 
                           cart_count=get_cart_count())

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        flash('Please login to add items to cart!')
        return redirect(url_for('login'))
    
    quantity = int(request.form.get('quantity', 1))
    
    # Check if product already in cart
    cart_item = CartItem.query.filter_by(user_id=session['user_id'], product_id=product_id).first()
    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=session['user_id'], product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
    
    db.session.commit()
    flash('Item added to cart!')
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        flash('Please login to view your cart!')
        return redirect(url_for('login'))
    
    cart_items = CartItem.query.filter_by(user_id=session['user_id']).all()
    total = get_cart_total()
    
    return render_template('cart.html', 
                           cart_items=cart_items, 
                           total=total, 
                           cart_count=get_cart_count())

@app.route('/update_cart/<int:item_id>', methods=['POST'])
def update_cart(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cart_item = CartItem.query.get_or_404(item_id)
    
    if cart_item.user_id != session['user_id']:
        flash('Unauthorized access!')
        return redirect(url_for('cart'))
    
    quantity = int(request.form.get('quantity', 1))
    
    if quantity <= 0:
        db.session.delete(cart_item)
    else:
        cart_item.quantity = quantity
    
    db.session.commit()
    flash('Cart updated!')
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:item_id>')
def remove_from_cart(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cart_item = CartItem.query.get_or_404(item_id)
    
    if cart_item.user_id != session['user_id']:
        flash('Unauthorized access!')
        return redirect(url_for('cart'))
    
    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from cart!')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cart_items = CartItem.query.filter_by(user_id=session['user_id']).all()
    
    if not cart_items:
        flash('Your cart is empty!')
        return redirect(url_for('cart'))
    
    total = get_cart_total()
    
    if request.method == 'POST':
        # Create order
        new_order = Order(user_id=session['user_id'], total_amount=total)
        db.session.add(new_order)
        db.session.flush()  # Get the order ID
        
        # Create order items
        for item in cart_items:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.product.price
            )
            db.session.add(order_item)
            
            # Update product stock
            product = Product.query.get(item.product_id)
            product.stock -= item.quantity
            
            # Remove from cart
            db.session.delete(item)
        
        db.session.commit()
        flash('Order placed successfully!')
        return redirect(url_for('order_confirmation', order_id=new_order.id))
    
    return render_template('checkout.html', 
                           cart_items=cart_items, 
                           total=total, 
                           cart_count=get_cart_count())

@app.route('/order_confirmation/<int:order_id>')
def order_confirmation(order_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    order = Order.query.get_or_404(order_id)
    
    if order.user_id != session['user_id']:
        flash('Unauthorized access!')
        return redirect(url_for('home'))
    
    return render_template('order_confirmation.html', 
                           order=order, 
                           cart_count=get_cart_count())

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    orders = Order.query.filter_by(user_id=session['user_id']).order_by(Order.order_date.desc()).all()
    return render_template('orders.html', 
                           orders=orders, 
                           cart_count=get_cart_count())

# Admin routes
@app.route('/admin')
def admin():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Unauthorized access!')
        return redirect(url_for('home'))
    
    products = Product.query.all()
    categories = Category.query.all()
    orders = Order.query.order_by(Order.order_date.desc()).all()
    
    return render_template('admin/dashboard.html', 
                           products=products, 
                           categories=categories, 
                           orders=orders)

# @app.route('/admin/add_category', methods=['GET', 'POST'])
# def add_category():
#     if 'user_id' not in session or not session.get('is_admin'):
#         flash('Unauthorized access!')
#         return redirect(url_for('home'))
    
#     if request.method == 'POST':
#         name = request.form.get('name')
        
#         # Handle image upload
#         image = None
#         if 'image' in request.files:
#             file = request.files['image']
#             if file.filename != '':
#                 filename = secure_filename(file.filename)
#                 file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#                 image = filename
        
#         new_category = Category(name=name, image=image)
#         db.session.add(new_category)
#         db.session.commit()
        
#         flash('Category added successfully!')
#         return redirect(url_for('admin'))
    
#     return render_template('admin/add_category.html')

@app.route('/admin/add_product', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Unauthorized access!')
        return redirect(url_for('home'))
    
    categories = Category.query.all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        stock = int(request.form.get('stock'))
        category_id = int(request.form.get('category_id'))
        
        # Handle image upload
        image = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image = filename
        
        new_product = Product(
            name=name,
            description=description,
            price=price,
            stock=stock,
            category_id=category_id,
            image=image
        )
        db.session.add(new_product)
        db.session.commit()
        
        flash('Product added successfully!')
        return redirect(url_for('admin'))
    
    return render_template('admin/add_product.html', categories=categories)

@app.route('/admin/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Unauthorized access!')
        return redirect(url_for('home'))
    
    product = Product.query.get_or_404(product_id)
    categories = Category.query.all()
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price'))
        product.stock = int(request.form.get('stock'))
        product.category_id = int(request.form.get('category_id'))
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                product.image = filename
        
        db.session.commit()
        flash('Product updated successfully!')
        return redirect(url_for('admin'))
    
    return render_template('admin/edit_product.html', product=product, categories=categories)

@app.route('/admin/delete_product/<int:product_id>')
def delete_product(product_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Unauthorized access!')
        return redirect(url_for('home'))
    
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    
    flash('Product deleted successfully!')
    return redirect(url_for('admin'))

@app.route('/admin/update_order_status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Unauthorized access!')
        return redirect(url_for('home'))
    
    order = Order.query.get_or_404(order_id)
    status = request.form.get('status')
    
    order.status = status
    db.session.commit()
    
    flash('Order status updated!')
    return redirect(url_for('admin'))

# Initialize database
@app.before_first_request
def create_tables():
    db.create_all()
    
    # Create admin user if not exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
        admin = User(username='admin', email='admin@example.com', password=hashed_password, is_admin=True)
        db.session.add(admin)
        
        # Create sample categories
        categories = [
            {'name': 'Fruits & Vegetables', 'image': 'fruits.jpg'},
            {'name': 'Dairy & Eggs', 'image': 'dairy.jpg'},
            {'name': 'Bakery', 'image': 'bakery.jpg'},
            {'name': 'Beverages', 'image': 'beverages.jpg'},
            {'name': 'Snacks', 'image': 'snacks.jpg'}
        ]
        
        for cat in categories:
            category = Category(name=cat['name'], image=cat['image'])
            db.session.add(category)
        
        db.session.commit()
        
        # Get category IDs
        fruits = Category.query.filter_by(name='Fruits & Vegetables').first()
        dairy = Category.query.filter_by(name='Dairy & Eggs').first()
        bakery = Category.query.filter_by(name='Bakery').first()
        beverages = Category.query.filter_by(name='Beverages').first()
        snacks = Category.query.filter_by(name='Snacks').first()
        
        # Create sample products
        products = [
            {'name': 'Apple', 'description': 'Fresh red apples', 'price': 1.99, 'stock': 100, 'category_id': fruits.id, 'image': 'apple.jpg'},
            {'name': 'Banana', 'description': 'Ripe yellow bananas', 'price': 0.99, 'stock': 150, 'category_id': fruits.id, 'image': 'banana.jpg'},
            {'name': 'Milk', 'description': 'Fresh whole milk', 'price': 2.49, 'stock': 50, 'category_id': dairy.id, 'image': 'milk.jpg'},
            {'name': 'Eggs', 'description': 'Farm fresh eggs', 'price': 3.99, 'stock': 60, 'category_id': dairy.id, 'image': 'eggs.jpg'},
            {'name': 'Bread', 'description': 'Freshly baked bread', 'price': 2.29, 'stock': 40, 'category_id': bakery.id, 'image': 'bread.jpg'},
            {'name': 'Water', 'description': 'Bottled mineral water', 'price': 1.49, 'stock': 200, 'category_id': beverages.id, 'image': 'water.jpg'},
            {'name': 'Chips', 'description': 'Potato chips', 'price': 2.99, 'stock': 80, 'category_id': snacks.id, 'image': 'chips.jpg'}
        ]
        
        for prod in products:
            product = Product(
                name=prod['name'],
                description=prod['description'],
                price=prod['price'],
                stock=prod['stock'],
                category_id=prod['category_id'],
                image=prod['image']
            )
            db.session.add(product)
        
        db.session.commit()



@app.context_processor
def inject_cart_count():
    from flask import session
    cart = session.get('cart', {})  # Get the cart from the session
    cart_count = sum(cart.values())  # Count how many items are in the cart
    return dict(cart_count=cart_count)





@app.route('/add_category', methods=['GET', 'POST'])
def add_category():
    if request.method == 'POST':
        name = request.form['name']
        image_file = request.files['image']
        image_filename = None

        if image_file and image_file.filename != '':
            image_filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image_file.save(image_path)

        new_category = Category(name=name, image=image_filename)
        db.session.add(new_category)
        db.session.commit()
        flash('Category added successfully!', 'success')
        return redirect(url_for('add_category'))

    categories = Category.query.all()
    return render_template('admin/add_category.html', categories=categories)


@app.route('/delete_category', methods=['POST'])
def delete_category():
    category_id = request.form.get('category_id')
    if category_id:
        category = Category.query.get(category_id)
        if category:
            db.session.delete(category)
            db.session.commit()
            flash(f"Category '{category.name}' deleted successfully.", 'success')
        else:
            flash("Category not found.", 'danger')
    else:
        flash("Invalid category selection.", 'warning')
    return redirect(url_for('add_category'))









# Sample data for our APIs
about_us_data = {
    "title": "About Our Grocery Delivery Service",
    "mission": "To provide fresh, high-quality groceries to your doorstep with unmatched convenience and reliability.",
    "history": "Founded in 2020, we started as a small local delivery service and have grown to serve thousands of customers across multiple cities.",
    "team": [
        {
            "name": "John Doe",
            "position": "CEO & Founder",
            "bio": "John has over 15 years of experience in retail and e-commerce."
        },
        {
            "name": "Jane Smith",
            "position": "Head of Operations",
            "bio": "Jane ensures that all deliveries are made on time and with care."
        },
        {
            "name": "Mike Johnson",
            "position": "Chief Technology Officer",
            "bio": "Mike leads our tech team to create seamless online shopping experiences."
        }
    ],
    "values": [
        "Customer Satisfaction",
        "Quality Products",
        "Timely Delivery",
        "Environmental Responsibility"
    ]
}

contact_us_data = {
    "title": "Contact Us",
    "description": "We're here to help! Reach out to us through any of the following channels:",
    "email": "support@grocerydelivery.com",
    "phone": "+1 (555) 123-4567",
    "hours": "Monday to Friday: 8am - 8pm, Saturday and Sunday: 9am - 6pm",
    "address": {
        "street": "123 Grocery Lane",
        "city": "Fresh City",
        "state": "FC",
        "zip": "12345"
    },
    "social_media": {
        "facebook": "facebook.com/grocerydelivery",
        "twitter": "twitter.com/grocerydelivery",
        "instagram": "instagram.com/grocerydelivery"
    },
    "faq": [
        {
            "question": "How do I track my order?",
            "answer": "You can track your order by logging into your account and visiting the 'Orders' section."
        },
        {
            "question": "What is your return policy?",
            "answer": "If you're not satisfied with any product, you can return it within 24 hours of delivery."
        },
        {
            "question": "Do you deliver to my area?",
            "answer": "We currently deliver to most major cities. Enter your zip code on our homepage to check availability."
        }
    ]
}

@app.route('/api/about-us', methods=['GET'])
def about_us():
    return jsonify(about_us_data)

@app.route('/api/contact-us', methods=['GET'])
def contact_us():
    return jsonify(contact_us_data)

















# NEW 
















if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
