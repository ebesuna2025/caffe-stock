from flask import Flask, render_template, request, redirect
import sqlite3, os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'caffe2.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 品目一覧
@app.route('/')
def index():
    conn = get_db_connection()
    products = conn.execute('''
        SELECT Product.ProductID,
               Product.ItemName,
               Product.StockQuantity,
               Product.MinimumStockQuantity,
               ProductCategory.ProductCategoryName
        FROM Product
        LEFT JOIN ProductCategory
          ON Product.ProductCategoryID = ProductCategory.ProductCategoryID
    ''').fetchall()
    conn.close()
    return render_template('index.html', products=products)

# 入出庫フォーム
@app.route('/transaction', methods=['GET', 'POST'])
def transaction():
    conn = get_db_connection()
    if request.method == 'POST':
        user_id = request.form['user_id']
        product_id = request.form['product_id']
        transaction_type = int(request.form['transaction_type'])
        quantity = int(request.form['quantity'])

        if transaction_type == 1:  # IN
            conn.execute('UPDATE Product SET StockQuantity = StockQuantity + ? WHERE ProductID = ?', (quantity, product_id))
        elif transaction_type == 2:  # OUT
            conn.execute('UPDATE Product SET StockQuantity = StockQuantity - ? WHERE ProductID = ?', (quantity, product_id))

        conn.execute('INSERT INTO InventoryTransaction (ProductID, TransactionTypeID, DateTime, UserID, Quantity) VALUES (?, ?, datetime("now"), ?, ?)',
                     (product_id, transaction_type, user_id, quantity))
        conn.commit()
        conn.close()
        return redirect('/')
    else:
        users = conn.execute('SELECT * FROM User').fetchall()
        products = conn.execute('SELECT * FROM Product').fetchall()
        types = conn.execute('SELECT * FROM TransactionType').fetchall()
        conn.close()
        return render_template('transaction.html', users=users, products=products, types=types)

# 商品一覧
@app.route('/products')
def products():
    conn = get_db_connection()
    products = conn.execute('''
        SELECT Product.ProductID,
               Product.ItemName,
               Product.StockQuantity,
               Product.MinimumStockQuantity,
               ProductCategory.ProductCategoryName,
               User.UserName AS CreatedBy
        FROM Product
        LEFT JOIN ProductCategory
          ON Product.ProductCategoryID = ProductCategory.ProductCategoryID
        LEFT JOIN User
          ON Product.CreatedByUserID = User.UserID
    ''').fetchall()
    conn.close()
    return render_template('products.html', products=products)

# 商品新規登録
@app.route('/product_add', methods=['GET','POST'])
def product_add():
    conn = get_db_connection()
    if request.method == 'POST':
        item_name = request.form['item_name']
        category_id = request.form['category_id']
        min_stock = request.form['min_stock']
        stock = request.form['stock']
        user_id = request.form['user_id']
        conn.execute('INSERT INTO Product (ItemName, ProductCategoryID, MinimumStockQuantity, StockQuantity, CreatedByUserID) VALUES (?, ?, ?, ?, ?)',
                     (item_name, category_id, min_stock, stock, user_id))
        conn.commit()
        conn.close()
        return redirect('/products')
    else:
        categories = conn.execute('SELECT * FROM ProductCategory').fetchall()
        users = conn.execute('SELECT * FROM User').fetchall()
        conn.close()
        return render_template('product_add.html', categories=categories, users=users)

# 商品編集
@app.route('/product_edit/<int:id>', methods=['GET','POST'])
def product_edit(id):
    conn = get_db_connection()
    if request.method == 'POST':
        item_name = request.form['item_name']
        min_stock = request.form['min_stock']
        stock = request.form['stock']
        conn.execute('UPDATE Product SET ItemName=?, MinimumStockQuantity=?, StockQuantity=? WHERE ProductID=?',
                     (item_name, min_stock, stock, id))
        conn.commit()
        conn.close()
        return redirect('/products')
    else:
        product = conn.execute('SELECT * FROM Product WHERE ProductID=?', (id,)).fetchone()
        conn.close()
        return render_template('product_edit.html', product=product)

# 商品削除
@app.route('/product_delete/<int:id>', methods=['POST'])
def product_delete(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM Product WHERE ProductID=?', (id,))
    conn.commit()
    conn.close()
    return redirect('/products')

if __name__ == '__main__':
    app.run(debug=True)