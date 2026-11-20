
import os
import sqlite3
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).with_name("nash_ai.db")

st.set_page_config(page_title="Nash.AI", page_icon="📊", layout="wide")


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            email TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT DEFAULT '',
            price REAL NOT NULL DEFAULT 0,
            stock INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            due_date TEXT,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            transaction_date TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS quotations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            description TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_price REAL NOT NULL,
            tax_percent REAL NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
        """)


def query_df(sql, params=()):
    with db() as con:
        return pd.read_sql_query(sql, con, params=params)


def money(value):
    return f"₹{float(value):,.2f}"


init_db()

st.sidebar.title("📊 Nash.AI")
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Customers", "Products & Stock", "Orders", "Quotations",
     "Income & Expenses", "AI Assistant", "Import / Export"]
)
st.sidebar.caption("Early MVP • Local database")
st.sidebar.info("Use fictional/sample data while testing. This MVP is not accounting or GST filing software.")

if page == "Dashboard":
    st.title("Business dashboard")
    orders = query_df("SELECT * FROM orders")
    customers = query_df("SELECT * FROM customers")
    products = query_df("SELECT * FROM products")
    tx = query_df("SELECT * FROM transactions")
    pending = int((orders["status"] == "Pending").sum()) if not orders.empty else 0
    revenue = float(tx.loc[tx["kind"] == "Income", "amount"].sum()) if not tx.empty else 0
    expenses = float(tx.loc[tx["kind"] == "Expense", "amount"].sum()) if not tx.empty else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Customers", len(customers))
    c2.metric("Products", len(products))
    c3.metric("Pending orders", pending)
    c4.metric("Recorded income", money(revenue))
    st.subheader("Financial snapshot")
    st.write(f"Recorded expenses: **{money(expenses)}**")
    st.write(f"Recorded net (income − expenses): **{money(revenue-expenses)}**")
    st.subheader("Upcoming / overdue orders")
    if not orders.empty:
        orders["due_date"] = pd.to_datetime(orders["due_date"], errors="coerce").dt.date
        today = date.today()
        due = orders[(orders["status"] != "Completed") & (orders["due_date"].notna())]
        due = due[due["due_date"] <= today]
        st.dataframe(due, use_container_width=True)
        if due.empty:
            st.success("No orders are due today or overdue.")
    else:
        st.info("Add orders to see reminders here.")

elif page == "Customers":
    st.title("Customers")
    with st.form("customer_form", clear_on_submit=True):
        name = st.text_input("Customer name")
        phone = st.text_input("Phone")
        email = st.text_input("Email")
        submitted = st.form_submit_button("Add customer")
    if submitted:
        if not name.strip():
            st.error("Customer name is required.")
        else:
            with db() as con:
                con.execute("INSERT INTO customers(name,phone,email,created_at) VALUES(?,?,?,?)",
                            (name.strip(), phone.strip(), email.strip(), datetime.now().isoformat(timespec="seconds")))
            st.success("Customer added.")
    st.dataframe(query_df("SELECT * FROM customers ORDER BY id DESC"), use_container_width=True)

elif page == "Products & Stock":
    st.title("Products and inventory")
    with st.form("product_form", clear_on_submit=True):
        name = st.text_input("Product name")
        sku = st.text_input("SKU / code")
        price = st.number_input("Selling price (₹)", min_value=0.0, step=10.0)
        stock = st.number_input("Opening stock", min_value=0, step=1)
        submitted = st.form_submit_button("Add product")
    if submitted:
        if not name.strip():
            st.error("Product name is required.")
        else:
            with db() as con:
                con.execute("INSERT INTO products(name,sku,price,stock) VALUES(?,?,?,?)",
                            (name.strip(), sku.strip(), price, int(stock)))
            st.success("Product added.")
    st.dataframe(query_df("SELECT * FROM products ORDER BY name"), use_container_width=True)
    st.caption("Stock is reduced when an order is marked Completed in this MVP.")

elif page == "Orders":
    st.title("Order tracking")
    customers = query_df("SELECT id,name FROM customers ORDER BY name")
    products = query_df("SELECT id,name,price,stock FROM products ORDER BY name")
    if customers.empty or products.empty:
        st.warning("Add at least one customer and one product before creating an order.")
    else:
        customer_map = {r["name"]: int(r["id"]) for _, r in customers.iterrows()}
        product_map = {r["name"]: r for _, r in products.iterrows()}
        with st.form("order_form", clear_on_submit=True):
            customer_name = st.selectbox("Customer", list(customer_map))
            product_name = st.selectbox("Product", list(product_map))
            quantity = st.number_input("Quantity", min_value=1, step=1)
            due = st.date_input("Due date", value=date.today())
            notes = st.text_input("Notes")
            submitted = st.form_submit_button("Create order")
        if submitted:
            p = product_map[product_name]
            with db() as con:
                con.execute("""INSERT INTO orders(customer_id,product_id,quantity,unit_price,status,due_date,notes,created_at)
                               VALUES(?,?,?,?,?,?,?,?)""",
                            (customer_map[customer_name], int(p["id"]), int(quantity), float(p["price"]),
                             "Pending", due.isoformat(), notes, datetime.now().isoformat(timespec="seconds")))
            st.success("Order created.")
    st.subheader("Update order status")
    all_orders = query_df("""SELECT o.id, c.name AS customer, p.name AS product, o.quantity,
                             o.unit_price, o.status, o.due_date, o.notes
                             FROM orders o LEFT JOIN customers c ON c.id=o.customer_id
                             LEFT JOIN products p ON p.id=o.product_id ORDER BY o.id DESC""")
    st.dataframe(all_orders, use_container_width=True)
    if not all_orders.empty:
        order_id = st.selectbox("Order ID", all_orders["id"].tolist())
        status = st.selectbox("New status", ["Pending", "In progress", "Dispatched", "Completed", "Cancelled"])
        if st.button("Save status"):
            with db() as con:
                old = con.execute("SELECT status,product_id,quantity FROM orders WHERE id=?", (int(order_id),)).fetchone()
                if old and status == "Completed" and old["status"] != "Completed":
                    stock_row = con.execute("SELECT stock FROM products WHERE id=?", (old["product_id"],)).fetchone()
                    if stock_row and stock_row["stock"] < old["quantity"]:
                        st.error("Not enough stock to complete this order.")
                    else:
                        con.execute("UPDATE products SET stock=stock-? WHERE id=?", (old["quantity"], old["product_id"]))
                        con.execute("UPDATE orders SET status=? WHERE id=?", (status, int(order_id)))
                        st.success("Order completed and stock updated.")
                else:
                    con.execute("UPDATE orders SET status=? WHERE id=?", (status, int(order_id)))
                    st.success("Order status updated.")

elif page == "Quotations":
    st.title("Quotation generator")
    with st.form("quotation_form", clear_on_submit=True):
        customer = st.text_input("Customer / company")
        description = st.text_input("Product or service description")
        qty = st.number_input("Quantity", min_value=0.01, value=1.0, step=1.0)
        unit_price = st.number_input("Unit price (₹)", min_value=0.0, step=10.0)
        tax = st.number_input("Tax percentage (for estimate only)", min_value=0.0, max_value=100.0, step=1.0)
        submitted = st.form_submit_button("Create quotation")
    if submitted:
        if not customer.strip() or not description.strip():
            st.error("Customer and description are required.")
        else:
            with db() as con:
                con.execute("""INSERT INTO quotations(customer_name,description,quantity,unit_price,tax_percent,created_at)
                               VALUES(?,?,?,?,?,?)""",
                            (customer.strip(), description.strip(), qty, unit_price, tax,
                             datetime.now().isoformat(timespec="seconds")))
            st.success("Quotation saved.")
    quotes = query_df("SELECT * FROM quotations ORDER BY id DESC")
    if not quotes.empty:
        quotes["Subtotal"] = quotes["quantity"] * quotes["unit_price"]
        quotes["Estimated tax"] = quotes["Subtotal"] * quotes["tax_percent"] / 100
        quotes["Estimated total"] = quotes["Subtotal"] + quotes["Estimated tax"]
        st.dataframe(quotes, use_container_width=True)
        selected = st.selectbox("Preview quotation ID", quotes["id"].tolist())
        q = quotes[quotes["id"] == selected].iloc[0]
        st.markdown(f"### QUOTATION #{int(q['id'])}")
        st.write(f"**Customer:** {q['customer_name']}")
        st.write(f"**Description:** {q['description']}")
        st.write(f"**Quantity:** {q['quantity']:g}")
        st.write(f"**Subtotal:** {money(q['Subtotal'])}")
        st.write(f"**Estimated tax:** {money(q['Estimated tax'])}")
        st.write(f"**Total:** {money(q['Estimated total'])}")
        st.caption("Tax is an estimate; confirm applicable tax rules with an accountant.")

elif page == "Income & Expenses":
    st.title("Income and expenses")
    with st.form("transaction_form", clear_on_submit=True):
        kind = st.selectbox("Type", ["Income", "Expense"])
        description = st.text_input("Description")
        amount = st.number_input("Amount (₹)", min_value=0.01, step=100.0)
        tx_date = st.date_input("Date", value=date.today())
        submitted = st.form_submit_button("Save transaction")
    if submitted:
        if not description.strip():
            st.error("Description is required.")
        else:
            with db() as con:
                con.execute("INSERT INTO transactions(kind,description,amount,transaction_date) VALUES(?,?,?,?)",
                            (kind, description.strip(), amount, tx_date.isoformat()))
            st.success("Transaction saved.")
    st.dataframe(query_df("SELECT * FROM transactions ORDER BY transaction_date DESC"), use_container_width=True)

elif page == "AI Assistant":
    st.title("Nash.AI assistant")
    st.caption("Optional AI feature. Never send confidential customer information without permission.")
    question = st.text_area("Ask about your business", placeholder="Which orders are pending?")
    if st.button("Ask Nash.AI"):
        orders = query_df("""SELECT o.id,c.name customer,p.name product,o.quantity,o.status,o.due_date
                            FROM orders o LEFT JOIN customers c ON c.id=o.customer_id
                            LEFT JOIN products p ON p.id=o.product_id""")
        customers = query_df("SELECT name,phone,email FROM customers")
        products = query_df("SELECT name,sku,price,stock FROM products")
        summary = (
            f"Orders: {orders.to_dict(orient='records')}\n"
            f"Customers: {customers.to_dict(orient='records')}\n"
            f"Products: {products.to_dict(orient='records')}"
        )
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.warning("OPENAI_API_KEY is not set. Basic business data is shown below.")
            st.write("Pending orders:", int((orders["status"] == "Pending").sum()) if not orders.empty else 0)
            st.dataframe(orders, use_container_width=True)
        else:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                response = client.responses.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
                    instructions=("You are Nash.AI, a careful small-business assistant. "
                                  "Use only the supplied records. State when data is missing. "
                                  "Do not invent payments, stock, dates, tax rules or commitments."),
                    input=f"Business records:\n{summary}\n\nUser question: {question}"
                )
                st.write(response.output_text)
            except Exception as exc:
                st.error(f"AI request failed: {exc}")

elif page == "Import / Export":
    st.title("Import and export")
    for table in ["customers", "products", "orders", "transactions", "quotations"]:
        data = query_df(f"SELECT * FROM {table}")
        st.subheader(table.title())
        st.download_button(
            f"Download {table}.csv",
            data=data.to_csv(index=False).encode("utf-8"),
            file_name=f"nash_{table}.csv",
            mime="text/csv",
            key=f"download_{table}"
        )
        uploaded = st.file_uploader(f"Import {table} CSV", type=["csv"], key=f"upload_{table}")
        if uploaded is not None:
            try:
                imported = pd.read_csv(uploaded)
                st.write(imported.head())
                st.warning("Import preview only. This MVP does not insert uploaded rows automatically.")
            except Exception as exc:
                st.error(f"Could not read CSV: {exc}")
