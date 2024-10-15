from flask import render_template, url_for, current_app, Blueprint, redirect, request
from utils import generate_sale_modifier, generate_customer_order_data, generate_procurement_modifier
from datetime import timedelta
import json
from app import db, app
from models import HighScore


core = Blueprint("core",__name__, template_folder="templates", static_folder='static')

@core.route("/")
def index():
    date = current_app.current_date
    day = current_app.days_of_the_week[current_app.current_date.weekday()]
    funds = current_app.funds

    """     app_full_cache = { "products": current_app.products,
                        "workcenters": current_app.workcenters,
                        "workorders": current_app.workorders,
                        "operations": current_app.operations,
                        "selling_dict": current_app.selling_dict,
                        "planning_dict": current_app.planning_dict,
                        "customer_order_list": current_app.customer_order_list, 
                        "warehouse": current_app.warehouse,
                        "part_name_data": current_app.part_name_data,
                        "raw_materials": current_app.raw_materials,
                        "production_methods": current_app.production_methods,
                        "production_methods": current_app.sales_modifiers_list,
                        "procurement_modifiers_list": current_app.procurement_modifiers_list,
                        "current_date": current_app.current_date,
                        "product_sale_price_past_list": current_app.product_sale_price_past_list,
                        "raw_material_cost_past_list": current_app.raw_material_cost_past_list,
                        "funds": current_app.funds,
                        "days_of_the_week": current_app.days_of_the_week,
                        "raw_materials_dict": current_app.raw_materials_dict,
                        "raw_material_mapping": current_app.raw_material_mapping,
                        "active_workcenter_text": current_app.active_workcenter_text,
                    } """
    player_data = []
    with app.app_context():
        players = HighScore.query.all()
        for player in players:
            player_data.append({"player_name":player.player_name, "score":player.score})
        

    return render_template("index.html", date=date, funds=funds, day=day, selling_dict=current_app.selling_dict, players=player_data)

@core.route("/end_day", methods=["POST"])
def end_day():
    current_page = current_app.current_page
    selling_dict = current_app.selling_dict
    products = current_app.products
    warehouse = current_app.warehouse
    workcenters = current_app.workcenters
    raw_materials = current_app.raw_materials
    workorders = current_app.workorders

    #calculates the total funds gained by selling the products in the selling dict
    total_funds_gained = 0
    for item in selling_dict:
        for product in products:
            if item == product.id:
                for product_id in warehouse.product_storage:
                    if item == product_id:
                        warehouse.product_storage[item] -= selling_dict[item]
                total_funds_gained += product.sale_price * selling_dict[item]

    new_generated_list = generate_sale_modifier(products=products, workcenters=workcenters)
    current_app.sales_modifiers_list.clear()
    for item in new_generated_list:
        current_app.sales_modifiers_list.append(item)

    new_customer_order_list = generate_customer_order_data(products=products, workcenters=workcenters) 
    current_app.customer_order_list.clear()
    for item in new_customer_order_list:
        current_app.customer_order_list.append(item)

    #adds the calculated gained funds to he existing funds
    current_app.funds += total_funds_gained

    #updates the date
    current_app.current_date += timedelta(days=1)

    #updates the product prices
    current_day_product_sale_price_list = [{'id': product.id, 'sale_price': product.sale_price, 'date': current_app.current_date} for product in current_app.products]
    current_app.product_sale_price_past_list.append(current_day_product_sale_price_list)
    current_app.product_sale_price_past_list.pop(0)

    new_procurement_modifiers_list = generate_procurement_modifier(raw_materials=raw_materials)
    current_app.procurement_modifiers_list.clear()
    for item in new_procurement_modifiers_list:
        current_app.procurement_modifiers_list.append(item)

    #updates the raw material prices
    current_day_raw_material_cost_list = [{'code': raw_material.code, 'cost': raw_material.cost, 'date': current_app.current_date} for raw_material in current_app.raw_materials]
    current_app.raw_material_cost_past_list.append(current_day_raw_material_cost_list)
    current_app.raw_material_cost_past_list.pop(0)

    for workcenter in workcenters:
        if workcenter.active == True:
            workcenter.run_all_stations()
    
    for workorder in workorders:
        for product_text in workorder.loaded_products:
            product = [product for product in products if product.id == product_text][0]
            workorder_status = workorder.are_all_parts_assembled(product_text)
            if workorder_status == True:
                if workorder.finished[product.id] == False:
                    warehouse.product_storage[product_text] += workorder.loaded_products[product_text]
                    workorder.finished[product.id] = True

                workorder.all_parts_manufactured[product.id] = False

    for workorder in workorders:
        flag = True
        for item in workorder.finished:
            if workorder.finished[item] == False:
                flag = False
        if flag == True:
            for wo_operation in workorder.wo_operations:
                for workcenter in workcenters:
                    for wc_operation in workcenter.operations[:]:
                        if wc_operation.id == wo_operation.id:
                            workcenter.operations.remove(wc_operation)
            for wo_assembly_operations in workorder.wo_assembly_operations:
                for workcenter in workcenters:
                    for wc_operation in workcenter.operations[:]:
                        if wc_operation.id == wo_assembly_operations.id:
                            workcenter.operations.remove(wc_operation)
                

    if current_page != "":
        return redirect(url_for(f"{current_page}.main"))
    else:
        return redirect(url_for(f"core.index"))



@core.route("/highscore", methods=["GET", "POST"])
def highscore():
    score = int(request.form.get("score"))
    name = request.form.get("name")

    new_score = HighScore(player_name = name, score = score)
    db.session.add(new_score)
    db.session.commit()
    return redirect(url_for("core.index"))


    




