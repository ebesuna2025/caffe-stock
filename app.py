from flask import Flask, render_template, request, redirect, session
import sqlite3
import hashlib

app = Flask(__name__)
app.secret_key = "secret_key"  # セッション管理用

def debug_session(prefix=""):
    # セッション内容と重要キーの有無を見やすく表示
    print(f"[DEBUG]{prefix} session = {dict(session)} | has_user_id = {'user_id' in session} | has_username = {'username' in session}")

# ログインページ
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()

        print(f"[DEBUG] /login POST try username='{username}'")
        conn = sqlite3.connect("caffe2.db")
        cur = conn.cursor()
        cur.execute("SELECT UserID FROM User WHERE UserName=? AND Password=?", (username, hashed_pw))
        user = cur.fetchone()
        conn.close()
        print(f"[DEBUG] /login DB fetch user={user}")

        if user:
            session["user_id"] = user[0]
            session["username"] = username
            debug_session(" after login")
            print("[DEBUG] /login success -> redirect '/'")
            return redirect("/")
        else:
            print("[DEBUG] /login failed (user not found or wrong password)")
            return "ログイン失敗しました"

    # GET
    debug_session(" GET /login")
    return render_template("login.html")

@app.route("/logout")
def logout():
    print("[DEBUG] /logout called -> clearing session ...")
    debug_session(" before logout")
    session.pop("user_id", None)
    session.pop("username", None)
    session.clear()
    debug_session(" after logout")
    print("[DEBUG] /logout redirect -> /login")
    return redirect("/login")

# トップページ（在庫一覧）
@app.route("/")
def index():
    print("[DEBUG] GET /")
    debug_session(" on /")
    # 未ログインならログインページへリダイレクト
    if "user_id" not in session:
        print("[DEBUG] not logged in -> redirect /login")
        return redirect("/login")

    print("[DEBUG] logged in -> show inventory list")
    conn = sqlite3.connect("caffe2.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT p.ProductID, c.ProductCategoryName, p.ItemName,
               p.StockQuantity, p.MinimumStockQuantity
        FROM Product p
        JOIN ProductCategory c ON p.ProductCategoryID = c.ProductCategoryID
    """)
    products = [
        {
            "ProductID": row[0],
            "ProductCategoryName": row[1],
            "ItemName": row[2],
            "StockQuantity": row[3],
            "MinimumStockQuantity": row[4],
        }
        for row in cur.fetchall()
    ]
    conn.close()
    return render_template("index.html", products=products)

# 入出庫フォーム
@app.route("/transaction", methods=["GET", "POST"])
def transaction():
    print("[DEBUG] /transaction accessed")
    debug_session(" on /transaction")
    if "user_id" not in session:
        print("[DEBUG] not logged in -> redirect /login (transaction)")
        return redirect("/login")

    conn = sqlite3.connect("caffe2.db")
    cur = conn.cursor()

    if request.method == "POST":
        user_id = request.form.get("user_id")
        product_id = request.form.get("product_id")
        transaction_type_id = request.form.get("transaction_type_id")
        quantity = int(request.form.get("quantity", "0"))

        print(f"[DEBUG] /transaction POST user_id={user_id}, product_id={product_id}, type={transaction_type_id}, qty={quantity}")
        cur.execute("""
            INSERT INTO InventoryTransaction(ProductID, TransactionTypeID, Quantity, UserID, DateTime)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (product_id, transaction_type_id, quantity, user_id))
        conn.commit()
        print("[DEBUG] /transaction POST committed")

    cur.execute("SELECT UserID, UserName FROM User")
    users = [{"UserID": row[0], "UserName": row[1]} for row in cur.fetchall()]

    cur.execute("SELECT ProductID, ItemName FROM Product")
    products = [{"ProductID": row[0], "ItemName": row[1]} for row in cur.fetchall()]

    cur.execute("SELECT TransactionTypeID, TransactionTypeName FROM TransactionType")
    types = [{"TransactionTypeID": row[0], "TransactionTypeName": row[1]} for row in cur.fetchall()]

    conn.close()
    return render_template("transaction.html", users=users, products=products, types=types)

# 商品新規登録
@app.route("/product_add", methods=["GET", "POST"])
def product_add():
    print("[DEBUG] /product_add accessed")
    debug_session(" on /product_add")
    if "user_id" not in session:
        print("[DEBUG] not logged in -> redirect /login (product_add)")
        return redirect("/login")

    conn = sqlite3.connect("caffe2.db")
    cur = conn.cursor()

    if request.method == "POST":
        item_name = request.form.get("item_name")
        category_id = request.form.get("category_id")
        min_stock = request.form.get("min_stock")
        stock = request.form.get("stock")
        user_id = request.form.get("user_id")

        print(f"[DEBUG] /product_add POST item='{item_name}', category_id={category_id}, min_stock={min_stock}, stock={stock}, user_id={user_id}")
        cur.execute("""
            INSERT INTO Product(ItemName, ProductCategoryID, MinimumStockQuantity, StockQuantity, UserID)
            VALUES (?, ?, ?, ?, ?)
        """, (item_name, category_id, min_stock, stock, user_id))
        conn.commit()
        conn.close()
        print("[DEBUG] /product_add POST committed -> redirect '/'")
        return redirect("/")

    cur.execute("SELECT ProductCategoryID, ProductCategoryName FROM ProductCategory")
    categories = [{"ProductCategoryID": row[0], "ProductCategoryName": row[1]} for row in cur.fetchall()]

    cur.execute("SELECT UserID, UserName FROM User")
    users = [{"UserID": row[0], "UserName": row[1]} for row in cur.fetchall()]

    conn.close()
    return render_template("product_add.html", categories=categories, users=users)

# 入出庫履歴一覧
@app.route("/transaction_list")
def transaction_list():
    print("[DEBUG] /transaction_list accessed")
    debug_session(" on /transaction_list")
    if "user_id" not in session:
        print("[DEBUG] not logged in -> redirect /login (transaction_list)")
        return redirect("/login")

    conn = sqlite3.connect("caffe2.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT it.TransactionID, p.ItemName, tt.TransactionTypeName,
               it.Quantity, u.UserName, it.DateTime
        FROM InventoryTransaction it
        JOIN Product p ON it.ProductID = p.ProductID
        JOIN TransactionType tt ON it.TransactionTypeID = tt.TransactionTypeID
        JOIN User u ON it.UserID = u.UserID
        ORDER BY it.DateTime DESC
    """)
    transactions = [
        {
            "TransactionID": row[0],
            "ItemName": row[1],
            "TransactionTypeName": row[2],
            "Quantity": row[3],
            "UserName": row[4],
            "TransactionDate": row[5],
        }
        for row in cur.fetchall()
    ]
    conn.close()
    return render_template("transaction_list.html", transactions=transactions)

# ユーザー登録ページ
@app.route("/user_add", methods=["GET", "POST"])
def user_add():
    print("[DEBUG] /user_add accessed")
    debug_session(" on /user_add")
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()

        print(f"[DEBUG] /user_add POST create username='{username}'")
        conn = sqlite3.connect("caffe2.db")
        cur = conn.cursor()
        cur.execute("INSERT INTO User(UserName, Password) VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
        conn.close()
        print("[DEBUG] /user_add POST committed -> redirect '/'")
        return redirect("/")

    return render_template("user_add.html")

# アプリ起動
if __name__ == "__main__":
    print("[DEBUG] app starting with debug=True")
    app.run(debug=True)