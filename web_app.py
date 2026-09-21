"""Deployment-ready Flask frontend for the online shopping database."""

import os
from decimal import Decimal, InvalidOperation
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database import get_connection

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "local-development-key-change-me")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("COOKIE_SECURE", "0") == "1"


def fetch_all(sql, params=()):
    connection = get_connection()
    if connection is None:
        return []
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def fetch_one(sql, params=()):
    rows = fetch_all(sql, params)
    return rows[0] if rows else None


def customer_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "admin_id" not in session:
            flash("Administrator login required.", "warning")
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped


def valid_password(stored, supplied):
    """Support the schema's original plaintext accounts and new password hashes."""
    try:
        return check_password_hash(stored, supplied)
    except (ValueError, TypeError):
        return stored == supplied


@app.context_processor
def layout_context():
    cart_count = 0
    if session.get("user_id"):
        row = fetch_one("SELECT COALESCE(SUM(quantity), 0) AS count FROM cart WHERE user_id = %s",
                        (session["user_id"],))
        cart_count = row["count"] if row else 0
    return {"cart_count": cart_count}


@app.route("/")
def index():
    search = request.args.get("q", "").strip()
    if search:
        term = f"%{search}%"
        products = fetch_all(
            """SELECT * FROM products
               WHERE product_name LIKE %s OR category LIKE %s
               ORDER BY product_name""", (term, term))
    else:
        products = fetch_all("SELECT * FROM products ORDER BY product_name")
    return render_template("index.html", products=products, search=search)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        if not all((name, email, phone, password)):
            flash("All fields are required.", "danger")
        else:
            connection = get_connection()
            if connection is None:
                flash("Database is unavailable. Please try again later.", "danger")
            else:
                cursor = connection.cursor()
                try:
                    cursor.execute(
                        """INSERT INTO users (name, email, password, phone)
                           VALUES (%s, %s, %s, %s)""",
                        (name, email, generate_password_hash(password), phone))
                    connection.commit()
                    flash("Registration successful. Please log in.", "success")
                    return redirect(url_for("login"))
                except Exception:
                    connection.rollback()
                    flash("That email is already registered or invalid.", "danger")
                finally:
                    cursor.close()
                    connection.close()
    return render_template("auth.html", mode="register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = fetch_one("SELECT * FROM users WHERE email = %s", (request.form.get("email", "").strip().lower(),))
        if user and valid_password(user["password"], request.form.get("password", "")):
            session.clear()
            session["user_id"] = user["user_id"]
            session["user_name"] = user["name"]
            return redirect(request.args.get("next") or url_for("index"))
        flash("Invalid email or password.", "danger")
    return render_template("auth.html", mode="login")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@app.post("/cart/add/<int:product_id>")
@customer_required
def add_to_cart(product_id):
    try:
        quantity = int(request.form.get("quantity", 1))
    except ValueError:
        quantity = 0
    product = fetch_one("SELECT * FROM products WHERE product_id = %s", (product_id,))
    if not product or quantity < 1:
        flash("Choose a valid quantity and product.", "danger")
        return redirect(url_for("index"))
    current = fetch_one("SELECT quantity FROM cart WHERE user_id = %s AND product_id = %s",
                        (session["user_id"], product_id))
    if (current["quantity"] if current else 0) + quantity > product["quantity"]:
        flash(f"Only {product['quantity']} units are available.", "warning")
        return redirect(request.referrer or url_for("index"))
    connection = get_connection()
    if connection is None:
        flash("Database is unavailable.", "danger")
    else:
        cursor = connection.cursor()
        try:
            if current:
                cursor.execute("UPDATE cart SET quantity = quantity + %s WHERE user_id = %s AND product_id = %s",
                               (quantity, session["user_id"], product_id))
            else:
                cursor.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, %s)",
                               (session["user_id"], product_id, quantity))
            connection.commit()
            flash("Added to cart.", "success")
        finally:
            cursor.close()
            connection.close()
    return redirect(request.referrer or url_for("index"))


@app.route("/cart")
@customer_required
def cart():
    items = fetch_all("""SELECT c.cart_id, c.quantity, p.product_id, p.product_name, p.price,
                                p.quantity AS stock, (c.quantity * p.price) AS subtotal
                         FROM cart c JOIN products p ON p.product_id = c.product_id
                         WHERE c.user_id = %s ORDER BY c.cart_id""", (session["user_id"],))
    total = sum((item["subtotal"] for item in items), Decimal("0"))
    return render_template("cart.html", items=items, total=total)


@app.post("/cart/update/<int:cart_id>")
@customer_required
def update_cart(cart_id):
    try:
        quantity = int(request.form.get("quantity", 0))
    except ValueError:
        quantity = 0
    item = fetch_one("""SELECT c.cart_id, p.quantity AS stock FROM cart c
                        JOIN products p ON p.product_id = c.product_id
                        WHERE c.cart_id = %s AND c.user_id = %s""", (cart_id, session["user_id"]))
    if item and 0 < quantity <= item["stock"]:
        connection = get_connection()
        if connection is None:
            flash("Database is unavailable. Please try again later.", "danger")
            return redirect(url_for("cart"))
        cursor = connection.cursor()
        cursor.execute("UPDATE cart SET quantity = %s WHERE cart_id = %s AND user_id = %s",
                       (quantity, cart_id, session["user_id"]))
        connection.commit()
        cursor.close()
        connection.close()
        flash("Cart updated.", "success")
    elif item and quantity == 0:
        return remove_cart(cart_id)
    else:
        flash("Quantity exceeds available stock.", "warning")
    return redirect(url_for("cart"))


@app.post("/cart/remove/<int:cart_id>")
@customer_required
def remove_cart(cart_id):
    connection = get_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM cart WHERE cart_id = %s AND user_id = %s", (cart_id, session["user_id"]))
        connection.commit()
        cursor.close()
        connection.close()
    flash("Item removed from cart.", "success")
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
@customer_required
def checkout():
    items = fetch_all("""SELECT c.product_id, c.quantity, p.product_name, p.price, p.quantity AS stock
                         FROM cart c JOIN products p ON p.product_id = c.product_id
                         WHERE c.user_id = %s""", (session["user_id"],))
    total = sum((item["price"] * item["quantity"] for item in items), Decimal("0"))
    if not items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("cart"))
    if request.method == "POST":
        name, address, phone = (request.form.get(field, "").strip()
                                for field in ("customer_name", "address", "phone"))
        if not all((name, address, phone)):
            flash("All delivery fields are required.", "danger")
            return render_template("checkout.html", items=items, total=total)
        connection = get_connection()
        if connection is None:
            flash("Database is unavailable.", "danger")
            return render_template("checkout.html", items=items, total=total)
        cursor = connection.cursor(dictionary=True)
        try:
            for item in items:
                cursor.execute("SELECT quantity FROM products WHERE product_id = %s FOR UPDATE", (item["product_id"],))
                stock = cursor.fetchone()["quantity"]
                if item["quantity"] > stock:
                    raise ValueError(f"Not enough stock for {item['product_name']}.")
            cursor.execute("""INSERT INTO orders
                (user_id, customer_name, address, phone, total_amount, order_status)
                VALUES (%s, %s, %s, %s, %s, 'Pending')""",
                           (session["user_id"], name, address, phone, total))
            order_id = cursor.lastrowid
            for item in items:
                cursor.execute("INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
                               (order_id, item["product_id"], item["quantity"], item["price"]))
                cursor.execute("UPDATE products SET quantity = quantity - %s WHERE product_id = %s",
                               (item["quantity"], item["product_id"]))
            cursor.execute("DELETE FROM cart WHERE user_id = %s", (session["user_id"],))
            connection.commit()
            flash(f"Order #{order_id} placed successfully.", "success")
            return redirect(url_for("orders"))
        except (ValueError, Exception) as error:
            connection.rollback()
            flash(str(error) if isinstance(error, ValueError) else "Could not place order.", "danger")
        finally:
            cursor.close()
            connection.close()
    return render_template("checkout.html", items=items, total=total)


@app.route("/orders")
@customer_required
def orders():
    customer_orders = fetch_all("""SELECT * FROM orders WHERE user_id = %s
                                   ORDER BY order_date DESC""", (session["user_id"],))
    return render_template("orders.html", orders=customer_orders, admin=False)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        admin = fetch_one("SELECT * FROM admin WHERE username = %s", (request.form.get("username", "").strip(),))
        if admin and valid_password(admin["password"], request.form.get("password", "")):
            session.clear()
            session["admin_id"] = admin["admin_id"]
            session["admin_name"] = admin["username"]
            return redirect(url_for("admin_dashboard"))
        flash("Invalid administrator credentials.", "danger")
    return render_template("auth.html", mode="admin")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    products = fetch_all("SELECT * FROM products ORDER BY product_id DESC")
    all_orders = fetch_all("""SELECT o.*, u.email FROM orders o JOIN users u ON u.user_id = o.user_id
                              ORDER BY o.order_date DESC""")
    return render_template("admin.html", products=products, orders=all_orders)


@app.post("/admin/products/save")
@admin_required
def save_product():
    product_id = request.form.get("product_id")
    try:
        name, category = request.form["product_name"].strip(), request.form["category"].strip()
        price, quantity = Decimal(request.form["price"]), int(request.form["quantity"])
        if not name or not category or price < 0 or quantity < 0:
            raise ValueError
    except (KeyError, InvalidOperation, ValueError):
        flash("Enter valid product details.", "danger")
        return redirect(url_for("admin_dashboard"))
    connection = get_connection()
    if connection is None:
        flash("Database is unavailable. Please try again later.", "danger")
        return redirect(url_for("admin_dashboard"))
    cursor = connection.cursor()
    if product_id:
        cursor.execute("""UPDATE products SET product_name=%s, category=%s, price=%s, quantity=%s
                          WHERE product_id=%s""", (name, category, price, quantity, product_id))
    else:
        cursor.execute("INSERT INTO products (product_name, category, price, quantity) VALUES (%s, %s, %s, %s)",
                       (name, category, price, quantity))
    connection.commit()
    cursor.close()
    connection.close()
    flash("Product saved.", "success")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/products/delete/<int:product_id>")
@admin_required
def delete_product(product_id):
    connection = get_connection()
    if connection is None:
        flash("Database is unavailable. Please try again later.", "danger")
        return redirect(url_for("admin_dashboard"))
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
        connection.commit()
        flash("Product deleted.", "success")
    except Exception:
        connection.rollback()
        flash("Product cannot be deleted if it is used by an order.", "warning")
    finally:
        cursor.close()
        connection.close()
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/orders/<int:order_id>/status")
@admin_required
def update_order_status(order_id):
    status = request.form.get("order_status", "")
    if status not in {"Pending", "Confirmed", "Shipped", "Delivered", "Cancelled"}:
        flash("Invalid order status.", "danger")
    else:
        connection = get_connection()
        if connection is None:
            flash("Database is unavailable. Please try again later.", "danger")
            return redirect(url_for("admin_dashboard"))
        cursor = connection.cursor()
        cursor.execute("UPDATE orders SET order_status = %s WHERE order_id = %s", (status, order_id))
        connection.commit()
        cursor.close()
        connection.close()
        flash("Order status updated.", "success")
    return redirect(url_for("admin_dashboard"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")
