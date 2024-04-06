from data_input import *
from draw_figure import *
from printtxt import *

import datetime
import gurobipy as gp

UB = 10000000000000000000
sub_LB = 0

MP = gp.Model('master')
y = {k: MP.addVar(vtype=gp.GRB.BINARY, name='y'.format(k), lb=0) for k in range(num_f_train)}
lamda = MP.addVar(vtype=gp.GRB.CONTINUOUS, name='sigma', lb=0)
sigma = {j: MP.addVar(vtype=gp.GRB.CONTINUOUS, name='chi'.format(j), lb=0) for j in range(num_demand)}
x = {(j, k): MP.addVar(vtype=gp.GRB.BINARY, name='x'.format(j, k), lb=0) for j in range(num_demand) for k in
     range(num_f_train)}
a = {(k, s): MP.addVar(vtype=gp.GRB.CONTINUOUS, name='a'.format(k, s), lb=0) for k in range(num_f_train) for s in
     range(num_station)}
d = {(k, s): MP.addVar(vtype=gp.GRB.CONTINUOUS, name='d'.format(k, s), lb=0) for k in range(num_f_train) for s in
     range(num_station)}
h = {k: MP.addVar(vtype=gp.GRB.CONTINUOUS, name='h'.format(k), lb=lower_shift[k], ub=upper_shift[k]) for k in
     range(num_p_train)}
z = {(j, jj): MP.addVar(vtype=gp.GRB.BINARY, name='z'.format(j, j), lb=0) for j in range(num_demand) for jj in
     range(num_demand)}

# objective function
expr = gp.LinExpr()
for k in range(num_f_train):
    expr += cost_service * y[k]
expr += lamda
MP.setObjective(expr)
MP.addConstr(lamda >= sub_LB)

sub_expr = gp.LinExpr()
for j in data_demand:
    sub_expr += data_demand[j].pd * sigma[j]
    sub_expr += data_demand[j].pn
    for k in range(num_f_train):
        sub_expr -= data_demand[j].pn * x[j, k]
MP.addConstr(lamda >= sub_expr)

MP_con_demand_unique = {(j, s):
    MP.addLConstr(
        lhs=gp.quicksum(x[j, k] for k in range(num_f_train)),
        rhs=1,
        sense=gp.GRB.LESS_EQUAL,
        name="MP_con_demand_unique" + str(j) + str(s))
    for j in data_demand for s in range(num_station)}

MP_con_demand_capacity = {(k, s):
    MP.addLConstr(
        lhs=gp.quicksum(data_demand[j].P * x[j, k] for j in set_demand_tra[s]),
        rhs=capacity_f_train,
        sense=gp.GRB.LESS_EQUAL,
        name="MP_con_demand_capacity" + str(k) + str(s))
    for k in range(num_f_train) for s in range(num_station)}

MP_con_demand_platform_capacity = {j:
    MP.addLConstr(
        lhs=data_demand[j].P + gp.quicksum(data_demand[j].P * z[j, jj] for jj in set_demand_ori[data_demand[j].I]),
        rhs=capacity_station,
        sense=gp.GRB.LESS_EQUAL,
        name="MP_con_demand_platform_capacity" + str(j))
    for j in data_demand}

MP_con_demand_define_z = {(j, jj, k):
    MP.addLConstr(
        lhs=a[k, data_demand[j].I],
        rhs=data_demand[j].R + num_T * (1 - x[jj, k] + z[jj, j]),
        sense=gp.GRB.LESS_EQUAL,
        name="MP_con_demand_define_z" + str(j) + str(jj) + str(k))
    for j in data_demand for jj in set_demand_ori[data_demand[j].I] for k in range(num_f_train)}

MP_con_demand_ready = {(j, k):
    MP.addLConstr(
        lhs=data_demand[j].R * x[j, k],
        rhs=a[k, data_demand[j].I],
        sense=gp.GRB.LESS_EQUAL,
        name="MP_con_demand_ready" + str(j) + str(k))
    for j in data_demand for k in range(num_f_train)}

MP_con_demand_within_time = {(j, k):
    MP.addLConstr(
        lhs=a[k, data_demand[j].E],
        rhs=num_T * (2 - x[j, k]),
        sense=gp.GRB.LESS_EQUAL,
        name="MP_con_demand_within_time" + str(j) + str(k))
    for j in data_demand for k in range(num_f_train)}

MP_con_demand_waiting = {(k, s):
    MP.addLConstr(
        lhs=d[k, s] - a[k, s],
        rhs=num_T * (gp.quicksum(x[j, k] for j in set_demand_ori[s]) + gp.quicksum(x[j, k] for j in set_demand_des[s])),
        sense=gp.GRB.LESS_EQUAL,
        name="MP_con_demand_waiting" + str(k) + str(s))
    for k in range(num_f_train) for s in range(num_station)}

MP_con_demand_travel = {(k, s):
    MP.addLConstr(
        lhs=a[k, s + 1] - d[k, s],
        rhs=lower_travel[s],
        sense=gp.GRB.GREATER_EQUAL,
        name="MP_con_demand_travel" + str(k) + str(s))
    for k in range(num_f_train) for s in range(num_station - 1)}

MP_con_demand_delay = {(j, k):
    MP.addLConstr(
        lhs=sigma[j],
        rhs=a[k, data_demand[j].E] - data_demand[j].B - num_T * (1 - x[j, k]),
        sense=gp.GRB.GREATER_EQUAL,
        name="MP_con_demand_delay" + str(j) + str(k))
    for j in data_demand for k in range(num_f_train)}

MP_con_demand_cargo_train = {(j, k):
    MP.addLConstr(
        lhs=x[j, k],
        rhs=y[k],
        sense=gp.GRB.LESS_EQUAL,
        name="MP_con_demand_cargo_train" + str(j) + str(k))
    for j in data_demand for k in range(num_f_train)}

MP_con_passenger_station = {k:
    MP.addLConstr(
        lhs=data_A[k][0] - data_D[k - 1][0] + h[k] + h[k - 1],
        rhs=lower_headway_station,
        sense=gp.GRB.GREATER_EQUAL,
        name="MP_con_passenger_station" + str(k))
    for k in range(1, num_f_train)}

MP_con_passenger_segment = {k:
    MP.addLConstr(
        lhs=data_D[k][0] - data_D[k - 1][0] + h[k] + h[k - 1],
        rhs=lower_headway_segment,
        sense=gp.GRB.GREATER_EQUAL,
        name="MP_con_passenger_segment" + str(k))
    for k in range(1, num_f_train)}

MP_con_passenger_station_before = {(k, s):
    MP.addLConstr(
        lhs=a[k, s] - data_D[k][s] - h[k],
        rhs=lower_headway_station - num_T * (1 - y[k]),
        sense=gp.GRB.GREATER_EQUAL,
        name="MP_con_passenger_station_before" + str(k))
    for k in range(num_f_train) for s in range(num_station)}

MP_con_passenger_station_after = {(k, s):
    MP.addLConstr(
        lhs=data_D[k + 1][s] + h[k + 1] - a[k, s],
        rhs=lower_headway_station - num_T * (1 - y[k]),
        sense=gp.GRB.GREATER_EQUAL,
        name="MP_con_passenger_station_after" + str(k))
    for k in range(num_f_train) for s in range(num_station)}

MP_con_passenger_freight_segment_before = {(k, s):
    MP.addLConstr(
        lhs=d[k, s] - data_D[k][s] - h[k],
        rhs=lower_headway_segment - num_T * (1 - y[k]),
        sense=gp.GRB.GREATER_EQUAL,
        name="MP_con_passenger_freight_segment_before" + str(k))
    for k in range(num_f_train) for s in range(num_station)}

MP_con_passenger_freight_segment_after = {(k, s):
    MP.addLConstr(
        lhs=data_D[k + 1][s] + h[k + 1] - d[k, s],
        rhs=lower_headway_segment - num_T * (1 - y[k]),
        sense=gp.GRB.GREATER_EQUAL,
        name="MP_con_passenger_freight_segment_after" + str(k))
    for k in range(num_f_train) for s in range(num_station)}
#
MP_con_passenger_wait = {k:
    MP.addLConstr(
        lhs=data_A[k][0] - data_D[k - 1][0] + h[k] - h[k - 1],
        rhs=upper_headway_passenger,
        sense=gp.GRB.LESS_EQUAL,
        name="MP_con_passenger_segment" + str(k))
    for k in range(1, num_f_train)}
MP_con_passenger_wait_before = {k:
    MP.addLConstr(
        lhs=data_A[k][0] - data_D[k - 1][0] + h[k] + h[k - 1],
        rhs=lower_headway_passenger,
        sense=gp.GRB.GREATER_EQUAL,
        name="MP_con_passenger_segment" + str(k))
    for k in range(1, num_f_train)}

time_start = datetime.datetime.now()

MP.Params.OutputFlag = 0
MP.ModelSense = gp.GRB.MINIMIZE
MP.optimize()

iter_count = 0

LB = MP.ObjVal
MP_y = [round(y[k].x) for k in range(num_f_train)]
SP, con_demand_cargo_train, con_passenger_station_before, con_passenger_station_after, \
    con_passenger_freight_segment_before, con_passenger_freight_segment_after, \
    con_passenger_define_no_freight_overcrowded = subproblem(MP_y)
SP.Params.OutputFlag = 0
SP.ModelSense = gp.GRB.MINIMIZE

while LB + 0.0001 < UB:
    iter_count += 1
    # Solve sub problems
    SP.optimize()
    # Judge which cut to add
    if SP.status == gp.GRB.Status.OPTIMAL:
        MP.addConstr(lamda >= (SP.ObjVal - sub_LB) * (
                1 - gp.quicksum(y[k] for k in range(num_f_train) if MP_y[k] <= 0.1)) + sub_LB)
        MP.update()
        UB = min(UB, SP.ObjVal + sum(cost_service * MP_y[k] for k in range(num_f_train)))
    else:
        MP.addConstr(gp.quicksum(y[k] for k in range(num_f_train) if MP_y[k] >= 0.9) <= round(sum(MP_y)) - 1)

    MP.optimize()
    MP_y = [round(y[k].x) for k in range(num_f_train)]
    if MP.status != gp.GRB.Status.OPTIMAL:
        print('Optimization was stopped with status %d' % MP.status)
        MP.computeIIS()
        for c in MP.getConstrs():
            if c.IISConstr:
                print('%s' % c.constrName)
    LB = max(MP.ObjVal, LB)
    print(iter_count, MP_y, UB, LB, lamda.x)
    timetable_f = {}
    for k in range(num_f_train):
        new_cycle = []
        if y[k].x > 0.99:
            for s in range(num_station):
                new_cycle.append(a[k, s].x)
                new_cycle.append(d[k, s].x)
            timetable_f[k] = new_cycle

    x_var = [[x[j, k].x for k in range(num_f_train)] for j in data_demand]
    sigma_var = [sigma[j].x for j in data_demand]
    subproblem_update(MP_y, SP)

time_end = datetime.datetime.now()

print('Optimal solution value', UB)
print('CPU time', time_end - time_start)
