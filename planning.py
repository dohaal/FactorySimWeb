from flask import Blueprint, render_template, current_app, session, redirect, request, url_for, jsonify, flash

from modules import WorkOrder

planning = Blueprint("planning", __name__, static_folder="static", template_folder="templates")

@planning.route("/")
def main():
    current_app.current_page = "planning"

    date = current_app.current_date
    day = current_app.days_of_the_week[current_app.current_date.weekday()]
    funds = current_app.funds
    products = current_app.products
    planning_dict = current_app.planning_dict
    selling_dict = current_app.selling_dict
    workcenters = current_app.workcenters
    workorders = current_app.workorders

    bom_flag = session.get("bom_flag", True)
    product_id = session.get("product_id", products[0].id)
    product = [product for product in products if product.id == product_id][0]

    product_opr_times = []
    for product in products:
        machining_total = sum(part.operation_times[index] * product.part_amounts[part.id] for part in product.product_parts for index, opr in enumerate(part.operations) if opr == "Machining")
        bending_total = sum(part.operation_times[index] * product.part_amounts[part.id] for part in product.product_parts for index, opr in enumerate(part.operations) if opr == "Bending")
        casting_total = sum(part.operation_times[index] * product.part_amounts[part.id] for part in product.product_parts for index, opr in enumerate(part.operations) if opr == "Casting")
        forging_total = sum(part.operation_times[index] * product.part_amounts[part.id] for part in product.product_parts for index, opr in enumerate(part.operations) if opr == "Forging")
        paintjob_total = sum(part.operation_times[index] * product.part_amounts[part.id] for part in product.product_parts for index, opr in enumerate(part.operations) if opr == "Paintjob")
        welding_total = sum(part.operation_times[index] * product.part_amounts[part.id] for part in product.product_parts for index, opr in enumerate(part.operations) if opr == "Welding")   
        product_opr_times.append([product.id, product.product_type, machining_total, bending_total, casting_total,
                                 forging_total, paintjob_total, welding_total])
        
    workcenter_workload_list = []
    for workcenter in workcenters:
        if workcenter.prod_method != "Assembly":
            workcenter_type = workcenter.prod_method
            workcenter_workload = sum(operation.remaining_work for operation in workcenter.operations)
            workcenter_stations = workcenter.station_count
            workcenter_workload_list.append([workcenter_type, workcenter_workload, workcenter_stations])

    return render_template("planning.html", date=date, day=day, funds=funds, products=products,
                           planning_dict=planning_dict, selling_dict=selling_dict, bom_flag=bom_flag,
                           product=product, product_opr_times=product_opr_times,
                            workcenter_workload_list=workcenter_workload_list, workorders=workorders)

@planning.route("/switch", methods=["POST", "GET"])
def switch():
    product_id = request.args.get("product_id")
    if product_id:
        session["product_id"] = product_id
    if request.form["planning_switch"] == "bom":
        session["bom_flag"] = True
    else:
        session["bom_flag"] = False
    return redirect(url_for("planning.main"))

@planning.route("/create_workorder", methods=["POST", "GET"])
def create_workorder():
    data = request.get_json("data")["data"]
    if data:
        current_app.planning_dict = data

    planning_dict_non_zero_quantities = {item: current_app.planning_dict[item] for item in current_app.planning_dict if current_app.planning_dict[item] != 0}
    if len(planning_dict_non_zero_quantities) :
        new_workorder = WorkOrder(loaded_products=current_app.planning_dict,workorders=current_app.workorders,current_date=current_app.current_date,
                                    operations=current_app.operations,products=current_app.products,workcenters=current_app.workcenters,
                                    warehouse=current_app.warehouse)
        current_app.workorders.append(new_workorder)

        for item in current_app.planning_dict:
            current_app.planning_dict[item] = 0

        return (jsonify(new_workorder.id),200)

    flash("Please add products to the list!")
    return ("error",200)

@planning.route("/product_change", methods=["POST", "GET"])
def product_change():
    product_id = request.get_json()["data"]

    if product_id:
        product = [product for product in current_app.products if product_id == product.id][0]
    else:
        product = None
    
    return_dict_general_info = {
        "Product ID": product.id,
        "Product Type": product.product_type,
        "Distinct Part Count": product.part_count,
        "Production Cost": product.production_cost,
        "Production Time": product.total_manufacturing_time,
        "Main Work Type": product.production_type_leaning,
        "Assembly Time": product.total_assembly_time,
    }

    return_list_bom = []
    for index,part in enumerate(product.product_parts):
         return_dict_bom = {}
         return_dict_bom["No"] = index + 1
         return_dict_bom["Part ID"] = part.id
         return_dict_bom["Part Name"] = part.name
         return_dict_bom["Amount"] = product.part_amounts[part.id]
         return_dict_bom["Assembly Time"] = part.assembly_time
         return_dict_bom["Raw Material"] = part.raw_material_name
         return_dict_bom["RM Cost"] = part.raw_material.cost
         return_dict_bom["Operations"] = part.operations
         return_dict_bom["Operation Times"] = part.operation_times
         return_list_bom.append(return_dict_bom)
    
    return (jsonify([return_list_bom, return_dict_general_info]))

@planning.route("/delete_workorder", methods=["POST", "GET"])
def delete_workorder():

    select_workorder_id = request.form.get("select_delete_workorder")

    if select_workorder_id != "Select Workorder" or not select_workorder_id:
    #planning_workorder_select = self.query("#planning_workorder_select").first()
        current_workorder = [workorder for workorder in current_app.workorders if select_workorder_id == workorder.id][0]
        for workcenter in current_app.workcenters:
            flag = True
            while flag:
                flag = False
                for index, operation in enumerate(workcenter.operations):
                    if operation.workorder_id == current_workorder.id:
                        workcenter.operations.pop(index)
                        flag = True

        for index, workorder in enumerate(current_app.workorders):
            if workorder.id == select_workorder_id:
                current_app.workorders.pop(index)
    else:
        flash("Please select a workorder!")

    return redirect(url_for("planning.main"))
