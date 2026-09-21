"""
app.py
------
Main program for the Online Shopping System.
Run this file to start the application:  python app.py

Structure of this file:
    1. USER FEATURES   (register, login, browse, cart, orders)
    2. ADMIN FEATURES  (login, manage products, manage orders)
    3. MENUS           (what the user sees on screen)
    4. MAIN PROGRAM    (the starting point)
"""

from database import get_connection


# ======================================================================
# 1. USER FEATURES
# ======================================================================

def register_user():
    """Create a new customer account."""
    print("\n--- USER REGISTRATION ---")
    name = input("Enter your name: ").strip()
    email = input("Enter your email: ").strip()
    password = input("Enter a password: ").strip()
    phone = input("Enter your phone number: ").strip()

    if not name or not email or not password or not phone:
        print("All fields are required.")
        return

    connection = get_connection()
    if connection is None:
        return

    try:
        cursor = connection.cursor()
        # Parameterized query (the %s placeholders) protects against SQL injection
        query = "INSERT INTO users (name, email, password, phone) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (name, email, password, phone))
        connection.commit()
        print("Registration successful! You can now log in.")
    except Exception as e:
        # Most common error here: email already used (UNIQUE constraint)
        print("Registration failed:", e)
    finally:
        cursor.close()
        connection.close()


def login_user():
    """
    Log a user in.
    Returns a dictionary with the user's details if successful,
    or None if the login fails.
    """
    print("\n--- USER LOGIN ---")
    email = input("Enter your email: ").strip()
    password = input("Enter your password: ").strip()

    connection = get_connection()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE email = %s AND password = %s"
        cursor.execute(query, (email, password))
        user = cursor.fetchone()

        if user:
            print(f"\nWelcome, {user['name']}!")
            return user
        else:
            print("Invalid email or password.")
            return None
    except Exception as e:
        print("Login failed:", e)
        return None
    finally:
        cursor.close()
        connection.close()


def display_products():
    """Show every product currently in the database."""
    connection = get_connection()
    if connection is None:
        return

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()

        if not products:
            print("No products available right now.")
            return

        print("\n{:<5} {:<20} {:<15} {:<10} {:<10}".format(
            "ID", "Name", "Category", "Price", "Stock"))
        print("-" * 65)
        for p in products:
            print("{:<5} {:<20} {:<15} {:<10} {:<10}".format(
                p['product_id'], p['product_name'], p['category'],
                float(p['price']), p['quantity']))
    except Exception as e:
        print("Could not fetch products:", e)
    finally:
        cursor.close()
        connection.close()


def search_product():
    """Search products by name or category."""
    keyword = input("\nEnter product name or category to search: ").strip()

    connection = get_connection()
    if connection is None:
        return

    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT * FROM products
            WHERE product_name LIKE %s OR category LIKE %s
        """
        like_pattern = f"%{keyword}%"
        cursor.execute(query, (like_pattern, like_pattern))
        results = cursor.fetchall()

        if not results:
            print("No matching products found.")
            return

        print("\n{:<5} {:<20} {:<15} {:<10} {:<10}".format(
            "ID", "Name", "Category", "Price", "Stock"))
        print("-" * 65)
        for p in results:
            print("{:<5} {:<20} {:<15} {:<10} {:<10}".format(
                p['product_id'], p['product_name'], p['category'],
                float(p['price']), p['quantity']))
    except Exception as e:
        print("Search failed:", e)
    finally:
        cursor.close()
        connection.close()


def add_to_cart(user):
    """Let the logged-in user add a product to their cart."""
    display_products()

    connection = get_connection()
    if connection is None:
        return

    try:
        product_id = int(input("\nEnter the Product ID to add to cart: "))
        quantity = int(input("Enter quantity: "))

        if quantity <= 0:
            print("Quantity must be greater than zero.")
            return

        cursor = connection.cursor(dictionary=True)

        # Check the product exists and has enough stock
        cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
        product = cursor.fetchone()

        if not product:
            print("Product not found.")
            return

        if product['quantity'] < quantity:
            print(f"Only {product['quantity']} units available in stock.")
            return

        # If this product is already in the user's cart, increase the quantity.
        # Otherwise, insert a new cart row.
        cursor.execute(
            "SELECT * FROM cart WHERE user_id = %s AND product_id = %s",
            (user['user_id'], product_id)
        )
        existing = cursor.fetchone()

        if existing:
            new_qty = existing['quantity'] + quantity
            cursor.execute(
                "UPDATE cart SET quantity = %s WHERE cart_id = %s",
                (new_qty, existing['cart_id'])
            )
        else:
            cursor.execute(
                "INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, %s)",
                (user['user_id'], product_id, quantity)
            )

        connection.commit()
        print("Product added to cart.")
    except ValueError:
        print("Please enter valid numbers for Product ID and quantity.")
    except Exception as e:
        print("Could not add to cart:", e)
    finally:
        cursor.close()
        connection.close()


def view_cart(user):
    """Show everything currently in the user's cart, with a grand total."""
    connection = get_connection()
    if connection is None:
        return

    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT p.product_name, p.price, c.quantity
            FROM cart c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.user_id = %s
        """
        cursor.execute(query, (user['user_id'],))
        items = cursor.fetchall()

        if not items:
            print("\nYour cart is empty.")
            return

        print("\n{:<20} {:<10} {:<10} {:<10}".format(
            "Product", "Price", "Quantity", "Subtotal"))
        print("-" * 55)

        grand_total = 0
        for item in items:
            subtotal = float(item['price']) * item['quantity']
            grand_total += subtotal
            print("{:<20} {:<10} {:<10} {:<10}".format(
                item['product_name'], float(item['price']),
                item['quantity'], subtotal))

        print("-" * 55)
        print(f"Grand Total: {grand_total}")
    except Exception as e:
        print("Could not fetch cart:", e)
    finally:
        cursor.close()
        connection.close()


def place_order(user):
    """
    Turn the user's cart into an order:
      1. Check stock is still available for every item.
      2. Create a row in 'orders'.
      3. Copy each cart item into 'order_items'.
      4. Reduce stock in 'products'.
      5. Empty the cart.
    """
    connection = get_connection()
    if connection is None:
        return

    try:
        cursor = connection.cursor(dictionary=True)

        # Get current cart items joined with product info
        cursor.execute("""
            SELECT c.cart_id, c.product_id, c.quantity, p.price, p.quantity AS stock, p.product_name
            FROM cart c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.user_id = %s
        """, (user['user_id'],))
        cart_items = cursor.fetchall()

        if not cart_items:
            print("\nYour cart is empty. Add products before placing an order.")
            return

        # Re-check stock in case it changed since items were added to the cart
        for item in cart_items:
            if item['quantity'] > item['stock']:
                print(f"Not enough stock for {item['product_name']}. "
                      f"Only {item['stock']} left.")
                return

        # Ask for delivery details
        print("\n--- PLACE ORDER ---")
        customer_name = input("Enter customer name: ").strip()
        address = input("Enter delivery address: ").strip()
        phone = input("Enter phone number: ").strip()

        if not customer_name or not address or not phone:
            print("All fields are required.")
            return

        total_amount = sum(float(item['price']) * item['quantity'] for item in cart_items)

        # 1. Create the order
        cursor.execute("""
            INSERT INTO orders (user_id, customer_name, address, phone, total_amount, order_status)
            VALUES (%s, %s, %s, %s, %s, 'Pending')
        """, (user['user_id'], customer_name, address, phone, total_amount))
        order_id = cursor.lastrowid

        # 2. Copy each cart item into order_items, and 3. reduce stock
        for item in cart_items:
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (%s, %s, %s, %s)
            """, (order_id, item['product_id'], item['quantity'], item['price']))

            cursor.execute("""
                UPDATE products SET quantity = quantity - %s WHERE product_id = %s
            """, (item['quantity'], item['product_id']))

        # 4. Empty the cart
        cursor.execute("DELETE FROM cart WHERE user_id = %s", (user['user_id'],))

        connection.commit()
        print(f"\nOrder placed successfully! Order ID: {order_id}, Total: {total_amount}")
    except Exception as e:
        connection.rollback()
        print("Order could not be placed:", e)
    finally:
        cursor.close()
        connection.close()


def view_orders(user):
    """Show the logged-in user's past orders and their status."""
    connection = get_connection()
    if connection is None:
        return

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT order_id, total_amount, order_status, order_date
            FROM orders
            WHERE user_id = %s
            ORDER BY order_date DESC
        """, (user['user_id'],))
        orders = cursor.fetchall()

        if not orders:
            print("\nYou have not placed any orders yet.")
            return

        print("\n{:<10} {:<12} {:<12} {:<20}".format(
            "Order ID", "Total", "Status", "Date"))
        print("-" * 55)
        for o in orders:
            print("{:<10} {:<12} {:<12} {:<20}".format(
                o['order_id'], float(o['total_amount']),
                o['order_status'], str(o['order_date'])))
    except Exception as e:
        print("Could not fetch orders:", e)
    finally:
        cursor.close()
        connection.close()


# ======================================================================
# 2. ADMIN FEATURES
# ======================================================================

def admin_login():
    """Log the admin in. Returns True if successful."""
    print("\n--- ADMIN LOGIN ---")
    username = input("Enter admin username: ").strip()
    password = input("Enter admin password: ").strip()

    connection = get_connection()
    if connection is None:
        return False

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM admin WHERE username = %s AND password = %s",
            (username, password)
        )
        admin = cursor.fetchone()

        if admin:
            print("Admin login successful!")
            return True
        else:
            print("Invalid admin credentials.")
            return False
    except Exception as e:
        print("Admin login failed:", e)
        return False
    finally:
        cursor.close()
        connection.close()


def add_product():
    """Admin: add a new product."""
    print("\n--- ADD PRODUCT ---")
    connection = get_connection()
    if connection is None:
        return

    try:
        name = input("Enter product name: ").strip()
        category = input("Enter category: ").strip()
        price = float(input("Enter price: "))
        quantity = int(input("Enter quantity: "))

        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO products (product_name, category, price, quantity)
            VALUES (%s, %s, %s, %s)
        """, (name, category, price, quantity))
        connection.commit()
        print("Product added successfully.")
    except ValueError:
        print("Price and quantity must be numbers.")
    except Exception as e:
        print("Could not add product:", e)
    finally:
        cursor.close()
        connection.close()


def update_product():
    """Admin: update an existing product's details."""
    display_products()
    connection = get_connection()
    if connection is None:
        return

    try:
        product_id = int(input("\nEnter Product ID to update: "))

        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
        product = cursor.fetchone()

        if not product:
            print("Product not found.")
            return

        print("Leave a field blank to keep its current value.")
        name = input(f"New name [{product['product_name']}]: ").strip()
        category = input(f"New category [{product['category']}]: ").strip()
        price_input = input(f"New price [{product['price']}]: ").strip()
        qty_input = input(f"New quantity [{product['quantity']}]: ").strip()

        name = name if name else product['product_name']
        category = category if category else product['category']
        price = float(price_input) if price_input else float(product['price'])
        quantity = int(qty_input) if qty_input else product['quantity']

        cursor.execute("""
            UPDATE products
            SET product_name = %s, category = %s, price = %s, quantity = %s
            WHERE product_id = %s
        """, (name, category, price, quantity, product_id))
        connection.commit()
        print("Product updated successfully.")
    except ValueError:
        print("Price and quantity must be numbers.")
    except Exception as e:
        print("Could not update product:", e)
    finally:
        cursor.close()
        connection.close()


def delete_product():
    """Admin: delete a product."""
    display_products()
    connection = get_connection()
    if connection is None:
        return

    try:
        product_id = int(input("\nEnter Product ID to delete: "))
        cursor = connection.cursor()
        cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
        connection.commit()

        if cursor.rowcount:
            print("Product deleted successfully.")
        else:
            print("Product not found.")
    except ValueError:
        print("Please enter a valid Product ID.")
    except Exception as e:
        # This usually happens if the product is already referenced in an order
        print("Could not delete product:", e)
    finally:
        cursor.close()
        connection.close()


def view_all_orders():
    """Admin: view every order placed by every customer."""
    connection = get_connection()
    if connection is None:
        return

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT o.order_id, u.name AS customer, o.total_amount, o.order_status, o.order_date
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            ORDER BY o.order_date DESC
        """)
        orders = cursor.fetchall()

        if not orders:
            print("\nNo orders have been placed yet.")
            return

        print("\n{:<10} {:<15} {:<12} {:<12} {:<20}".format(
            "Order ID", "Customer", "Total", "Status", "Date"))
        print("-" * 70)
        for o in orders:
            print("{:<10} {:<15} {:<12} {:<12} {:<20}".format(
                o['order_id'], o['customer'], float(o['total_amount']),
                o['order_status'], str(o['order_date'])))
    except Exception as e:
        print("Could not fetch orders:", e)
    finally:
        cursor.close()
        connection.close()


def update_order_status():
    """Admin: change the status of an order."""
    view_all_orders()
    connection = get_connection()
    if connection is None:
        return

    valid_statuses = ["Pending", "Confirmed", "Shipped", "Delivered", "Cancelled"]

    try:
        order_id = int(input("\nEnter Order ID to update: "))

        print("Choose new status:")
        for i, status in enumerate(valid_statuses, start=1):
            print(f"{i}. {status}")
        choice = int(input("Enter choice (1-5): "))

        if choice < 1 or choice > len(valid_statuses):
            print("Invalid choice.")
            return

        new_status = valid_statuses[choice - 1]

        cursor = connection.cursor()
        cursor.execute(
            "UPDATE orders SET order_status = %s WHERE order_id = %s",
            (new_status, order_id)
        )
        connection.commit()

        if cursor.rowcount:
            print(f"Order status updated to '{new_status}'.")
        else:
            print("Order not found.")
    except ValueError:
        print("Please enter valid numbers.")
    except Exception as e:
        print("Could not update order status:", e)
    finally:
        cursor.close()
        connection.close()


# ======================================================================
# 3. MENUS
# ======================================================================

def user_menu(user):
    """Menu shown after a customer logs in."""
    while True:
        print("\n===== USER MENU =====")
        print("1. View Products")
        print("2. Search Product")
        print("3. Add to Cart")
        print("4. View Cart")
        print("5. Place Order")
        print("6. My Orders")
        print("7. Logout")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            display_products()
        elif choice == "2":
            search_product()
        elif choice == "3":
            add_to_cart(user)
        elif choice == "4":
            view_cart(user)
        elif choice == "5":
            place_order(user)
        elif choice == "6":
            view_orders(user)
        elif choice == "7":
            print("Logged out.")
            break
        else:
            print("Invalid choice. Please try again.")


def admin_menu():
    """Menu shown after the admin logs in."""
    while True:
        print("\n===== ADMIN MENU =====")
        print("1. Add Product")
        print("2. View Products")
        print("3. Update Product")
        print("4. Delete Product")
        print("5. View Orders")
        print("6. Update Order Status")
        print("7. Logout")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            add_product()
        elif choice == "2":
            display_products()
        elif choice == "3":
            update_product()
        elif choice == "4":
            delete_product()
        elif choice == "5":
            view_all_orders()
        elif choice == "6":
            update_order_status()
        elif choice == "7":
            print("Admin logged out.")
            break
        else:
            print("Invalid choice. Please try again.")


# ======================================================================
# 4. MAIN PROGRAM
# ======================================================================

def main():
    while True:
        print("\n===== ONLINE SHOPPING SYSTEM =====")
        print("1. User Registration")
        print("2. User Login")
        print("3. Admin Login")
        print("4. Exit")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            register_user()
        elif choice == "2":
            user = login_user()
            if user:
                user_menu(user)
        elif choice == "3":
            if admin_login():
                admin_menu()
        elif choice == "4":
            print("Thank you for using the Online Shopping System. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
