from flask import Blueprint, render_template,current_app, request, session, redirect, url_for, jsonify,flash

logistics = Blueprint("logistics", __name__, static_folder="static", template_folder="templates")

@logistics.route("/")
def main():
    current_app.current_page = "logistics"

    date = current_app.current_date
    day = current_app.days_of_the_week[current_app.current_date.weekday()]
    funds = current_app.funds
    warehouse = current_app.warehouse
    workorders = current_app.workorders
    raw_materials = current_app.raw_materials

    current_shelf_code = session.get("shelf_code", "A")
    current_shelf = [shelf for shelf in warehouse.shelves if shelf.code == current_shelf_code][0]

    shelf_capacities = {}
    for shelf in warehouse.shelves:
        shelf_capacities[shelf.code] = 0
        for address in shelf.addresses:
            if shelf.addresses[address] != "":
                shelf_capacities[shelf.code] += 1

    return render_template("logistics.html", date=date, day=day, funds=funds, 
                           shelf_capacities=shelf_capacities, warehouse=warehouse, 
                           current_shelf=current_shelf, workorders=workorders,
                           raw_materials=raw_materials)

@logistics.route("/select_shelf", methods=["POST"])
def select_shelf():
    shelf_code = request.form.get("shelf_code")
    if shelf_code:
        session["shelf_code"] = shelf_code

    return redirect(url_for("logistics.main"))

@logistics.route("/buy_shelf", methods=["POST"])
def buy_shelf():

    SHELF_PRICE = 10000
    current_app.warehouse.add_shelf()
    current_app.funds -= SHELF_PRICE
    return redirect(url_for("logistics.main"))

@logistics.route("/get_product", methods=["POST"])
def get_product():
    workorder_id = request.get_json("data")
    if workorder_id:
        workorder = [workorder for workorder in current_app.workorders if workorder_id == workorder.id][0]
        workorder_product_ids = [product for product in workorder.loaded_products if workorder.loaded_products[product] != 0]
    else:
        workorder_product_ids = None
    return jsonify(workorder_product_ids)

@logistics.route("/calculate_raw_material_need", methods=["POST"])
def calculate_raw_material_need():
    product_id, workorder_id = request.get_json("data")

    if product_id and workorder_id:
        selected_product = [product for product in current_app.products if product_id == product.id][0]
        selected_workorder = [workorder for workorder in current_app.workorders if workorder_id == workorder.id][0]

        result_list = []
        material_need_all = selected_product.calculate_raw_material_need(selected_workorder)
        for material in current_app.raw_materials:
            material_need = material_need_all[material.code]
            result_list.append([material.code, material.name, current_app.warehouse.raw_material_stocks[material.code],
                        material_need, selected_workorder.loaded_products_transfer_status[selected_product.id]])

        return jsonify(result_list)
    else:
        raise(ValueError("product_id and workorder_id was not received!"))
        
@logistics.route("/transfer_materials", methods=["POST"])
def transfer_materials():

    workorder_id = request.form.get("logistics_workorder_select")
    product_id = request.form.get("logistics_product_select")

    workorder_ids = [workorder.id for workorder in current_app.workorders]
    product_ids = [product.id for product in current_app.products]

    if product_id in product_ids and workorder_id in workorder_ids :
        selected_product = [product for product in current_app.products if product_id == product.id][0]
        selected_workorder = [workorder for workorder in current_app.workorders if workorder_id == workorder.id][0]

        flag = True
        material_need_all = selected_product.calculate_raw_material_need(selected_workorder)
        for material in current_app.raw_materials:
            material_need = material_need_all[material.code]
            material_stock = current_app.warehouse.raw_material_stocks[material.code]
            if material_need > material_stock:
                flag = False
                break
        if flag == True:
            for material in current_app.raw_materials:
                material_need = material_need_all[material.code]
                material_stock = current_app.warehouse.raw_material_stocks[material.code]
                current_app.warehouse.raw_material_stocks[material.code] = current_app.warehouse.raw_material_stocks[material.code] - material_need
            for part in selected_product.product_parts:
                for shelf in current_app.warehouse.shelves:
                    for address in shelf.addresses:
                        if shelf.addresses[address] == part.id:
                            if part.raw_material.code != "E1":
                                shelf.unfinished_part_stocks[address] += (selected_workorder.loaded_products[selected_product.id] * selected_product.part_amounts[part.id])
                            else:
                                shelf.finished_part_stocks[address] += (selected_workorder.loaded_products[selected_product.id] * selected_product.part_amounts[part.id])
        return redirect(url_for("logistics.main"))
    flash("Please select workorder and product!")
    return redirect(url_for("logistics.main"))
