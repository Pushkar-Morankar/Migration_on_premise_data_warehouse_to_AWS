import os
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime, date
import plotly
import plotly.graph_objs as go
import json
import pandas as pd

app = Flask(__name__)

# PostgreSQL Configuration - IMPORTANT: REPLACE WITH YOUR ACTUAL CREDENTIALS
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Megaledon%4002@localhost/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class Customers(db.Model):
    __tablename__ = 'customers'
    customer_id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String)
    segment = db.Column(db.String)
    country = db.Column(db.String)
    city = db.Column(db.String)
    state = db.Column(db.String)
    postal_code = db.Column(db.String)
    region = db.Column(db.String)

class Orders(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer)
    product_id = db.Column(db.Integer)
    order_date = db.Column(db.Date)
    ship_date = db.Column(db.Date)
    ship_mode = db.Column(db.String)
    sales = db.Column(db.Float)

class Products(db.Model):
    __tablename__ = 'products'
    product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String)
    category = db.Column(db.String)
    sub_category = db.Column(db.String)

@app.route('/')
def dashboard():
    try:
        # Today's date
        today = date.today

        # Total Sales for Today
        total_sales = db.session.query(func.sum(Orders.sales)).filter(Orders.order_date == today).scalar() or 0
        total_sales = round(total_sales, 2)

        # Number of Orders Today
        total_orders = db.session.query(func.count(Orders.order_id)).filter(Orders.order_date == today).scalar() or 0

        # Top 5 Selling Products Today
        top_products = db.session.query(
            Products.product_name, 
            func.sum(Orders.sales).label('total_sales')
        ).join(Orders, Products.product_id == Orders.product_id)\
         .filter(Orders.order_date == today)\
         .group_by(Products.product_name)\
         .order_by(func.sum(Orders.sales).desc())\
         .limit(5).all()

        # Sales by Category
        category_sales = db.session.query(
            Products.category, 
            func.sum(Orders.sales).label('total_sales')
        ).join(Orders, Products.product_id == Orders.product_id)\
         .filter(Orders.order_date == today)\
         .group_by(Products.category)\
         .all()

        # Create Plotly Graphs
        top_products_graph = create_top_products_chart(top_products)
        category_sales_graph = create_category_sales_pie(category_sales)

        return render_template('dashboard.html', 
                               total_sales=total_sales, 
                               total_orders=total_orders,
                               top_products_graph=top_products_graph,
                               category_sales_graph=category_sales_graph)
    except Exception as e:
        # Log the error and return an error template
        print(f"Error in dashboard route: {e}")
        return render_template('error.html', error=str(e))

def create_top_products_chart(top_products):
    # Handle case when no data is available
    if not top_products:
        products = ['No Data']
        sales = [0]
    else:
        products = [product[0] for product in top_products]
        sales = [product[1] for product in top_products]

    trace = go.Bar(
        x=products,
        y=sales,
        marker=dict(color='rgba(50, 171, 96, 0.6)')
    )

    layout = go.Layout(
        title='Top 5 Products by Sales Today',
        xaxis=dict(title='Product Name'),
        yaxis=dict(title='Total Sales ($)')
    )

    fig = go.Figure(data=[trace], layout=layout)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON

def create_category_sales_pie(category_sales):
    # Handle case when no data is available
    if not category_sales:
        categories = ['No Data']
        sales = [1]
    else:
        categories = [category[0] for category in category_sales]
        sales = [category[1] for category in category_sales]

    trace = go.Pie(
        labels=categories,
        values=sales,
        hole=.3,
        marker=dict(colors=plotly.colors.qualitative.Pastel)
    )

    layout = go.Layout(
        title='Sales Distribution by Category Today'
    )

    fig = go.Figure(data=[trace], layout=layout)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON

# Add auto-refresh route
@app.route('/refresh_data')
def refresh_data():
    try:
        today = date.today
        
        # Fetch latest data
        total_sales = db.session.query(func.sum(Orders.sales)).filter(Orders.order_date == today).scalar() or 0
        total_orders = db.session.query(func.count(Orders.order_id)).filter(Orders.order_date == today).scalar() or 0

        return jsonify({
            'total_sales': round(total_sales, 2),
            'total_orders': total_orders
        })
    except Exception as e:
        print(f"Error in refresh_data route: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
    
    # Enable debug mode for detailed error messages
    app.run(debug=True)