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
    total = sum(item['price'] * item['quantity'] for item in cart.values())
    return total


@app.route("/")
def home():
    flowers, addons = load_data()
    cart = session.get('cart', {})
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
    flower = request.form['flower']
    quantity = int(request.form['quantity'])
    flowers, addons = load_data()
    cart = session.get('cart', {})

    if flower not in flowers:
        flash("Invalid flower selected.")
        return redirect(url_for('home'))

    if flower in cart:
        cart[flower]['quantity'] += quantity
    else:
        cart[flower] = {
            'price': flowers[flower]['price'],
            'quantity': quantity
        }

    session['cart'] = cart
    session.modified = True
    flash(f"{quantity} {flower}(s) added to cart.")

    return redirect(url_for('home'))


@app.route('/remove_from_cart/<item>')
def remove_from_cart(item):
    cart = session.get('cart', {})

    if item in cart:
        del cart[item]
        session['cart'] = cart
        session.modified = True
        flash(f"Removed all {item} from the cart.")
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
    app.run(debug=True)
