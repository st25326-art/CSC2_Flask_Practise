from flask import Flask, flash, redirect, render_template, request, session, url_for
import json

app = Flask(__name__)
app.secret_key = 'supersecretkey'


def load_data():
    with open("data/flowers.json") as file:
        flowers = json.load(file)
    with open("data/addons.json") as file:
        addons = json.load(file)
    return flowers, addons


def calculate_total(cart):
    return sum(item['price'] * item['quantity'] for item in cart)


def make_cart_item(flower, details):
    if not flower:
        return None

    if not isinstance(details, dict):
        return None

    try:
        price = float(details['price'])
        quantity = int(details['quantity'])
    except (KeyError, TypeError, ValueError):
        return None

    addons = details.get('addons', [])
    if not isinstance(addons, list):
        addons = []

    if quantity < 1:
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
                item = make_cart_item(item.get('flower'), item)
                if item:
                    clean_cart.append(item)

    if clean_cart != cart:
        session['cart'] = clean_cart
        session.modified = True

    return clean_cart


@app.route("/")
def home():
    flowers, addons = load_data()
    cart = get_cart()
    total = calculate_total(cart)
    return render_template(
        "index.html",
        flowers=flowers,
        addons=addons,
        cart=cart,
        total=total
    )


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    flower = request.form.get('flower')
    try:
        quantity = int(request.form.get('quantity', 1))
    except ValueError:
        quantity = 1

    selected_addons = request.form.getlist('addons')
    flowers, addons = load_data()
    cart = get_cart()

    if flower not in flowers:
        flash("Invalid flower selected.")
        return redirect(url_for('home'))

    if quantity < 1:
        quantity = 1

    selected_addons = [
        addon for addon in selected_addons
        if addon in addons
    ]
    addon_total = sum(addons[addon]['price'] for addon in selected_addons)

    cart.append({
        'flower': flower,
        'addons': selected_addons,
        'price': flowers[flower]['price'] + addon_total,
        'quantity': quantity
    })

    session['cart'] = cart
    session.modified = True
    flash(f"Added {quantity} {flower} order to the cart.")

    return redirect(url_for('home'))


@app.route('/remove_from_cart/<int:item_index>')
def remove_from_cart(item_index):
    cart = get_cart()

    if 0 <= item_index < len(cart):
        removed_item = cart.pop(item_index)
        session['cart'] = cart
        session.modified = True
        flash(f"Removed {removed_item['flower']} from the cart.")
    else:
        flash("Item not found in cart")

    return redirect(url_for('home'))


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/order_history')
def order_history():
    return render_template('order_history.html')


@app.route('/invoices')
def invoices():
    return render_template('invoices.html')


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
