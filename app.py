import json
import datetime
from flask import Flask, render_template, request, session, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'csc2_flower_shop_key'

# Load flowers and addons data from JSON files
def load_data():
    with open('data/flowers.json') as f:
        flowers = json.load(f)
    with open('data/addons.json') as f:
        addons = json.load(f)
    return flowers, addons

# Calculate total cost based on cart contents and selected addons
def calculate_total(cart, selected_addons=None):
    if selected_addons is None:
        selected_addons = {}
    flower_subtotal = sum(item['price'] * item['quantity'] for item in cart)
    addon_subtotal = sum(selected_addons.values())
    total = flower_subtotal + addon_subtotal
    return total, flower_subtotal, addon_subtotal

def make_cart_item(flower, details):
    if not isinstance(details, dict):
        return None
    quantity = details.get('quantity', 0)
    price = details.get('price', 0)
    addons = details.get('addons', [])
    if not flower or quantity < 1:
        return None
    return {
        'flower': flower,
        'addons': addons,
        'price': price,
        'quantity': quantity
    }

def get_cart():
    cart = session.get('cart', [])
    clean_cart = []
    if isinstance(cart, dict):
        for flower, details in cart.items():
            item = make_cart_item(flower, details)
            if item:
                clean_cart.append(item)
    elif isinstance(cart, list):
        for item in cart:
            if isinstance(item, dict):
                cleaned = make_cart_item(item.get('flower'), item)
                if cleaned:
                    clean_cart.append(cleaned)
    session['cart'] = clean_cart
    session.modified = True
    return clean_cart

@app.route('/')
def home():
    flowers, addons = load_data()
    cart = get_cart()
    selected_addons = session.get('selected_addons', {})
    total, flower_subtotal, addon_subtotal = calculate_total(cart, selected_addons)
    return render_template(
        'index.html',
        flowers=flowers,
        addons=addons,
        cart=cart,
        total=total,
        flower_subtotal=flower_subtotal,
        addon_subtotal=addon_subtotal,
        selected_addons=selected_addons
    )

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    flower = request.form.get('flower')
    quantity = int(request.form.get('quantity', 1))
    flowers, _ = load_data()

    if flower not in flowers:
        flash("Flower not found.")
        return redirect(url_for('home'))

    price = flowers[flower]['price']
    cart = get_cart()

    for item in cart:
        if item['flower'] == flower:
            item['quantity'] += quantity
            session['cart'] = cart
            session.modified = True
            flash(f"{quantity} {flower}(s) added to cart.")
            return redirect(url_for('home'))

    cart.append({
        'flower': flower,
        'price': price,
        'quantity': quantity,
        'addons': []
    })
    session['cart'] = cart
    session.modified = True
    flash(f"{quantity} {flower}(s) added to cart.")
    return redirect(url_for('home'))

@app.route('/remove_from_cart/<flower>')
def remove_from_cart(flower):
    cart = get_cart()
    cart = [item for item in cart if item['flower'] != flower]
    session['cart'] = cart
    session.modified = True
    flash(f"Removed all {flower.capitalize()} from the cart.")
    return redirect(url_for('home'))

# Add selected addons to the session
@app.route('/select_addon', methods=['POST'])
def select_addon():
    selected_addons = {}
    _, addons = load_data()
    selected_keys = request.form.getlist('addons')
    if not selected_keys:
        flash("No add-ons selected.")
    else:
        for addon in selected_keys:
            if addon in addons:
                selected_addons[addon] = float(addons[addon]['price'])
        flash(f"{len(selected_addons)} add-on(s) added to cart.")
    session['selected_addons'] = selected_addons
    session.modified = True
    return redirect(url_for('home'))

# Clear cart and addons from session (cancel current order)
@app.route('/cancel_order', methods=['POST'])
def cancel_order():
    session.pop('cart', None)
    session.pop('selected_addons', None)
    session.modified = True
    flash("Order cancelled. Your cart has been emptied.")
    return redirect(url_for('home'))

# Checkout current order
@app.route('/checkout', methods=['POST'])
def checkout():
    customer_name = request.form.get('customer_name', '').strip().title()
    if not customer_name:
        flash("Customer name is required.")
        return redirect(url_for('home'))
    cart = get_cart()
    selected_addons = session.get('selected_addons', {})
    if not cart:
        flash("Your cart is empty.")
        return redirect(url_for('home'))
    total, flower_subtotal, addon_subtotal = calculate_total(cart, selected_addons)
    invoice_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    invoice_number = f"INV_{customer_name.replace(' ', '_')}_{invoice_date}"
    session.pop('cart', None)
    session.pop('selected_addons', None)
    session.modified = True
    return render_template('invoices.html',
        customer_name=customer_name,
        cart=cart,
        selected_addons=selected_addons,
        total=total,
        flower_subtotal=flower_subtotal,
        addon_subtotal=addon_subtotal,
        invoice_number=invoice_number,
        invoice_date=invoice_date
    )

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/order_history')
def order_history():
    return render_template('order_history.html')

if __name__ == '__main__':
    app.run(debug=True)
