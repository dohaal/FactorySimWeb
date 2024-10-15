import os
import random
import math
from datetime import timedelta
import csv

from modules import Product, WorkCenter, RawMaterial

def generate_sale_modifier(products, workcenters):
    product_types = products[0].product_types
    sales_modifiers_list = []

    modifier_texts = ["Great increase", "Major increase", "Minor increase", "Minor decrease", "Major decrease", "Great decrease"]
    modifiers = [1.5, 1.3, 1.15, 0.85, 0.7, 0.5]
    modifier_weight = [1, 2, 3, 3, 2, 1]
    for i in range(len(product_types)):
        modifier_dict = {}
        modifier = random.choices(modifiers, weights=modifier_weight, k=1)[0]
        product_type = product_types[i]
        for j in range(len(modifiers)):
            if modifier == modifiers[j]:
                modifier_text = modifier_texts[j]

        modifier_dict["type"] = product_type
        modifier_dict["value"] = modifier
        modifier_dict["text"] = modifier_text
        sales_modifiers_list.append(modifier_dict)
    
    for product in products:
        base_cost = product.calculate_base_cost(workcenters)
        for modifier in sales_modifiers_list:
            if product.product_type == modifier["type"]:
                if modifier["value"] == 1.5:
                    product.permanent_modifier += 0.1
                elif modifier["value"] == 0.5:
                    product.permanent_modifier -= 0.1
                product.production_cost = base_cost
                product.sale_price = int(base_cost * modifier["value"] * product.permanent_modifier)
                product.exchange = int(product.sale_price - product.production_cost)
                
    return sales_modifiers_list

def generate_procurement_modifier(raw_materials):
    raw_material_names = [raw_material.name for raw_material in raw_materials]
    procurement_modifiers_list = []

    modifier_texts = ["Great increase", "Major increase", "Minor increase", "Minor decrease", "Major decrease", "Great decrease"]
    modifiers = [0.2, 0.15, 0.1, -0.1, -0.15, -0.2]
    modifier_weight = [1, 2, 3, 3, 2, 1]
    for i in range(len(raw_material_names)):
        modifier_dict = {}
        modifier = random.choices(modifiers, weights=modifier_weight, k=1)[0]
        raw_material_name = raw_material_names[i]
        for j in range(len(modifiers)):
            if modifier == modifiers[j]:
                modifier_text = modifier_texts[j]

        modifier_dict["type"] = raw_material_name
        modifier_dict["value"] = modifier
        modifier_dict["text"] = modifier_text
        procurement_modifiers_list.append(modifier_dict)
    
    for raw_material in raw_materials:
        base_cost = raw_material.cost
        for modifier in procurement_modifiers_list:
            if raw_material.name == modifier["type"]:
                if modifier["value"] == 0.2:
                    raw_material.permanent_modifier += 0.05
                elif modifier["value"] == -0.2:
                    raw_material.permanent_modifier -= 0.05
                raw_material.cost = round(base_cost + (base_cost * modifier["value"]) * raw_material.permanent_modifier, 0)
    return procurement_modifiers_list

def generate_customer_order_data(products, workcenters, modifier = 1):
    """ Generates customer order data. The player may or may not choose to fullfill these orders. Creates
    a multiplier consisting the total amount of turns needed to manufacture the product and the amount of
    workcenter operators who will do the work. The idea is to get higher number of orders for products
    that consists fewer amounts of parts and fewer amounts of orders for products that consist many parts.
    The number of orders also increase as the capacity of the factory increases.
    """
    BALANCING_MULTIPLIER = 100
    STD_DEV_BALANCER = 3

    product_types = [product.product_type for product in products]
    product_ids = [product.id for product in products]
    product_operation_turncounts = [product.total_operation_turncount for product in products]

    total_workcenter_capacity = sum(workcenter.operator_count for workcenter in workcenters if workcenter.station_count != 10)
    
    product_quantity_multiplier = [total_workcenter_capacity/prod_opr_turncount for prod_opr_turncount in product_operation_turncounts]
    product_quantity_multiplier_balanced_modified = [multiplier * BALANCING_MULTIPLIER * modifier for multiplier in product_quantity_multiplier]
    product_quantity_multiplier_randomized = [random.normalvariate(multiplier, multiplier/STD_DEV_BALANCER) for multiplier in product_quantity_multiplier_balanced_modified] 

    product_quantity = [[product_ids[i], product_types[i], math.floor(product_quantity_multiplier_randomized[i])] for i in range(len(product_ids))]
    return product_quantity

def initial_product_price_history_generation(products, workcenters, current_date):
    TIME_RANGE = 29
    date = current_date - timedelta(days=TIME_RANGE)
    product_price_data_total = []
    for i in range(TIME_RANGE):
        product_price_data_perday = []
        generate_sale_modifier(products=products, workcenters=workcenters)
        for product in products:
            plot_info = {}
            plot_info["id"] = product.id 
            plot_info["sale_price"] = product.sale_price
            plot_info["date"] = date
            product_price_data_perday.append(plot_info)
        date += timedelta(days=1)
        product_price_data_total.append(product_price_data_perday)
    return product_price_data_total

def initial_raw_material_cost_history_generation(current_date, raw_materials):
    TIME_RANGE = 29
    date = current_date - timedelta(days=TIME_RANGE)
    raw_material_cost_data_total = []
    for i in range(TIME_RANGE):
        raw_material_cost_data_perday = []
        generate_procurement_modifier(raw_materials=raw_materials)
        for raw_material in raw_materials:
            plot_info = {}
            plot_info["code"] = raw_material.code
            plot_info["cost"] = raw_material.cost
            plot_info["date"] = date
            raw_material_cost_data_perday.append(plot_info)
        date += timedelta(days=1)
        raw_material_cost_data_total.append(raw_material_cost_data_perday)
    return raw_material_cost_data_total
        
def initial_machine_data_generation(lg, md, sm, warehouse, products, workorders, raw_materials, 
                                    production_methods, part_name_data, workcenters, selling_dict, 
                                    planning_dict, raw_materials_dict, raw_material_mapping):
    """ generates machine info if it does not already exist """

    endproduct_lg = []
    endproduct_md = []
    endproduct_sm = []
    for i in range(lg):
        production_type_leaning = random.choices(production_methods, k=1)[0]
        raw_material_codes = [raw_material.code for raw_material in raw_materials for prod_type in raw_material.prod_types if prod_type == production_type_leaning] 

        raw_material_code_indexes = []
        for code in raw_material_codes:
            for index, item in enumerate(raw_materials_dict):
                if code == item:
                    raw_material_code_indexes.append(index)

        leaning_weights = [1,1,1,1,1,1,1,1,1,1]
        for item in raw_material_code_indexes:
            leaning_weights[item] = 3
        
        endproduct_lg.append(Product('LG', warehouse=warehouse, products=products, workorders=workorders, 
                                raw_materials=raw_materials, production_methods=production_methods,
                                part_name_data=part_name_data, workcenters=workcenters, selling_dict=selling_dict,
                                planning_dict=planning_dict, leaning_weights=leaning_weights, 
                                production_type_leaning=production_type_leaning))
    for i in range(md):
        production_type_leaning = random.choices(production_methods, k=1)[0]
        raw_material_codes = [raw_material.code for raw_material in raw_materials for prod_type in raw_material.prod_types if prod_type == production_type_leaning] 

        raw_material_code_indexes = []
        for code in raw_material_codes:
            for index, item in enumerate(raw_materials_dict):
                if code == item:
                    raw_material_code_indexes.append(index)

        leaning_weights = [1,1,1,1,1,1,1,1,1,1]
        for item in raw_material_code_indexes:
            leaning_weights[item] = 10
        endproduct_md.append(Product('MD', warehouse=warehouse, products=products, workorders=workorders,
                                raw_materials=raw_materials, production_methods=production_methods,
                                part_name_data=part_name_data, workcenters=workcenters, selling_dict=selling_dict,
                                planning_dict=planning_dict, leaning_weights=leaning_weights,
                                production_type_leaning=production_type_leaning)) 
    for i in range(sm):
        production_type_leaning = random.choices(production_methods, k=1)[0]
        raw_material_codes = [raw_material.code for raw_material in raw_materials for prod_type in raw_material.prod_types if prod_type == production_type_leaning] 

        raw_material_code_indexes = []
        for code in raw_material_codes:
            for index, item in enumerate(raw_materials_dict):
                if code == item:
                    raw_material_code_indexes.append(index)

        leaning_weights = [1,1,1,1,1,1,1,1,1,1]
        for item in raw_material_code_indexes:
            leaning_weights[item] = 10
        endproduct_sm.append(Product('SM', warehouse=warehouse, products=products, workorders=workorders,
                                raw_materials=raw_materials, production_methods=production_methods, 
                                part_name_data=part_name_data, workcenters=workcenters, selling_dict=selling_dict,
                                planning_dict=planning_dict, leaning_weights=leaning_weights,
                                production_type_leaning=production_type_leaning))

    end_products_all = endproduct_lg + endproduct_md + endproduct_sm
    return end_products_all 

def initial_workcenter_data_generation(warehouse, workcenters, production_methods, products, workorders):
    """ generates workcenter info if it does not already exist """
    for item in production_methods:
        workcenters.append(WorkCenter(prod_method=item, warehouse=warehouse, workcenters=workcenters,
                                        workorders=workorders, products=products))
    return workcenters

def initial_raw_material_generation(app):
    """ generates raw material objects for each item in raw_materials dict """
    app.raw_materials_dict = {'S1': 'Steel Ingot', 'S2': 'Steel Sheet','S3': 'Steel Plate','S4': 'Steel Bar',
                      'A1': 'Aluminum Ingot', 'A2': 'Aluminum Sheet', 'A3': 'Aluminum Plate', 'A4': 'Aluminum Bar',
                      'P1': 'Plastic Pellets', 'E1': 'Electronics'}
    app.raw_material_mapping = {'Machining': ['S3', 'A3'], 'Bending': ['S2', 'A2'], 'Casting': ['S1', 'A1', 'P1'], 'Forging': ['S4', 'A4'], 
                            'Paintjob': ['A2', 'A3', 'A4', 'S2', 'S3'], 'Welding': ['S2', 'S3', 'S4']}
    
    raw_materials = []
    for raw_material_code in app.raw_materials_dict:
        raw_material_production_methods = [production_type for production_type in app.raw_material_mapping for code in app.raw_material_mapping[production_type] if code == raw_material_code]
        raw_material_name = app.raw_materials_dict[raw_material_code]
        raw_materials.append(RawMaterial(raw_material_code, raw_material_name, raw_material_production_methods, app.warehouse))
    return raw_materials

def part_names_csv_reader():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, 'part_names.csv')
    with open(file_path, mode='r') as file:
        csv_dict_reader = csv.DictReader(file)
        data = [row for row in csv_dict_reader]
    return data