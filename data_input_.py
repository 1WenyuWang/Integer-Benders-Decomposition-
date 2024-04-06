# 50,60,70,80,90,100,110,120,130,140,150
num_demand = 100

# 30,40,50,60,70,80,90,100
capacity_station = 100

# 0,1,2,3,4,5,6,7,8,9,10
num_shift = 10

num_real_station = 13
num_station = num_real_station * 2
num_p_train = 21
num_slot = num_p_train - 1
num_f_train = 20
# num_demand=20
num_T = 480
cost_service = 1
capacity_f_train = 100
capacity_p_train = 1350

upper_shift = [num_shift for i in range(num_p_train - 2)]
upper_shift.insert(0, 0)
upper_shift.append(0)
lower_shift = [-num_shift for i in range(num_p_train - 2)]
lower_shift.insert(0, 0)
lower_shift.append(0)
lower_travel = [4 for s in range(num_station - 1)]
lower_headway_station = 2
lower_headway_segment = 2
lower_headway_passenger = 12
upper_headway_passenger = 16


class demand():
    def __init__(self):
        self.index = 0
        self.I = 0
        self.E = 0
        self.R = 0
        self.B = 0
        self.P = 0
        self.L = 0.0
        self.pd = 0.0
        self.pn = 0.0
        self.psi = 0.0


print('data_input_start')
data_demand = {}
sheet_demand = excelrd.open_workbook('example.xlsx').sheet_by_name('demand')
for l in range(1, num_demand + 1):
    tem_demand = demand()
    tem_demand.index = int(sheet_demand.cell_value(l, 0))
    tem_demand.I = int(sheet_demand.cell_value(l, 1))
    tem_demand.E = int(sheet_demand.cell_value(l, 2))
    tem_demand.R = int(sheet_demand.cell_value(l, 3))
    tem_demand.B = int(sheet_demand.cell_value(l, 4))
    tem_demand.P = float(sheet_demand.cell_value(l, 5))
    tem_demand.L = int(sheet_demand.cell_value(l, 6))
    tem_demand.pd = float(sheet_demand.cell_value(l, 7))
    tem_demand.pn = float(sheet_demand.cell_value(l, 8))
    tem_demand.psi = float(sheet_demand.cell_value(l, 9))
    data_demand[tem_demand.index] = tem_demand

data_passenger = [[0 for t in range(num_T)] for i in range(num_station)]
sheet_passenger = excelrd.open_workbook('example.xlsx').sheet_by_name('passenger')
for i in range(num_station):
    for t in range(num_T):
        data_passenger[i][t] = int(sheet_passenger.cell_value(i + 1, t + 1))

data_A = [[0 for i in range(num_station)] for k in range(num_p_train)]
data_D = [[0 for i in range(num_station)] for k in range(num_p_train)]
sheet_A = excelrd.open_workbook('example.xlsx').sheet_by_name('A')
for i in range(num_station):
    for k in range(num_p_train):
        data_A[k][i] = int(sheet_A.cell_value(i + 1, k + 1))
        data_D[k][i] = data_A[k][i] + 1
print('data_input_complete')

set_demand_tra = {s: [] for s in range(num_station)}
for s in range(num_station):
    for j in data_demand:
        if data_demand[j].I <= s and data_demand[j].E > s:
            set_demand_tra[s].append(j)

set_demand_ori = {s: [] for s in range(num_station)}
for s in range(num_station):
    for j in data_demand:
        if data_demand[j].I == s:
            set_demand_ori[s].append(j)

set_demand_des = {s: [] for s in range(num_station)}
for s in range(num_station):
    for j in data_demand:
        if data_demand[j].E == s:
            set_demand_ori[s].append(j)


def subproblem(y):
    SP = gp.Model('SP')
    x = {(j, k): SP.addVar(vtype=gp.GRB.BINARY, name='x'.format(j, k), lb=0) for j in range(num_demand) for k in
         range(num_f_train)}
    sigma = {j: SP.addVar(vtype=gp.GRB.CONTINUOUS, name='chi'.format(j), lb=0) for j in range(num_demand)}
    a = {(k, s): SP.addVar(vtype=gp.GRB.INTEGER, name='a'.format(k, s), lb=0) for k in range(num_f_train) for s in
         range(num_station)}
    d = {(k, s): SP.addVar(vtype=gp.GRB.INTEGER, name='d'.format(k, s), lb=0) for k in range(num_f_train) for s in
         range(num_station)}
    h = {k: SP.addVar(vtype=gp.GRB.INTEGER, name='h'.format(k), lb=lower_shift[k], ub=upper_shift[k]) for k in
         range(num_p_train)}
    z = {(j, jj): SP.addVar(vtype=gp.GRB.BINARY, name='z'.format(j, j), lb=0) for j in range(num_demand) for jj in
         range(num_demand)}
    xi = {(k, t): SP.addVar(vtype=gp.GRB.BINARY, name='xi'.format(k, t), lb=0) for k in range(num_p_train) for t in
          range(num_T)}

    # objective function
    expr = gp.LinExpr()
    for j in data_demand:
        expr += data_demand[j].pd * sigma[j]
        expr += data_demand[j].pn
        for k in range(num_f_train):
            expr -= data_demand[j].pn * x[j, k]
    # for k in range(num_f_train):
    #     expr += cost_service * y[k]
    SP.setObjective(expr)

    # constraints
    con_demand_unique = {(j, s):
        SP.addLConstr(
            lhs=gp.quicksum(x[j, k] for k in range(num_f_train)),
            rhs=1,
            sense=gp.GRB.LESS_EQUAL,
            name="con_demand_unique" + "_" + str(j) + "_" + str(s))
        for j in data_demand for s in range(num_station)}

    con_demand_capacity = {(k, s):
        SP.addLConstr(
            lhs=gp.quicksum(data_demand[j].P * x[j, k] for j in set_demand_tra[s]),
            rhs=capacity_f_train,
            sense=gp.GRB.LESS_EQUAL,
            name="con_demand_capacity" + "_" + str(k) + "_" + str(s))
        for k in range(num_f_train) for s in range(num_station)}

    con_demand_platform_capacity = {j:
        SP.addLConstr(
            lhs=data_demand[j].P + gp.quicksum(data_demand[j].P * z[j, jj] for jj in set_demand_ori[data_demand[j].I]),
            rhs=capacity_station,
            sense=gp.GRB.LESS_EQUAL,
            name="con_demand_platform_capacity" + "_" + str(j))
        for j in data_demand}

    con_demand_define_z = {(j, jj, k):
        SP.addLConstr(
            lhs=a[k, data_demand[j].I],
            rhs=data_demand[j].R + num_T * (1 - x[jj, k] + z[jj, j]),
            sense=gp.GRB.LESS_EQUAL,
            name="con_demand_define_z" + "_" + str(j) + "_" + str(jj) + "_" + str(k))
        for j in data_demand for jj in set_demand_ori[data_demand[j].I] for k in range(num_f_train)}

    con_demand_ready = {(j, k):
        SP.addLConstr(
            lhs=data_demand[j].R * x[j, k],
            rhs=a[k, data_demand[j].I],
            sense=gp.GRB.LESS_EQUAL,
            name="con_demand_ready" + "_" + str(j) + "_" + str(k))
        for j in data_demand for k in range(num_f_train)}

    con_demand_within_time = {(j, k):
        SP.addLConstr(
            lhs=a[k, data_demand[j].E],
            rhs=num_T * (2 - x[j, k]),
            sense=gp.GRB.LESS_EQUAL,
            name="con_demand_within_time" + "_" + str(j) + "_" + str(k))
        for j in data_demand for k in range(num_f_train)}

    con_demand_load = {(k, s):
        SP.addLConstr(
            lhs=gp.quicksum(data_demand[j].L * x[j, k] for j in set_demand_ori[s]) + gp.quicksum(
                data_demand[j].L * x[j, k] for j in set_demand_des[s]),
            rhs=d[k, s] - a[k, s],
            sense=gp.GRB.LESS_EQUAL,
            name="con_demand_load" + "_" + str(k) + "_" + str(s))
        for k in range(num_f_train) for s in range(num_station)}

    con_demand_waiting = {(k, s):
        SP.addLConstr(
            lhs=d[k, s] - a[k, s],
            rhs=num_T * (gp.quicksum(x[j, k] for j in set_demand_ori[s]) + gp.quicksum(
                x[j, k] for j in set_demand_des[s])),
            sense=gp.GRB.LESS_EQUAL,
            name="con_demand_waiting" + "_" + str(k) + "_" + str(s))
        for k in range(num_f_train) for s in range(num_station)}

    con_demand_travel = {(k, s):
        SP.addLConstr(
            lhs=a[k, s + 1] - d[k, s],
            rhs=lower_travel[s],
            sense=gp.GRB.GREATER_EQUAL,
            name="con_demand_travel" + "_" + str(k) + "_" + str(s))
        for k in range(num_f_train) for s in range(num_station - 1)}

    con_demand_delay = {(j, k):
        SP.addLConstr(
            lhs=sigma[j],
            rhs=a[k, data_demand[j].E] - data_demand[j].B - num_T * (1 - x[j, k]),
            sense=gp.GRB.GREATER_EQUAL,
            name="con_demand_delay" + "_" + str(j) + "_" + str(k))
        for j in data_demand for k in range(num_f_train)}

    con_demand_cargo_train = {(j, k):
        SP.addLConstr(
            lhs=x[j, k],
            rhs=y[k],
            sense=gp.GRB.LESS_EQUAL,
            name="con_demand_cargo_train" + "_" + str(j) + "_" + str(k))
        for j in data_demand for k in range(num_f_train)}

    # con_freight_shift_range在变量定义中已经实现

    con_passenger_station = {k:
        SP.addLConstr(
            lhs=data_A[k][0] - data_D[k - 1][0] + h[k] + h[k - 1],
            rhs=lower_headway_station,
            sense=gp.GRB.GREATER_EQUAL,
            name="con_passenger_station" + "_" + str(k))
        for k in range(1, num_f_train)}

    con_passenger_segment = {k:
        SP.addLConstr(
            lhs=data_D[k][0] - data_D[k - 1][0] + h[k] + h[k - 1],
            rhs=lower_headway_segment,
            sense=gp.GRB.GREATER_EQUAL,
            name="con_passenger_segment" + "_" + str(k))
        for k in range(1, num_f_train)}

    con_passenger_station_before = {(k, s):
        SP.addLConstr(
            lhs=a[k, s] - h[k],
            rhs=lower_headway_station - num_T * (1 - y[k]) + data_D[k][s],
            sense=gp.GRB.GREATER_EQUAL,
            name="con_passenger_station_before" + "_" + str(k) + "_" + str(s))
        for k in range(num_f_train) for s in range(num_station)}

    con_passenger_station_after = {(k, s):
        SP.addLConstr(
            lhs=h[k + 1] - a[k, s],
            rhs=lower_headway_station - num_T * (1 - y[k]) - data_D[k + 1][s],
            sense=gp.GRB.GREATER_EQUAL,
            name="con_passenger_station_after" + "_" + str(k) + "_" + str(s))
        for k in range(num_f_train) for s in range(num_station)}

    con_passenger_freight_segment_before = {(k, s):
        SP.addLConstr(
            lhs=d[k, s] - h[k],
            rhs=lower_headway_segment - num_T * (1 - y[k]) + data_D[k][s],
            sense=gp.GRB.GREATER_EQUAL,
            name="con_passenger_freight_segment_before" + "_" + str(k) + "_" + str(s))
        for k in range(num_f_train) for s in range(num_station)}

    con_passenger_freight_segment_after = {(k, s):
        SP.addLConstr(
            lhs=h[k + 1] - d[k, s],
            rhs=lower_headway_segment - num_T * (1 - y[k]) - data_D[k + 1][s],
            sense=gp.GRB.GREATER_EQUAL,
            name="con_passenger_freight_segment_after" + "_" + str(k) + "_" + str(s))
        for k in range(num_f_train) for s in range(num_station)}
    #
    con_passenger_wait = {k:
        SP.addLConstr(
            lhs=data_A[k][0] - data_D[k - 1][0] + h[k] - h[k - 1],
            rhs=upper_headway_passenger,
            sense=gp.GRB.LESS_EQUAL,
            name="con_passenger_wait" + "_" + str(k))
        for k in range(1, num_f_train)}
    con_passenger_wait_before = {k:
        SP.addLConstr(
            lhs=data_A[k][0] - data_D[k - 1][0] + h[k] + h[k - 1],
            rhs=lower_headway_passenger,
            sense=gp.GRB.GREATER_EQUAL,
            name="con_passenger_wait_before" + "_" + str(k))
        for k in range(1, num_f_train)}

    ###########about xi

    con_passenger_define_xi = {(k, t):
        SP.addLConstr(
            lhs=xi[k, t],
            rhs=xi[k, t - 1],
            sense=gp.GRB.LESS_EQUAL,
            name="con_passenger_define_xi" + "_" + str(k) + "_" + str(t))
        for k in range(num_p_train) for t in range(1, num_T)}

    con_passenger_define_xi_2 = {k:
        SP.addLConstr(
            lhs=data_D[k][0] + h[k],
            rhs=gp.quicksum((t - 1) * (xi[k, t - 1] - xi[k, t]) for t in range(1, num_T)),
            sense=gp.GRB.GREATER_EQUAL,
            name="con_passenger_define_xi_2" + "_" + str(k))
        for k in range(num_p_train)}

    con_passenger_define_no_freight_overcrowded = {k:
        SP.addLConstr(
            lhs=h[k] - gp.quicksum((t - 1) * (xi[k, t - 1] - xi[k, t]) for t in range(1, num_T)),
            rhs=num_T * (1 - y[k]) - data_D[k][0],
            sense=gp.GRB.LESS_EQUAL,
            name="con_passenger_define_no_freight_overcrowded" + "_" + str(k))
        for k in range(num_slot)}

    con_demand_capacity_first = {s:
        SP.addLConstr(
            lhs=capacity_p_train,
            rhs=gp.quicksum(data_passenger[s][t] * (1 - xi[k, t]) for t in range(num_T)),
            sense=gp.GRB.GREATER_EQUAL,
            name="con_demand_capacity_first" + "_" + str(k))
        for s in range(num_station)}

    con_demand_capacity_later = {(k, s):
        SP.addLConstr(
            lhs=capacity_p_train,
            rhs=gp.quicksum(data_passenger[s][t] * (xi[k - 1, t] - xi[k, t]) for t in range(num_T)),
            sense=gp.GRB.GREATER_EQUAL,
            name="con_demand_capacity_later" + "_" + str(k) + "_" + str(s))
        for k in range(1, num_f_train) for s in range(num_station)}

    SP.ModelSense = gp.GRB.MINIMIZE
    SP.update()

    return SP, con_demand_cargo_train, con_passenger_station_before, con_passenger_station_after, con_passenger_freight_segment_before, con_passenger_freight_segment_after, con_passenger_define_no_freight_overcrowded


def subproblem_update(y, SP):
    for j in data_demand:
        for k in range(num_f_train):
            SP.getConstrByName("con_demand_cargo_train" + "_" + str(j) + "_" + str(k)).setAttr('RHS', y[k])
    for k in range(num_f_train):
        for s in range(num_station):
            SP.getConstrByName("con_passenger_station_before" + "_" + str(k) + "_" + str(s)).setAttr('RHS',
                                                                                                     lower_headway_station - num_T * (
                                                                                                             1 - y[
                                                                                                         k]) +
                                                                                                     data_D[k][s])
    for k in range(num_f_train):
        for s in range(num_station):
            SP.getConstrByName("con_passenger_station_after" + "_" + str(k) + "_" + str(s)).setAttr('RHS',
                                                                                                    lower_headway_station - num_T * (
                                                                                                            1 - y[
                                                                                                        k]) -
                                                                                                    data_D[k + 1][s])
    for k in range(num_f_train):
        for s in range(num_station):
            SP.getConstrByName("con_passenger_freight_segment_before" + "_" + str(k) + "_" + str(s)).setAttr('RHS',
                                                                                                             lower_headway_segment - num_T * (
                                                                                                                     1 -
                                                                                                                     y[
                                                                                                                         k]) +
                                                                                                             data_D[k][
                                                                                                                 s])
    for k in range(num_f_train):
        for s in range(num_station):
            SP.getConstrByName("con_passenger_freight_segment_after" + "_" + str(k) + "_" + str(s)).setAttr('RHS',
                                                                                                            lower_headway_segment - num_T * (
                                                                                                                    1 -
                                                                                                                    y[
                                                                                                                        k]) -
                                                                                                            data_D[
                                                                                                                k + 1][
                                                                                                                s])
    for k in range(num_slot):
        SP.getConstrByName("con_passenger_define_no_freight_overcrowded" + "_" + str(k)).setAttr('RHS',
                                                                                                 num_T * (1 - y[k]) -
                                                                                                 data_D[k][0])

    SP.update()
    return SP
