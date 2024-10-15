from flask import Blueprint, render_template, current_app,request, jsonify, redirect, url_for
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import os

sales = Blueprint("sales", __name__, static_folder="static", template_folder="templates")

@sales.route("/")
def main():
    current_app.current_page = "sales"

    date = current_app.current_date
    day = current_app.days_of_the_week[current_app.current_date.weekday()]
    funds = current_app.funds
    sales_modifiers_list = current_app.sales_modifiers_list

    customer_order_dict = {order[0]: order[2] for order in current_app.customer_order_list}

    #past sales price generation is done for 29 days after that todays info is added here
    if len(current_app.product_sale_price_past_list) < 30:
        current_day_product_sale_price_list = [{'id': product.id, 'sale_price': product.sale_price, 'date': current_app.current_date} for product in current_app.products]
        current_app.product_sale_price_past_list.append(current_day_product_sale_price_list)

    selected_product = current_app.products[0].id
    sale_prices = [product["sale_price"] for day in current_app.product_sale_price_past_list for product in day if product["id"] == selected_product]
    dates = [product["date"] for day in current_app.product_sale_price_past_list for product in day if product["id"] == selected_product]

    y = sale_prices
    x = dates
    aspect_ratio = (8, 5)

    fig, ax = plt.subplots(figsize=aspect_ratio)
    ax.plot(x, y, 'o-',  color='black', linewidth=2)
    ax.plot(x, y, 'o', color='red')
    plt.grid(True)
    plt.tight_layout()
    fig.autofmt_xdate()

    basedir = os.path.abspath(os.path.dirname(__file__))
    plt.savefig( os.path.join(basedir, "static", "plot.png"))
    plt.close(fig)

    return render_template("sales.html", date=date, funds=funds, day=day, products=current_app.products, selling_dict = current_app.selling_dict,
                            warehouse=current_app.warehouse, customer_order_list=current_app.customer_order_list, customer_order_dict=customer_order_dict,
                            inventory = current_app.warehouse.product_storage, sales_modifiers_list=sales_modifiers_list)

@sales.route("/sell_product", methods=["GET", "POST"])
def sales_sell_product():
    try:
        selling_dict = request.get_json()["data"]
        total_funds_gained = 0
        for item in selling_dict:
            for product in current_app.products:
                if item == product.id:
                    for product_id in current_app.warehouse.product_storage:
                        if item == product_id:
                            current_app.warehouse.product_storage[item] -= selling_dict[item]
                    total_funds_gained += int(product.sale_price * selling_dict[item])
        current_app.funds += total_funds_gained
        
        #return redirect(url_for("sales.main"))
        return ("true", 200)

    except Exception as e:
        return (e, 500)

@sales.route("/replot", methods=["POST", "GET"])
def replot():
    try:
        selected_product_id = request.get_json()["data"]

        selected_product = [product.id for product in current_app.products if product.id == selected_product_id][0]
        sale_prices = [product["sale_price"] for day in current_app.product_sale_price_past_list for product in day if product["id"] == selected_product]
        dates = [product["date"] for day in current_app.product_sale_price_past_list for product in day if product["id"] == selected_product]

        y = sale_prices
        x = dates
        aspect_ratio = (8, 5)

        fig, ax = plt.subplots(figsize=aspect_ratio)
        ax.plot(x, y, 'o-',  color='black', linewidth=2)
        ax.plot(x, y, 'o', color='red')
        plt.grid(True)
        plt.tight_layout()
        fig.autofmt_xdate()

        basedir = os.path.abspath(os.path.dirname(__file__))
        fullpath =  os.path.join(basedir, "static", "plot.png")
        plt.savefig( os.path.join(basedir, "static", "plot.png"))
        plt.close(fig)

        return (jsonify(fullpath), 200)
    except Exception as e:
        return (e, 500)

