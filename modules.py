import random
import string
import math

def allocate_workcenter(operation, workcenters):
    for workcenter in workcenters:
        if workcenter.prod_method == operation.task:
            workcenter.operations.append(operation)

class WorkOrder:
    def __init__(self, loaded_products, workorders, current_date, operations, products, workcenters, warehouse):
        self.id = f"WO-{current_date.day}/{current_date.month}/{current_date.year}-{len(workorders) + 1}"
        self.loaded_products = {key: loaded_products[key] for key in loaded_products}
        self.loaded_products_transfer_status = {key: False for key in loaded_products}
        self.date = current_date
        self.wo_operations = []
        self.wo_assembly_operations = []
        self.existing_operations = operations
        self.all_parts_manufactured = {key: False for key in loaded_products}
        self.products = products
        self.warehouse = warehouse
        self.finished = {key: False for key in loaded_products}

        for product_id in self.loaded_products:
            current_product = [product for product in products if product.id == product_id][0]
            product_amount = self.loaded_products[product_id]
            if product_amount != 0:
                for part in current_product.product_parts:
                    part_amount=current_product.part_amounts[part.id]
                    for index, operation in enumerate(part.operations):
                        remaining_work = part.operation_times[index] * part_amount * product_amount

                        new_operation = Operation(workorder_id=self.id,task=operation,operations=self.existing_operations,
                                                            loaded_part=part,product=current_product,remaining_work=remaining_work,
                                                            product_amount=product_amount,part_amount=part_amount)
                        self.wo_operations.append(new_operation)
                        self.existing_operations.append(new_operation)
                        
                        allocate_workcenter(workcenters=workcenters, operation=new_operation)

                    remaining_assembly = part.assembly_time * part_amount * product_amount
                    new_assembly_operation = Operation(workorder_id=self.id,task="Assembly",operations=self.existing_operations,
                                                            loaded_part=part,product=current_product,remaining_work=remaining_assembly,
                                                            product_amount=product_amount,part_amount=part_amount)
                    self.wo_assembly_operations.append(new_assembly_operation)
                    self.existing_operations.append(new_assembly_operation)
                    allocate_workcenter(workcenters=workcenters, operation=new_assembly_operation)

    def are_all_parts_assembled(self, product_text):
        flag = True
      
        for operation in self.wo_assembly_operations:
            if operation.product_id == product_text:
                if operation.remaining_work > 0:
                    flag = False
                    break
        return flag

class Operation:
    def __init__(self, workorder_id, task, product, operations, loaded_part, remaining_work, product_amount, part_amount):
        while True:
            digits = "".join(random.choices(string.digits, k=6))
            generated_opr_number = f"OPR-{digits}-{len(operations) + 1}"
            existing_opr_numbers = [operation.id for operation in operations]
            if generated_opr_number not in existing_opr_numbers:
                self.id = generated_opr_number
                break

        self.product_id = product.id
        self.loaded_part = loaded_part
        self.raw_material = self.loaded_part.raw_material_name
        self.workorder_id = workorder_id
        self.task = task
        self.part_amount = part_amount
        self.product_amount = product_amount
        self.remaining_work = remaining_work
        self.workcenter = None

    #def serialize(self):
    #    return {}
     
class WorkCenter:
    def __init__(self, prod_method, warehouse, workcenters, workorders, products):
        DEFAULT_FAIL_RATE = 0.02
        DEFAULT_FAULTY_PART_RATE = 0.05
        DEFAULT_OPERATING_COST = 50
        DEFAULT_STATION_COUNT = 2
        DEFAULT_OPERATOR_COUNT = 2
        self.warehouse = warehouse
        self.workorders = workorders
        self.products = products

        while True:
            digits = ''.join(random.choices(string.digits, k=6))
            generated_id = prod_method[:3].upper() + digits

            self.id = ''
            existing_ids = [workcenter.id for workcenter in workcenters]
            if generated_id not in existing_ids:
                self.id = generated_id
                break

        self.operating_cost = DEFAULT_OPERATING_COST
        self.prod_method = prod_method
        self.fail_rate = DEFAULT_FAIL_RATE
        self.faulty_part_rate = DEFAULT_FAULTY_PART_RATE
        self.progress = 0
        self.active = False
        self.faulty = False
        if self.prod_method == "Paintjob":
            self.station_count = DEFAULT_STATION_COUNT + 1
        else:
            self.station_count = DEFAULT_STATION_COUNT
        self.operator_count = DEFAULT_OPERATOR_COUNT
        self.operations = []

    def __str__(self):
        return ("Workcenter ID: " + str(self.id) + "\n" +
                "Production Method: " + self.prod_method + "\n" +
                "Fail Rate: " + str(self.fail_rate) + "%\n" +
                "Active: " + str(self.active) + "\n" +
                "Station Count: " + str(self.station_count) + "\n" +
                "Operator Count: " + str(self.operator_count) + "\n" +
                "Faulty Part Rate: " + str(self.faulty_part_rate) + "%\n")
    #def serialize_opr(self):


    def add_operation(self, operation):
        self.operations.append(operation)

    def add_operator(self):
        if self.operator_count < self.station_count:
            self.operator_count += 1
            print("Operator successfully added.")
        else:
            print("Not enough stations.")

    def add_station(self):
        self.station_count += 1

    def run(self, operation):
        loaded_part = operation.loaded_part
        
        if self.active:
            shelf, part_address = [(shelf, address) for shelf in self.warehouse.shelves for address in shelf.addresses if shelf.addresses[address] == loaded_part.id][0]

            operation.remaining_work -= 1
            if  operation.remaining_work == 0:
                if loaded_part.operations_done < len(loaded_part.operations) - 1:
                    loaded_part.operations_done += 1

                else:
                    loaded_part.operations_done = 0
                    shelf.finished_part_stocks[part_address] += operation.part_amount
                    shelf.unfinished_part_stocks[part_address] -= operation.part_amount

    def ass_run(self, operation):
        loaded_part = operation.loaded_part

        if self.active:
            shelf, part_address = [(shelf, address) for shelf in self.warehouse.shelves for address in shelf.addresses if shelf.addresses[address] == loaded_part.id][0]
            operation.remaining_work -= 1
            if  operation.remaining_work == 0:
                shelf.finished_part_stocks[part_address] -= operation.part_amount

    def run_all_stations(self):
        operations_run = 0
        i = 0
        while True:
            if i < len(self.operations):
                if self.operations[i].remaining_work > 0:
                    if 'ASS' not in self.id:
                        unfinished_part_stock = self.warehouse.check_unfinished_part_stocks(self.operations[i].loaded_part.id)
                        if self.operations[i].part_amount <= unfinished_part_stock:
                            self.run(self.operations[i])
                            operations_run += 1
                    else:
                        workorder = [workorder for workorder in self.workorders if workorder.id == self.operations[i].workorder_id][0]
                        product = [product for product in self.products if product.id == self.operations[i].product_id][0]
                        are_all_parts_available = product.check_stock_for_assembly(self.warehouse, workorder.loaded_products[product.id], workorder)

                        if are_all_parts_available:
                            finished_part_stock = self.warehouse.check_finished_part_stocks(self.operations[i].loaded_part.id)
                            if self.operations[i].part_amount <= finished_part_stock:
                                self.ass_run(self.operations[i])
                                operations_run += 1
                i += 1
                if operations_run >= self.operator_count:
                    break
            else:
                break

class Assembly(WorkCenter):
    def __init__(self, warehouse, workcenters, workorders, products):
        super().__init__(warehouse=warehouse, workcenters=workcenters, prod_method="Assembly",
                         products=products, workorders=workorders)
        DEFAULT_STATION_COUNT = 10
        DEFAULT_OPERATOR_COUNT = 3
        self.station_count = DEFAULT_STATION_COUNT
        self.operator_count = DEFAULT_OPERATOR_COUNT

class Warehouse:
    def __init__(self):
        self.shelves = []
        self.product_storage = {}
        self.raw_material_stocks = {}
        
    def __str__(self):
        shelf_codes = [shelve.shelve_code for shelve in self.shelves]
        return ("Shelves: " + shelf_codes + "\n")

    def serialize(self):
        serialized_shelves = {}
        #for index, shelf in enumerate(self.shelves):
        #    serialized_shelves[f"shelf_{index}"] = shelf.serialize()
        return {
            "shelves": {f"shelf_{i}": shelf.serialize() for i, shelf in enumerate(self.shelves)},
            "product_storage": self.product_storage,
            "raw_material_stocks": self.raw_material_stocks
        }

    def check_unfinished_part_stocks(self, part_code):
        for shelve in self.shelves:
            for address in shelve.addresses:
                if shelve.addresses[address] == part_code: 
                    return shelve.unfinished_part_stocks[address]
        return None
    
    def check_finished_part_stocks(self, part_code):
        for shelve in self.shelves:
            for address in shelve.addresses:
                if shelve.addresses[address] == part_code: 
                    return shelve.finished_part_stocks[address]
        return None
                
    def add_shelf(self):
        all_shelf_codes = string.ascii_uppercase
        existing_shelf_codes = [shelf.code for shelf in self.shelves]
        code = [letter for letter in all_shelf_codes if letter not in existing_shelf_codes][0]
        self.shelves.append(Shelf(code))
        return self.shelves[-1], code

    def allocate_space_to_part(self, part_number, part_name):
        shelf, address = self.check_shelf_space()
        shelf.addresses[address] = part_number
        shelf.partnames[address] = part_name
        return address
    
    def add_finished_stock(self,part_number):
        for shelf in self.shelves:
            for address in shelf.addresses:
                if shelf.addresses[address] == part_number:  
                    shelf.finished_part_stocks[address] += 1
    def add_unfinished_stock(self,part_number):
        for shelf in self.shelves:
            for address in shelf.addresses:
                if shelf.addresses[address] == part_number:  
                    shelf.unfinished_part_stocks[address] += 1  

    def check_shelf_space(self):
        for shelf in self.shelves:
            for address in shelf.addresses:
                if shelf.addresses[address] == '':
                    return shelf, address
        new_shelf, code = self.add_shelf()
        initial_address = code + "1"
        return new_shelf, initial_address

class Shelf:
    def __init__(self, code):

        STORAGE_LIMIT = 101
        self.code = code
        self.addresses = {f"{code}{str(num)}": '' for num in range(1,STORAGE_LIMIT)}
        self.finished_part_stocks = {f"{code}{str(num)}": 0 for num in range(1,STORAGE_LIMIT)}
        self.being_worked_on = {f"{code}{str(num)}": 0 for num in range(1,STORAGE_LIMIT)}
        self.unfinished_part_stocks = {f"{code}{str(num)}": 0 for num in range(1,STORAGE_LIMIT)}
        self.partnames = {f"{code}{str(num)}": '' for num in range(1,STORAGE_LIMIT)}

    def serialize(self):
        return {
            "code": self.code,
            "addresses": self.addresses,
            "finished_part_stocks": self.finished_part_stocks,
            "being_worked_on": self.being_worked_on,
            "unfinished_part_stocks": self.unfinished_part_stocks,
            "partnames": self.partnames
        }

    def add_part():
        pass

    def __str__(self):
        return ("Shelf Adress: " + str(self.addresses) + "-- Finshed: " + {self.finished_part_stocks} + "-- Unfinished: " + {self.unfinished_part_stocks} + "-- On The Way: " + {self.on_the_way_stocks} + "\n")

class Product:
    def __init__(self, size, warehouse, products, workorders, raw_materials, production_methods, 
                 part_name_data, workcenters, selling_dict, planning_dict, leaning_weights,
                 production_type_leaning):
        part_counts = {
            'LG': 40,
            'MD': 20,
            'SM': 10,
            }
        self.product_types = [key for key in part_name_data[0]] 
        self.raw_materials = raw_materials
        self.raw_materials_need = {}
        while True:
            digits = ''.join(random.choices(string.digits, k=6))
            generated_product_number = 'E' + digits + size

            #self.id = ''
            existing_product_numbers = [product.id for product in products]
            if generated_product_number not in existing_product_numbers:
                self.id = generated_product_number
                break
        
        self.production_type_leaning = production_type_leaning
        self.part_count = part_counts.get(size, 0) + random.randint(-5, 5)
        self.product_type = self.product_types[random.randint(0,6)]

        self.product_parts = [Part(self, warehouse, raw_materials, production_methods, part_name_data, self.product_type, leaning_weights, production_type_leaning) for i in range(self.part_count)]

        amounts = [1, 2, 3, 4, 5, 6, 7, 8]
        weights_amounts = [10, 3, 1, 1, 1, 1, 1, 1]

        self.part_amounts = {part.id: random.choices(amounts, weights=weights_amounts, k=1)[0] for part in self.product_parts}
        selling_dict[self.id] = 0
        planning_dict[self.id] = 0

        self.production_cost = int(self.calculate_base_cost(workcenters=workcenters))
        for i in range(len(part_counts)): # makes the larger machines more profitable
            if self.id[-2:] == "LG":
                profit_balancer = 1.4
            elif self.id[-2:] == "MD":
                profit_balancer = 1.2
            else:
                profit_balancer = 1

        self.permanent_modifier = profit_balancer
        self.sale_price = int(self.production_cost * self.permanent_modifier)
        #warehouse.product_storage[self.id] = math.floor(15000/self.sale_price)
        warehouse.product_storage[self.id] = 0
        self.exchange = self.production_cost - self.sale_price
        
        self.total_assembly_time = sum(part.assembly_time * self.part_amounts[part.id] for part in self.product_parts)
        self.total_manufacturing_time = sum(part.operation_times[i] * self.part_amounts[part.id] for part in self.product_parts for i in range(len(part.operation_times)))

    def calculate_base_cost(self, workcenters):
        total_raw_part_cost = sum(part.raw_material.cost * self.part_amounts[part.id] for part in self.product_parts)
        operation_times = [operation_time for part in self.product_parts for operation_time in part.operation_times]
        self.total_operation_turncount = sum(sum(part.operation_times) * self.part_amounts[part.id]  for part in self.product_parts)
        default_operating_cost = workcenters[0].operating_cost
        base_operating_cost = self.total_operation_turncount * default_operating_cost
        base_cost = total_raw_part_cost + base_operating_cost
        return base_cost

    def list_part_amounts(self):
        for item in self.part_amounts:
            print(f"{item}: {self.part_amounts[item]}")
    
    def calculate_raw_material_need(self, workorder):
        for raw_material in self.raw_materials:
            self.raw_materials_need[raw_material.code] = 0
        for part in self.product_parts:
            part_count = self.part_amounts[part.id]
            self.raw_materials_need[part.raw_material.code] += part_count * workorder.loaded_products[self.id]
        return self.raw_materials_need
    
    def check_stock_for_assembly(self, warehouse, prd_count, workorder):
        flag = workorder.all_parts_manufactured[self.id]
        if prd_count == 0:
            prd_count = 1
        if flag == False:
            flag = True
            for part in self.product_parts:
                stock = warehouse.check_finished_part_stocks(part.id)
                need = self.part_amounts[part.id] * prd_count
                if need > stock:
                    flag = False
                    break
        if flag == True:
            workorder.all_parts_manufactured[self.id] = True
        return flag
        


class Part:
    def __init__(self, current_product, warehouse, raw_materials, production_methods, part_name_data, product_type, leaning_weights, production_type_leaning):

        assembly_times = [1, 1, 1, 2, 3]
        weights_assembly_times = [5, 4, 3, 2, 1]
        self.assembly_time = random.choices(assembly_times, weights=weights_assembly_times, k=1)[0]

        lead_times = [2, 5, 7, 10, 13]
        weights_lead_times = [3, 3, 3, 2, 1]
        self.lead_time = random.choices(lead_times, weights=weights_lead_times, k=1)[0]

        self.raw_material = random.choices(raw_materials, weights=leaning_weights, k=1)[0]
        self.raw_material_name = self.raw_material.name
        raw_material_operation_count = len(self.raw_material.prod_types)
        if self.raw_material.code not in ["E1"]:
            if production_type_leaning in self.raw_material.prod_types:
                index = self.raw_material.prod_types.index(production_type_leaning)
            else:
                index = None
            prod_weights = []
            for i in range(len(self.raw_material.prod_types)):
                if i == index:
                    prod_weights.append(4)
                else:
                    prod_weights.append(1)
            self.operations = random.choices(self.raw_material.prod_types, weights=prod_weights, k=random.randint(1,raw_material_operation_count))
        else:
            self.operations = []
        operation_times_list = [1, 1, 1, 2, 3]
        weights_operation_times = [5, 4, 3, 2, 1]
        self.operation_times = [random.choices(operation_times_list, weights=weights_operation_times, k=1)[0] for operation in self.operations]

        digits = ''.join(random.choices(string.digits, k=6))
        self.id = 'P' + digits + self.raw_material.name.upper()[:3]

        part_names = [row[product_type] for row in part_name_data]
        self.name = random.choices(part_names, k=1)[0]

        self.part_storage_loc = warehouse.allocate_space_to_part(part_number=self.id, part_name=self.name)
        self.faulty = False

        self.operations_done = 0

    def __str__(self):
        return ("Part Number: " + str(self.id) + "\n" +
                "Part Name: " + str(self.name) + "\n" +
                "Assembly Time: " + str(self.assembly_time) + " turns\n" +
                "Raw Material Lead Time: " + str(self.lead_time) + " turns\n" +
                "Raw Material: " + str(self.raw_material.name) + "\n" +
                "Raw Material Cost: " + str(self.raw_material.cost) + "$\n" +
                "Operations: " + str(self.operations) + "\n" +
                "Operation Times: " + str(self.operation_times) + " turns\n" +
                "Part Storage Location: " + str(self.part_storage_loc) + "\n" +
                "Batch Number: " + str(self.batch_num) + "\n")

class RawMaterial:
    def __init__(self, raw_material_code, raw_material_name, raw_material_prod_types, warehouse):
        price_range = [10, 20, 30, 40 ,50, 60]
        self.cost = random.choices(price_range)[0]
        self.code = raw_material_code
        self.name = raw_material_name
        self.prod_types = raw_material_prod_types
        
        warehouse.raw_material_stocks[self.code] = 50

        self.permanent_modifier = 1
        lead_times = [2, 5, 7, 10, 13]
        weights_lead_times = [3, 3, 3, 2, 1]
        self.lead_time = random.choices(lead_times, weights=weights_lead_times, k=1)[0]

        order_quantities = [10, 20, 30, 40, 50]
        order_quantity_weights = [5, 4, 3, 2, 1]
        self.minimum_order_quantity = random.choices(order_quantities, weights=order_quantity_weights, k=1)[0]