from flask import Blueprint, request, render_template, redirect, url_for
from app import db
from app.models import Product, Order, OrderItem
from flask_login import current_user, login_required
from datetime import datetime

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')

@orders_bp.route('/process_order', methods=['POST'])
@login_required
def process_order():
    product_ids = request.form.getlist('productId[]')
    quantities = request.form.getlist('quantity[]')
    prices = request.form.getlist('price[]')

    # Calculate total amount
    total_amount = sum(float(price) * int(quantity) for price, quantity in zip(prices, quantities))

    # Insert the order into the database
    order = Order(user_id=current_user.id, order_date_time=datetime.utcnow(), total_amount=total_amount)
    db.session.add(order)
    db.session.commit()

    # Insert order items
    for product_id, quantity, price in zip(product_ids, quantities, prices):
        if int(quantity) > 0:
            order_item = OrderItem(order_id=order.id, product_id=int(product_id), quantity=int(quantity), amount=float(price) * int(quantity))
            db.session.add(order_item)

    db.session.commit()

    return redirect(url_for('orders.checkout', order_id=order.id))


@orders_bp.route('/checkout/<int:order_id>')
@login_required
def checkout(order_id):
    order = Order.query.get_or_404(order_id)
    items = db.session.query(OrderItem, Product).join(Product).filter(OrderItem.order_id == order_id).all()

    return render_template('orders/checkout.html', order=order, items=items)


@orders_bp.route('/order-history', methods=['GET'])
@login_required
def order_history():
    orders = Order.query.filter_by(user_id=current_user.id).all()
    order_data = []

    for order in orders:
        # Get all items for this order
        items = OrderItem.query.filter_by(order_id=order.id).all()

        # Build the order data to include the product details
        item_data = []
        for item in items:
            # Access the product details through the relationship
            product = Product.query.get(item.product_id)
            item_data.append({
                'product_name': product.product_name,
                'price': product.price,
                'quantity': item.quantity,
                'total_price': item.amount  # This could also be item.quantity * product.price
            })

        order_data.append({
            'order': order,
            'items': item_data
        })

    return render_template('orders/order_history.html', orders=order_data)


# app/routes/orders.py

@orders_bp.route('/order_completed/<int:order_id>', methods=['GET'])
@login_required
def order_completed(order_id):
    # Fetch the order to confirm it was completed
    order = Order.query.get_or_404(order_id)

    # Ensure the order belongs to the current user
    if order.user_id != current_user.id:
        flash('You are not authorized to view this order.', 'danger')
        return redirect(url_for('orders.order_history'))

    # Render order completed page
    return render_template('orders/order_completed.html', order=order)
