let selling_dict = {};
let planning_dict = {};
let inventory = {};
let customer_order_dict = {};
let workcenter_ids = [];
let funds = 0;

document.addEventListener('DOMContentLoaded', function () {
    let selling_dict_element = document.querySelector("#selling_dict_dataCache")
    if (selling_dict_element) {
        let selling_dict_json = selling_dict_element.getAttribute("data-cache");
        selling_dict =  JSON.parse(selling_dict_json);
    } else {
        selling_dict = null
    }
    let inventory_element = document.querySelector("#inventory_dataCache");
    if (inventory_element) {
        let inventory_json = inventory_element.getAttribute("data-cache");
        inventory =  JSON.parse(inventory_json);
    } else {
        inventory = null
    }
    let customer_order_dict_element = document.querySelector("#customer_order_dataCache");
    if (customer_order_dict_element) {
        let customer_order_dict_json = customer_order_dict_element.getAttribute("data-cache");
        customer_order_dict =  JSON.parse(customer_order_dict_json);
    } else {
        customer_order_dict = null
    }
    let funds_element = document.querySelector("#funds_dataCache");
    if (funds_element) {
        let funds_json = funds_element.getAttribute("data-cache");
        funds =  JSON.parse(funds_json);
    } else {
        funds = null
    }
    let planning_dict_element = document.querySelector("#planning_dict_dataCache");
    if (planning_dict_element) {
        let planning_dict_json = planning_dict_element.getAttribute("data-cache");
        planning_dict =  JSON.parse(planning_dict_json);
    } else {
        planning_dict = null
    }
    let workcenter_ids_elemement = document.querySelector("#workcenters_dataCache");
    if (workcenter_ids_elemement) {
        let workcenter_ids_json = workcenter_ids_elemement.getAttribute("data-cache");
        workcenter_ids = JSON.parse(workcenter_ids_json);   
    }

    workcenter_ids.forEach(workcenter_id => {
        let current_workcenter_stop = document.querySelector(`#production_${workcenter_id}_stop`);
        if (current_workcenter_stop) {
            current_workcenter_stop.addEventListener("click", async function (event) {
                event.preventDefault()
                const response = await fetch("/production/stop_workcenter", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({data: this.getAttribute("id")})
                }); 
                if (!response.ok) {
                    throw new Error(`Http error!  status: ${response.status}`);
                }
                const responseData = response.json();
                console.log(responseData);
                location.reload();
            });
        }
        let current_workcenter_start = document.querySelector(`#production_${workcenter_id}_start`);
        if (current_workcenter_start) {
            current_workcenter_start.addEventListener("click", async function (event) {
                event.preventDefault()
                const response = await fetch("/production/start_workcenter", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({data: this.getAttribute("id")})
                }); 
                if (!response.ok) {
                    throw new Error(`Http error! status: ${response.status}`);
                }
                const responseData = response.json();
                console.log(responseData);
                location.reload();
            });
        }
    });
    const raw_material_widgets = document.querySelectorAll(".raw_material_widget");
    if (raw_material_widgets.length > 0) {
        for (let i=0;i<raw_material_widgets.length;i++) {
            raw_material_widgets[i].addEventListener("click", async function() {
                const response = await fetch("/procurement/select_material", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify(this.id)
                });
                if (!response.ok) {
                    throw new Error(`Http error!  status: ${response.status}`);
                }
                const responseData = await response.json();
                location.reload();
            });
            
        }
    }
    const innerButtons = document.querySelectorAll(".btn-success, .btn-close, .btn-primary, .procurement_quantity, .modal");
    innerButtons.forEach(button => {
        button.addEventListener("click", function(event) {
            event.stopPropagation();
        });
    });

})

const sales_add_product_button = document.querySelector("#sales_add_product")
if (sales_add_product_button) {
    sales_add_product_button.addEventListener("click", function() {
        const select_value = document.querySelector("#sales_select_product").value;
        const sales_table_body = document.querySelector("#sales_selling_table");
    
        if (select_value != "Select Product") {
            if  (selling_dict[select_value] < inventory[select_value] && selling_dict[select_value] < customer_order_dict[select_value]) {
                selling_dict[select_value] += 1;
            }
        }
        while (sales_table_body.firstChild) {
            sales_table_body.removeChild(sales_table_body.firstChild);
        }
        for (let product in selling_dict) {
            if (selling_dict[product] != 0) {
                const new_row = document.createElement("tr");
    
                const id_col = document.createElement("td");
                const quan_col = document.createElement("td");
                id_col.innerText = product;
                quan_col.innerText = selling_dict[product];
                new_row.appendChild(id_col);
                new_row.appendChild(quan_col);
                sales_table_body.appendChild(new_row);
            }
        }
    })
}

const sales_clear_product_button = document.querySelector("#sales_clear_product");
if (sales_clear_product_button) {
    sales_clear_product_button.addEventListener("click", function() {
        const sales_table_body = document.querySelector("#sales_selling_table");
        while (sales_table_body.firstChild) {
            sales_table_body.removeChild(sales_table_body.firstChild);
            Object.keys(selling_dict).forEach(key => {
                selling_dict[key] = 0;
            });
        }
    })
        
}

const sales_sell_product_button = document.querySelector("#sales_sell_product");
if (sales_sell_product_button) {
    sales_sell_product_button.addEventListener("submit",async function(event) {
        const response = await fetch("/sales/sell_product", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({data: selling_dict})
        });
        if (!response.ok) {
            throw new Error(`Http error! status: ${response.status}`);
        }
    
        let response_data = await response.json();
        let total_funds_gained = response_data["message"];
        document.querySelector("#funds").innerHTML = `Funds: ${total_funds_gained+funds}`;
    })    
}

const sales_select_product_field = document.querySelector("#sales_select_product");
if (sales_select_product_field) {
    sales_select_product_field.addEventListener("change",async function() {
        const sales_plot_img = document.querySelector("#sales_plot_img");
        const product_id = this.value;
        const response = await fetch("/sales/replot", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({data: product_id})
        });
        if (!response.ok) {
            throw new Error(`Http error!  status: ${response.status}`);
        } 
        responseData = await response.json();
        const timestamp = new Date().getTime();
        sales_plot_img.setAttribute('src', `/static/plot.png?t=${timestamp}`);
    })    
}

const planning_add_product_button = document.querySelector("#planning_add_product"); 
if (planning_add_product_button) {
    planning_add_product_button.addEventListener("click", function() {
        const select_value = document.querySelector("#planning_select_product").value;
        const planning_table_body = document.querySelector("#planning_workorder_table");
    
        if (select_value != "Select Product") {
            planning_dict[select_value] += 1;
        }
        while (planning_table_body.firstChild) {
            planning_table_body.removeChild(planning_table_body.firstChild);
        }
        for (let product in planning_dict) {
            if (planning_dict[product] != 0) {
                const new_row = document.createElement("tr");

                const id_col = document.createElement("td");
                const quan_col = document.createElement("td");
                id_col.innerText = product;
                quan_col.innerText = planning_dict[product];
                new_row.appendChild(id_col);
                new_row.appendChild(quan_col);
                planning_table_body.appendChild(new_row);
            }
        }
    })
}
const planning_clear_product_button = document.querySelector("#planning_clear_product");
if (planning_clear_product_button) {
    planning_clear_product_button.addEventListener("click", function() {
        const planning_table_body = document.querySelector("#planning_workorder_table");
        while (planning_table_body.firstChild) {
            planning_table_body.removeChild(planning_table_body.firstChild);
            Object.keys(planning_dict).forEach(key => {
                planning_dict[key] = 0;
            });
        }
    }) 
}

const planning_create_workorder = document.querySelector("#planning_create_workorder");
if (planning_create_workorder) {
    planning_create_workorder.addEventListener("click", async function(event) {
        event.preventDefault()
        const response = await fetch("/planning/create_workorder", {
            method: "POST",
            headers: {"Content-Type": "application/json",},
            body: JSON.stringify({data: planning_dict})
        }); 
        if (!response.ok) {
            throw new Error(`Http error!  status: ${response.status}`)
        } let responseData = await response.json();
        location.reload();
    })
} 

const planning_select_product = document.querySelector("#planning_select_product")
if (planning_select_product) {
    planning_select_product.addEventListener("change", async function() {
        const product_id = this.value;
        const response = await fetch("/planning/product_change", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({data: product_id})
        });
        if (!response.ok) {
            throw new Error(`Http error!  status: ${response.status}`);
        }
        let response_data = await response.json();
        console.log(response_data);
        //let total_funds_gained = response_data["message"];
        const general_info_table_tbody = document.querySelector("#planning_general_table_tbody");
        const bom_table_tbody = document.querySelector("#planning_bom_table_tbody");
    
        while(general_info_table_tbody.firstChild) {
            general_info_table_tbody.removeChild(general_info_table_tbody.firstChild)
        }
        while(bom_table_tbody.firstChild) {
            bom_table_tbody.removeChild(bom_table_tbody.firstChild)
        }
    
        for (let i=0;i<Object.keys(response_data[1]).length;i++) {
            const new_row = document.createElement("tr")
            const col_1 = document.createElement("td")
            const col_2 = document.createElement("td")
    
            col_1.innerText = Object.keys(response_data[1])[i]
            col_2.innerText = response_data[1][Object.keys(response_data[1])[i]]
    
            new_row.appendChild(col_1)
            new_row.appendChild(col_2)
            general_info_table_tbody.appendChild(new_row)
        }
        const headers = ["No", "Part ID", "Part Name", "Amount", "Assembly Time", "Raw Material", "RM Cost", "Operations", "Operation Times"];
        for (let i=0;i<response_data[0].length;i++) {
            const new_row = document.createElement("tr")
            for (let j=0;j<headers.length;j++) {
                const col = document.createElement("td")
                col.innerText = response_data[0][i][headers[j]]
                new_row.appendChild(col)
            }
            bom_table_tbody.appendChild(new_row)
        }
    })
}

//planning tree view
var toggler = document.getElementsByClassName("caret");

if (toggler) {
    var i;

    for (i = 0; i < toggler.length; i++) {
      toggler[i].addEventListener("click", function() {
        this.parentElement.querySelector(".nested").classList.toggle("active");
        this.parentElement.querySelector(".caret-svg").classList.toggle("rotated");

      });

    }   
    
    const logistics_workorder_select = document.querySelector("#logistics_workorder_select");
    if (logistics_workorder_select) {
        logistics_workorder_select.addEventListener("change", async function (event) {
            event.preventDefault()
            const product_select = document.querySelector("#logistics_product_select")
            const response = await fetch("/logistics/get_product", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(this.value)
            });
            if (!response.ok) {
                throw new Error(`Http error!  status: ${response.status}`)
            }
            const responseData = await response.json()
        
            responseData.forEach(item => {
                const new_option = document.createElement("option")
                new_option.innerText = item
                product_select.appendChild(new_option)
            });
        })
    }
}

const logistics_product_select = document.querySelector("#logistics_product_select");
if (logistics_product_select) {
    logistics_product_select.addEventListener("change", async function (event) {
        event.preventDefault()
        const workorder_id = document.querySelector("#logistics_workorder_select").value
        const response = await fetch("/logistics/calculate_raw_material_need", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify([this.value, workorder_id])
        });
        if (!response.ok) {
            throw new Error(`Http error!  status: ${response.status}`)
        }
        const responseData = await response.json()
        console.log(responseData)
    
        const logistics_raw_materials_tbody = document.querySelector("#logistics_raw_materials_tbody");
        while(logistics_raw_materials_tbody.childNodes.length > 0) {
            logistics_raw_materials_tbody.firstChild.remove();
        }
    
        responseData.forEach(row => {
            const new_row = document.createElement("tr");
            row.forEach(element => {
                const new_col = document.createElement("td");
                new_col.innerText = element;
                new_row.appendChild(new_col);
            });
            logistics_raw_materials_tbody.appendChild(new_row)
        });
    })
}



