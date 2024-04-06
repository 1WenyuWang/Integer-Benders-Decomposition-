time_start = datetime.datetime.now()

MIP = gp.Model("MIP")

x = {(j, k): MIP.addVar(vtype=gp.GRB.BINARY, name='x'.format(j, k),lb=0) for j in range(num_demand) for k in range(num_f_train)}
sigma = {j: MIP.addVar(vtype=gp.GRB.CONTINUOUS, name='chi'.format(j),lb=0) for j in range(num_demand)}
y = {k: MIP.addVar(vtype=gp.GRB.BINARY, name='y'.format(k),lb=0) for k in range(num_f_train)}
a = {(k, s): MIP.addVar(vtype=gp.GRB.INTEGER, name='a'.format(k, s),lb=0) for k in range(num_f_train) for s in range(num_station)}
d = {(k, s): MIP.addVar(vtype=gp.GRB.INTEGER, name='d'.format(k, s),lb=0) for k in range(num_f_train) for s in range(num_station)}
h = {k: MIP.addVar(vtype=gp.GRB.INTEGER, name='h'.format(k),lb=lower_shift[k],ub=upper_shift[k]) for k in range(num_p_train)}
z = {(j, jj): MIP.addVar(vtype=gp.GRB.BINARY, name='z'.format(j, j),lb=0) for j in range(num_demand) for jj in range(num_demand)}
xi = {(k, t): MIP.addVar(vtype=gp.GRB.BINARY, name='xi'.format(k, t),lb=0) for k in range(num_p_train) for t in range(num_T)}

# objective function
expr = gp.LinExpr()
for j in data_demand:
    expr += data_demand[j].pd*sigma[j]
    expr += data_demand[j].pn
    for k in range(num_f_train):
        expr -= data_demand[j].pn*x[j, k]
for k in range(num_f_train):
    expr += cost_service*y[k]
MIP.setObjective(expr)

# constraints
con_demand_unique = {(j, s):
    MIP.addLConstr(
        lhs=gp.quicksum(x[j, k] for k in range(num_f_train)),
        rhs=1,
        sense=gp.GRB.LESS_EQUAL,
        name="con_demand_unique" + str(j) + str(s))
    for j in data_demand for s in range(num_station)}

con_demand_capacity = {(k, s):
    MIP.addLConstr(
        lhs=gp.quicksum(data_demand[j].P*x[j, k] for j in set_demand_tra[s]),
        rhs=capacity_f_train,
        sense=gp.GRB.LESS_EQUAL,
        name="con_demand_capacity" + str(k) + str(s))
    for k in range(num_f_train) for s in range(num_station)}

con_demand_platform_capacity = {j:
    MIP.addLConstr(
        lhs=data_demand[j].P+gp.quicksum(data_demand[j].P*z[j, jj] for jj in set_demand_ori[data_demand[j].I]),
        rhs=capacity_station,
        sense=gp.GRB.LESS_EQUAL,
        name="con_demand_platform_capacity" + str(j))
    for j in data_demand}

con_demand_define_z = {(j, jj, k):
    MIP.addLConstr(
        lhs=a[k, data_demand[j].I],
        rhs=data_demand[j].R+num_T*(1-x[jj, k]+z[jj, j]),
        sense=gp.GRB.LESS_EQUAL,
        name="con_demand_define_z" + str(j) + str(jj) + str(k))
    for j in data_demand for jj in set_demand_ori[data_demand[j].I] for k in range(num_f_train)}

con_demand_ready = {(j, k):
    MIP.addLConstr(
        lhs=data_demand[j].R*x[j, k],
        rhs=a[k, data_demand[j].I],
        sense=gp.GRB.LESS_EQUAL,
        name="con_demand_ready" + str(j) + str(k))
    for j in data_demand for k in range(num_f_train)}

con_demand_within_time = {(j, k):
    MIP.addLConstr(
        lhs=a[k, data_demand[j].E],
        rhs=num_T*(2-x[j, k]),
        sense=gp.GRB.LESS_EQUAL,
        name="con_demand_within_time" + str(j) + str(k))
    for j in data_demand for k in range(num_f_train)}

con_demand_load = {(k, s):
    MIP.addLConstr(
        lhs=gp.quicksum(data_demand[j].L*x[j, k] for j in set_demand_ori[s])+gp.quicksum(data_demand[j].L*x[j, k] for j in set_demand_des[s]),
        rhs=d[k, s]-a[k, s],
        sense=gp.GRB.LESS_EQUAL,
        name="con_demand_load" + str(k) + str(s))
    for k in range(num_f_train) for s in range(num_station)}

con_demand_waiting = {(k, s):
    MIP.addLConstr(
        lhs=d[k, s]-a[k, s],
        rhs=num_T*(gp.quicksum(x[j, k] for j in set_demand_ori[s])+gp.quicksum(x[j, k] for j in set_demand_des[s])),
        sense=gp.GRB.LESS_EQUAL,
        name="con_demand_waiting" + str(k) + str(s))
    for k in range(num_f_train) for s in range(num_station)}

con_demand_travel = {(k, s):
    MIP.addLConstr(
        lhs=a[k, s+1]-d[k, s],
        rhs=lower_travel[s],
        sense=gp.GRB.GREATER_EQUAL,
        name="con_demand_travel" + str(k) + str(s))
    for k in range(num_f_train) for s in range(num_station-1)}

con_demand_delay = {(j, k):
    MIP.addLConstr(
        lhs=sigma[j],
        rhs=a[k, data_demand[j].E]-data_demand[j].B-num_T*(1-x[j,k]),
        sense=gp.GRB.GREATER_EQUAL,
        name="con_demand_delay" + str(j) + str(k))
    for j in data_demand for k in range(num_f_train)}

con_demand_cargo_train = {(j, k):
    MIP.addLConstr(
        lhs=x[j, k],
        rhs=y[k],
        sense=gp.GRB.LESS_EQUAL,
        name="con_demand_cargo_train" + str(j) + str(k))
    for j in data_demand for k in range(num_f_train)}

con_passenger_station = {k:
    MIP.addLConstr(
        lhs=data_A[k][0]-data_D[k-1][0]+h[k]+h[k-1],
        rhs=lower_headway_station,
        sense=gp.GRB.GREATER_EQUAL,
        name="con_passenger_station" + str(k))
    for k in range(1, num_f_train)}

con_passenger_segment = {k:
    MIP.addLConstr(
        lhs=data_D[k][0]-data_D[k-1][0]+h[k]+h[k-1],
        rhs=lower_headway_segment,
        sense=gp.GRB.GREATER_EQUAL,
        name="con_passenger_segment" + str(k))
    for k in range(1, num_f_train)}

con_passenger_station_before = {(k, s):
    MIP.addLConstr(
        lhs=a[k, s]-data_D[k][s]-h[k],
        rhs=lower_headway_station-num_T*(1-y[k]),
        sense=gp.GRB.GREATER_EQUAL,
        name="con_passenger_station_before" + str(k))
    for k in range(num_f_train) for s in range(num_station)}

con_passenger_station_after = {(k, s):
    MIP.addLConstr(
        lhs=data_D[k+1][s]+h[k+1]-a[k, s],
        rhs=lower_headway_station-num_T*(1-y[k]),
        sense=gp.GRB.GREATER_EQUAL,
        name="con_passenger_station_after" + str(k))
    for k in range(num_f_train) for s in range(num_station)}

con_passenger_freight_segment_before = {(k, s):
    MIP.addLConstr(
        lhs=d[k, s]-data_D[k][s]-h[k],
        rhs=lower_headway_segment-num_T*(1-y[k]),
        sense=gp.GRB.GREATER_EQUAL,
        name="con_passenger_freight_segment_before" + str(k))
    for k in range(num_f_train) for s in range(num_station)}

con_passenger_freight_segment_after = {(k, s):
    MIP.addLConstr(
        lhs=data_D[k+1][s]+h[k+1]-d[k, s],
        rhs=lower_headway_segment-num_T*(1-y[k]),
        sense=gp.GRB.GREATER_EQUAL,
        name="con_passenger_freight_segment_after" + str(k))
    for k in range(num_f_train) for s in range(num_station)}
#
con_passenger_wait = {k:
    MIP.addLConstr(
        lhs=data_A[k][0]-data_D[k-1][0]+h[k]-h[k-1],
        rhs=upper_headway_passenger,
        sense=gp.GRB.LESS_EQUAL,
        name="con_passenger_segment" + str(k))
    for k in range(1, num_f_train)}
con_passenger_wait_before = {k:
    MIP.addLConstr(
        lhs=data_A[k][0]-data_D[k-1][0]+h[k]+h[k-1],
        rhs=lower_headway_passenger,
        sense=gp.GRB.GREATER_EQUAL,
        name="con_passenger_segment" + str(k))
    for k in range(1, num_f_train)}

con_passenger_define_xi = {(k, t):
    MIP.addLConstr(
        lhs=xi[k, t],
        rhs=xi[k, t-1],
        sense=gp.GRB.LESS_EQUAL,
        name="con_passenger_define_xi" + str(k))
    for k in range(num_p_train) for t in range(1, num_T)}

con_passenger_define_xi_2 = {k:
    MIP.addLConstr(
        lhs=data_D[k][0]+h[k],
        rhs=gp.quicksum((t-1)*(xi[k, t-1]-xi[k, t]) for t in range(1,num_T)),
        sense=gp.GRB.GREATER_EQUAL,
        name="con_passenger_define_xi" + str(k))
    for k in range(num_p_train)}

con_passenger_define_no_freight_overcrowded = {k:
    MIP.addLConstr(
        lhs=data_D[k][0]+h[k],
        rhs=gp.quicksum((t-1)*(xi[k, t-1]-xi[k, t]) for t in range(1,num_T))+num_T*(1-y[k]),
        sense=gp.GRB.LESS_EQUAL,
        name="con_passenger_define_xi" + str(k))
    for k in range(num_slot)}

con_demand_capacity_first = {s:
    MIP.addLConstr(
        lhs=capacity_p_train,
        rhs=gp.quicksum(data_passenger[s][t]*(1-xi[k, t]) for t in range(num_T)),
        sense=gp.GRB.GREATER_EQUAL,
        name="con_demand_travel" + str(k))
    for s in range(num_station)}

con_demand_capacity_later = {(k, s):
    MIP.addLConstr(
        lhs=capacity_p_train,
        rhs=gp.quicksum(data_passenger[s][t]*(xi[k-1, t]-xi[k, t]) for t in range(num_T)),
        sense=gp.GRB.GREATER_EQUAL,
        name="con_demand_travel" + str(k) + str(s))
    for k in range(1, num_f_train) for s in range(num_station)}

MIP.ModelSense = gp.GRB.MINIMIZE
# MIP.setParam('MIPFocus', 1)
MIP.setParam('TimeLimit', 7200)
# MIP.Params.OutputFlag = 0a
MIP.optimize()

if MIP.status != gp.GRB.Status.OPTIMAL:
    print('Optimization was stopped with status %d' % MIP.status)
    MIP.computeIIS()
    for c in MIP.getConstrs():
        if c.IISConstr:
            print('%s' % c.constrName)

time_end = datetime.datetime.now()

timetable_p = {}
for k in range(num_p_train):
    new_cycle = []
    for s in range(num_station):
        new_cycle.append(data_A[k][s]+h[k].x)
        new_cycle.append(data_D[k][s]+h[k].x)
    timetable_p[k] = new_cycle
timetable_f = {}
for k in range(num_f_train):
    new_cycle = []
    if y[k].x > 0.99:
        for s in range(num_station):
            new_cycle.append(a[k, s].x)
            new_cycle.append(d[k, s].x)
        timetable_f[k] = new_cycle
x_var = [[x[j, k].x for k in range(num_f_train)]for j in data_demand]
y_var = [y[k].x for k in range(num_f_train)]
xi_var = [[xi[k,t].x for t in range(num_T)]for k in range(num_p_train)]
sigma_var = [sigma[j].x for j in data_demand]
print('x_var', 'sigma_var')
for j in data_demand:
    print(j, x_var[j], sigma_var[j])
print('y_var')
print(y_var)

print('Optimal solution value', MIP.ObjVal)
print('CPU time', time_end-time_start)
yizhuang_timetable(timetable_p, timetable_f)

print('complete')
