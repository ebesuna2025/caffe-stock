from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# トップページ（在庫一覧）
@app.route("/")
def index():
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
    conn = sqlite3.connect("caffe2.db")
    cur = conn.cursor()
    if request.method == "POST":
        product_id = request.form["product_id"]
        transaction_type_id = request.form["transaction_type_id"]
        quantity = int(request.form["quantity"])
        user_id = request.form["user_id"]

        cur.execute("""
            INSERT INTO InventoryTransaction(ProductID, TransactionTypeID, Quantity, UserID, DateTime)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (product_id, transaction_type_id, quantity, user_id))
        conn.commit()

    # 商品一覧とユーザー一覧を取得してフォームに渡す
    cur.execute("SELECT ProductID, ItemName FROM Product")
    products = cur.fetchall()
    cur.execute("SELECT UserID, UserName FROM User")
    users = cur.fetchall()
    cur.execute("SELECT TransactionTypeID, TransactionTypeName FROM TransactionType")
    types = cur.fetchall()
    conn.close()
    return render_template("transaction.html", products=products, users=users, types=types)

# 商品新規登録
@app.route("/product_add", methods=["GET", "POST"])
def product_add():
    conn = sqlite3.connect("caffe2.db")
    cur = conn.cursor()

    if request.method == "POST":
        item_name = request.form["item_name"]
        category_id = request.form["category_id"]
        min_stock = request.form["min_stock"]
        stock = request.form["stock"]
        user_id = request.form["user_id"]

        cur.execute("""
            INSERT INTO Product(ItemName, ProductCategoryID, MinimumStockQuantity, StockQuantity, UserID)
            VALUES (?, ?, ?, ?, ?)
        """, (item_name, category_id, min_stock, stock, user_id))
        conn.commit()
        conn.close()
        return redirect("/")

    # Categoryテーブルから一覧取得
    cur.execute("SELECT ProductCategoryID, ProductCategoryName FROM ProductCategory")
    categories = [
        {"ProductCategoryID": row[0], "ProductCategoryName": row[1]}
        for row in cur.fetchall()
    ]

    # Userテーブルから一覧取得
    cur.execute("SELECT UserID, UserName FROM User")
    users = [
        {"UserID": row[0], "UserName": row[1]}
        for row in cur.fetchall()
    ]

    conn.close()
    return render_template("product_add.html", categories=categories, users=users)

# 入出庫履歴一覧
@app.route("/transaction_list")
def transaction_list():
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
            "TransactionDate": row[5],  # 表示用キー名はそのまま
        }
        for row in cur.fetchall()
    ]
    conn.close()
    return render_template("transaction_list.html", transactions=transactions)

if __name__ == "__main__":
    app.run(debug=True)