# Simple Online Shopping System (Python + MySQL)

A console-based shopping application built for a BCA project.
Customers can register, log in, browse/search products, manage a
cart, place orders, and view order history. An admin panel lets
the admin manage products and update order statuses.

No paid software, no paid APIs, no payment gateway — everything
runs locally with free tools.

---

## 1. Project Overview

- Customers can register, log in, browse and search products,
  add items to a cart, place an order, and check their order history.
- The admin can log in separately to add/update/delete products,
  view all orders, and update an order's status
  (Pending → Confirmed → Shipped → Delivered / Cancelled).
- All data is stored in a MySQL database called `online_shopping`.
- The interface is a simple text menu in the terminal — no GUI,
  no web framework, so it's easy to read and explain in a viva.

---

## 2. Folder / File Structure

```
online_shopping_system/
│
├── schema.sql        -> Run this once in MySQL to create the database and tables
├── database.py       -> Holds the MySQL connection details and get_connection()
├── app.py            -> The whole application: all features + menus + main()
├── requirements.txt  -> The one Python package this project needs
└── README.md         -> This file
```

Keeping the database connection in its own file (`database.py`)
means if your MySQL password ever changes, you only edit it in
one place.

---

## 3. MySQL Database Design

| Table         | Purpose                                             |
|---------------|------------------------------------------------------|
| `users`       | Customer accounts (name, email, password, phone)     |
| `products`    | Items for sale (name, category, price, stock)        |
| `cart`        | Items a user has added but not yet ordered            |
| `orders`      | One row per placed order (customer info, total, status) |
| `order_items` | The individual products inside each order (line items) |
| `admin`       | Admin login credentials                               |

**Relationships (foreign keys):**
- `cart.user_id` → `users.user_id`
- `cart.product_id` → `products.product_id`
- `orders.user_id` → `users.user_id`
- `order_items.order_id` → `orders.order_id`
- `order_items.product_id` → `products.product_id`

`order_items` exists because one order can contain many products —
this is a standard "one order, many line items" design, the same
pattern real shopping sites use.

The full SQL is in **`schema.sql`** — it creates the database,
every table (with `PRIMARY KEY`, `FOREIGN KEY`, `NOT NULL`, and a
`UNIQUE` email), the default admin login, and 8 sample products.

---

## 4. Installation Requirements

You need:
1. **Python 3.8+** — https://www.python.org/downloads/
2. **MySQL Server** (Community Edition, free) — https://dev.mysql.com/downloads/mysql/
3. **VS Code** or **PyCharm** (Community Edition, free)

Both MySQL and the tools above are completely free.

---

## 5. Installing the MySQL Connector

Open a terminal (or the terminal inside VS Code/PyCharm) and run:

```bash
pip install mysql-connector-python
```

or, using the requirements file included in this project:

```bash
pip install -r requirements.txt
```

---

## 6. Setting Up the Database

1. Open MySQL Workbench (or the `mysql` command line).
2. Open `schema.sql` and run the **entire file**. This will:
   - Create the `online_shopping` database
   - Create all 6 tables
   - Insert the default admin account
   - Insert 8 sample products

You can re-run it safely — every `CREATE TABLE` uses
`IF NOT EXISTS`, so it won't error out if you run it twice
(though re-running the `INSERT` statements will duplicate the
sample rows — that's fine for testing, just be aware of it).

---

## 7. Configuring the Database Connection

Open **`database.py`** and edit these three lines near the top:

```python
MYSQL_HOST = "localhost"
MYSQL_USER = "root"             # <-- your MySQL username
MYSQL_PASSWORD = ""             # <-- your MySQL password
MYSQL_DATABASE = "online_shopping"
```

Put in your own MySQL username and password (the ones you set up
when you installed MySQL). Never share your real password with
anyone else — this project intentionally leaves the password
field blank so you fill in your own.

---

## 8. How to Run the Project

**In VS Code:**
1. Open the `online_shopping_system` folder (File → Open Folder).
2. Open a terminal (Terminal → New Terminal).
3. Run:
   ```bash
   python app.py
   ```

**In PyCharm:**
1. Open the folder as a new project.
2. Right-click `app.py` → **Run 'app'**.

You should see the main menu appear in the terminal/console.

---

## 9. Sample Login Credentials

**Admin login** (created automatically by `schema.sql`):
- Username: `admin`
- Password: `admin123`

**User login:** there is no default customer account — use
option **1 (User Registration)** in the main menu to create one,
then log in with the same email and password.

---

## 10. Sample Products (already inserted by schema.sql)

| ID | Name          | Category     | Price   | Stock |
|----|---------------|--------------|---------|-------|
| 1  | Laptop        | Electronics  | 45000.00| 10    |
| 2  | Mobile Phone  | Electronics  | 15000.00| 20    |
| 3  | Headphones    | Electronics  | 1200.00 | 50    |
| 4  | Notebook      | Stationery   | 40.00   | 100   |
| 5  | Pen           | Stationery   | 10.00   | 200   |
| 6  | Backpack      | Accessories  | 900.00  | 30    |
| 7  | Water Bottle  | Accessories  | 250.00  | 40    |
| 8  | T-Shirt       | Clothing     | 500.00  | 60    |

---

## 11. Testing Steps

Follow this order to test everything end-to-end:

1. **Register** a new user (option 1 from the main menu).
2. **Log in** as that user (option 2).
3. **View Products** — confirm the 8 sample products appear.
4. **Search Product** — try searching "phone" and "Electronics".
5. **Add to Cart** — add a product, then add the same product
   again and confirm the quantity increases instead of creating
   a duplicate row.
6. **View Cart** — confirm subtotal and grand total are correct.
7. **Place Order** — enter delivery details and confirm you get
   an Order ID. Check that the product's stock decreased
   (View Products again) and the cart is now empty.
8. **My Orders** — confirm the order appears with status "Pending".
9. **Logout**, then log in as **Admin** (option 3, `admin`/`admin123`).
10. **View Orders** — confirm you can see the order from step 7.
11. **Update Order Status** — change it to "Shipped".
12. Log back in as the user and check **My Orders** again — the
    status should now show "Shipped".
13. As admin, try **Add Product**, **Update Product**, and
    **Delete Product** to confirm the admin panel works.
14. Try adding more items to a cart than are in stock — confirm
    you get an error instead of the order going through.

---

## 12. Common Errors and Solutions

| Error message | Cause | Solution |
|---|---|---|
| `Could not connect to the database` | Wrong username/password in `database.py`, or MySQL isn't running | Double-check `database.py`, and make sure the MySQL service is started |
| `Unknown database 'online_shopping'` | `schema.sql` was never run | Open `schema.sql` in MySQL and run the whole file |
| `ModuleNotFoundError: No module named 'mysql'` | The connector package isn't installed | Run `pip install mysql-connector-python` |
| `Duplicate entry '...' for key 'email'` | Trying to register with an email that's already used | Use a different email, or log in instead of registering again |
| Program crashes on non-numeric input | Typing text where a number is expected (e.g. Product ID) | The program already catches this with `try/except`; if it still happens, make sure you didn't edit those blocks out |
| `Cannot delete or update a parent row: a foreign key constraint fails` | Trying to delete a product that's already part of an existing order | This is expected behavior — order history should not disappear when a product is removed. Consider marking products as "unavailable" instead in a future version |

## 13. Web deployment

The Flask version is started with `web_app.py` (the original `app.py`
console program is unchanged):

```bash
pip install -r requirements.txt
flask --app web_app run
# production: gunicorn --workers 2 --threads 4 web_app:app
```

`Procfile` contains the production Gunicorn command for Render, Heroku, and
similar hosts. Configure `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`,
`MYSQL_DATABASE`, and a long random `FLASK_SECRET_KEY` as platform
environment variables. `.env.example` documents the names without exposing
credentials. Run `schema.sql` against the managed MySQL database before
starting the web service. Customer passwords created by the web app are
hashed; the original sample admin account remains compatible.

Web routes include customer registration/login, product search, cart and
checkout, order history, and an `/admin` dashboard for product and order
management. The web app uses parameterized MySQL queries and signed Flask
sessions. in a future version |

---

## 13. Explanation of Major Parts (for Viva)

**`database.py`**
A single function, `get_connection()`, that opens a connection to
MySQL using the `mysql-connector-python` library. Every other
function calls this whenever it needs to talk to the database,
and closes the connection when it's done. Keeping this in one
place means the connection logic is written only once.

**Parameterized queries (`%s` placeholders)**
Every SQL query in `app.py` uses `%s` placeholders with the actual
values passed in as a separate tuple, e.g.:
```python
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
```
This is safer than building a query by joining strings together,
because it prevents **SQL injection** — a common attack where a
user types SQL code into an input box to manipulate your query.

**`try / except` blocks**
Used everywhere user input is read or a database call is made, so
that one bad input (like typing text instead of a number) or one
failed query doesn't crash the whole program — it just prints an
error and returns to the menu.

**Cart → Order flow**
The cart table holds items temporarily. When `place_order()` runs,
it: (1) re-checks stock is still available, (2) creates one row in
`orders`, (3) copies each cart item into `order_items` (this is
why there are two separate tables — one order can have many
items), (4) reduces stock in `products`, and (5) empties the
cart. This mirrors how real e-commerce systems separate an "order"
from its "line items."

**Menus (`user_menu`, `admin_menu`, `main`)**
Each menu is just a `while True` loop that prints options, reads
the user's choice, and calls the matching function. `main()` is
the entry point — it's the first thing that runs when you type
`python app.py`, and it decides whether to show the registration
screen, hand off to `user_menu()`, or hand off to `admin_menu()`.

---

## Notes / Possible Extensions (not required, just ideas)

- Passwords are stored in plain text for simplicity, which is
  fine for a college project but should never be done in a real
  product — real systems hash passwords (e.g. with `bcrypt`).
- No payment gateway or online AI features were added, per the
  project requirements — this keeps the project focused and
  appropriate for a BCA submission.
