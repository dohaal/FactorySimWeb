from flask import Blueprint, render_template, current_app, redirect, url_for, request, session, jsonify, flash
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')


import os

procurement = Blueprint("procurement", __name__, static_folder="static", template_folder="templates")

@procurement.route("/")
def main():
    current_app.current_page = "procurement"

    date = current_app.current_date
    day = current_app.days_of_the_week[current_app.current_date.weekday()]
    funds = current_app.funds
    raw_materials = current_app.raw_materials
    procurement_modifiers_list = current_app.procurement_modifiers_list
    raw_material_cost_past_list = current_app.raw_material_cost_past_list
    workorders = current_app.workorders
    warehouse = current_app.warehouse

    current_material = session.get("current_material",  raw_materials[0].code)
    raw_material_costs = [raw_material["cost"] for day in raw_material_cost_past_list for raw_material in day if raw_material["code"] == current_material]
    dates = [raw_material["date"].strftime("%Y-%m-%d %H:%M:%S") for day in raw_material_cost_past_list for raw_material in day if raw_material["code"] == current_material]

    y = raw_material_costs
    x = dates

    aspect_ratio = (10, 5)

    fig, ax = plt.subplots(figsize=aspect_ratio)
    ax.plot(x, y, 'o-',  color='black', linewidth=2)
    ax.plot(x, y, 'o', color='red')

    step = 4
    ax.set_xticks(x[::step])
    ax.set_xticklabels(x[::step], rotation=45)

    plt.grid(True)
    plt.tight_layout()
    fig.autofmt_xdate()

    basedir = os.path.abspath(os.path.dirname(__file__))
    plt.savefig( os.path.join(basedir, "static", "plot.png"))
    plt.close(fig)

    procurement_switch = session.get("procurement_switch", "market_expectations")

    return render_template("procurement.html", date=date, day=day, funds=funds, raw_materials=raw_materials,
                           procurement_modifiers_list=procurement_modifiers_list, workorders=workorders,
                           procurement_switch=procurement_switch, warehouse=warehouse)

@procurement.route("/switch", methods=["POST"])
def switch():
    procurement_switch = request.form.get("procurement_switch")
    if procurement_switch:
        if procurement_switch == "market_expectations":
            session["procurement_switch"] = "market_expectations"
        elif procurement_switch == "current_stocks":
            session["procurement_switch"] = "current_stocks"
        return redirect(url_for("procurement.main"))

@procurement.route("/select_material", methods=["POST"])
def select_material():
    object_id = request.get_json("data")

    if object_id:
        if len(object_id.split("_")) == 3:
            material_code = object_id.split("_")[1]
        elif len(object_id.split("_")) == 4:
            material_code_list = object_id.split("_")[1:2]
            material_code= "_".join(material_code_list)
        material = [material for material in current_app.raw_materials if material.code == material_code][0]
        session["current_material"] = material.code
        return jsonify("ok", 200)
    else:
        raise ValueError("selected raw material did not arrive to /select_material!")
    

    #material.name
@procurement.route("/buy", methods=["POST"])
def buy():

    for key, value in request.form.items():
            if key.startswith('select_material_'):
                material_code = value
                #material_code = key.split('_')[-1]
                quantity_key = f'procurement_quantity_{material_code}'
                if quantity_key in request.form:
                    quantity = request.form[quantity_key]


    #quantity = request.form.get("procurement_quantity_data")
    #raw_material_id = request.form.get("select_material_data")
    if quantity == "":
        quantity = 0
    else:
        quantity = int(quantity)

    raw_material = [material for material in current_app.raw_materials if material.code == material_code][0]
    if raw_material.minimum_order_quantity <= int(quantity):
        total_price = quantity * int(raw_material.cost)
        if total_price < current_app.funds:
            current_app.funds = current_app.funds - total_price
            current_app.warehouse.raw_material_stocks[raw_material.code] += quantity
    else:
        flash("Please enter a quantity that is bigger than the minimum order!")
    return redirect(url_for("procurement.main"))