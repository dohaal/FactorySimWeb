from flask import Blueprint, render_template,current_app, request, redirect, url_for, session

production = Blueprint("production", __name__, static_folder="static", template_folder="templates")

@production.route("/")
def main():
    current_app.current_page = "production"

    date = current_app.current_date
    day = current_app.days_of_the_week[current_app.current_date.weekday()]
    funds = current_app.funds
    workcenters = current_app.workcenters
    current_workcenter_id = session.get('workcenter_id', workcenters[0].id)
    current_workcenter = [wc for wc in current_app.workcenters if current_workcenter_id == wc.id][0]
    workcenter_ids = [workcenter.id for workcenter in workcenters]


    current_operations_total_work = sum(operation.remaining_work for workcenter in workcenters for operation in workcenter.operations if workcenter.id == current_workcenter_id)
    if len(workcenters[0].operations) > 0:
        initial_workorder = [workorder for workorder in current_app.workorders if workorder.id == workcenters[0].operations[0].workorder_id][0]
    else:
        initial_workorder = None

    return render_template("production.html", date=date, day=day, funds=funds, workcenters=workcenters, 
                           current_operations_total_work=current_operations_total_work, initial_workorder=initial_workorder,
                           current_workcenter = current_workcenter, workcenter_ids=workcenter_ids)

@production.route("/workstation", methods=["POST", "GET"])
def workstation():
    workcenter_id = request.form.get("workcenter_data")
    
    session["workcenter_id"] = workcenter_id
    return redirect(url_for("production.main"))

@production.route("/start_workcenter", methods=["POST"])
def start_workcenter():
    data = request.get_json("data")["data"]

    if data:
        data_list = data.split(('_'))
        workcenter_id = data_list[1]

        current_workcenter = [workcenter for workcenter in current_app.workcenters if workcenter.id == workcenter_id][0]
        if len(current_workcenter.operations) > 0:
            current_workcenter.active = True
        else:
            current_workcenter.active = False
        return ("ok", 200)
    else:
        return("error", 400)

@production.route("/stop_workcenter", methods=["POST"])
def stop_workcenter():
    data = request.get_json("data")["data"]

    if data:
        data_list = data.split(('_'))
        workcenter_id = data_list[1]

        current_workcenter = [workcenter for workcenter in current_app.workcenters if workcenter.id == workcenter_id][0]
        current_workcenter.active = False
        return ("ok", 200)
    else:
        return("error", 400)