from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import date

import os
import secrets

from utils import part_names_csv_reader, initial_raw_material_generation, initial_workcenter_data_generation
from utils import initial_machine_data_generation, generate_customer_order_data, initial_product_price_history_generation
from utils import initial_raw_material_cost_history_generation, generate_sale_modifier
from utils import generate_procurement_modifier
from modules import Warehouse, Assembly

from sqlalchemy import create_engine

db = SQLAlchemy()

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "data.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = secrets.token_hex(16)

db.init_app(app)

from core import core
from logistics import logistics
from procurement import procurement
from production import production
from sales import sales
from planning import planning
app.register_blueprint(core)
app.register_blueprint(logistics, url_prefix='/logistics')
app.register_blueprint(procurement, url_prefix='/procurement')
app.register_blueprint(production, url_prefix='/production')
app.register_blueprint(sales, url_prefix='/sales')
app.register_blueprint(planning, url_prefix='/planning')

app.products = []
app.workcenters = []
app.workorders = []
app.operations = [] #so that we can check if the created ids are unique
app.selling_dict = {}
app.planning_dict = {}
app.customer_order_list = []
app.warehouse = None
app.raw_materials = None
app.procurement_modifiers_list = []
app.sales_modifiers_list = []
app.funds = 50000
app.current_date = date(year=2024, month=1, day=1)
app.product_sale_price_past_list = []
app.raw_material_cost_past_list = []

app.part_name_data = None
app.production_methods = None





app.days_of_the_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
app.raw_materials_dict = {}
app.raw_material_mapping = {}
app.active_workcenter_text = ""

app.current_page = ""

app.part_name_data = part_names_csv_reader()
app.production_methods = ['Machining', 'Bending', 'Casting', 'Forging', 'Paintjob', 'Welding']
app.warehouse = Warehouse()
app.raw_materials = initial_raw_material_generation(app)
app.workcenters = initial_workcenter_data_generation(warehouse=app.warehouse, workcenters=app.workcenters, production_methods=app.production_methods,
                                                        workorders=app.workorders, products=app.products)
app.products = initial_machine_data_generation(lg=3, md=3, sm=3,warehouse=app.warehouse, products=app.products, workorders=app.workorders, 
                                        production_methods=app.production_methods, raw_materials=app.raw_materials,
                                        part_name_data=app.part_name_data, workcenters=app.workcenters, selling_dict=app.selling_dict,
                                        planning_dict=app.planning_dict, raw_material_mapping=app.raw_material_mapping,
                                        raw_materials_dict=app.raw_materials_dict)
app.workcenters.append(Assembly(warehouse=app.warehouse, workcenters=app.workcenters, workorders=app.workorders,
                                    products=app.products))
app.customer_order_list = generate_customer_order_data(app.products, app.workcenters)

app.product_sale_price_past_list = initial_product_price_history_generation(products=app.products, workcenters=app.workcenters, current_date=app.current_date)
app.raw_material_cost_past_list = initial_raw_material_cost_history_generation(raw_materials=app.raw_materials, current_date=app.current_date)

app.sales_modifiers_list = generate_sale_modifier(products=app.products, workcenters=app.workcenters)
app.procurement_modifiers_list = generate_procurement_modifier(raw_materials=app.raw_materials)




for product in app.products:
    app.planning_dict[product.id] = 0

import models

if __name__ == "__main__":
    app.run(debug=True)

