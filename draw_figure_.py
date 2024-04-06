from data_input import num_T, num_real_station
from matplotlib import pyplot as plt


def yizhuang_timetable(timetable_p, timetable_f):
    plt.figure(figsize=(10, 5))
    plt.yticks([i for i in range(num_real_station)],
               ['次渠', '次渠南', '经海路', '同济南路', '荣昌东街', '荣京东街', '万源街', '亦庄文化园', '亦庄桥',
                '旧宫', '小红门', '肖村', '宋家庄'])
    plt.xticks([0, 60, 120, 180, 240, 300, 360, 420, 480],
               ['10:00', '10:30', '11:00', '11:30', '12:00', '12:30', '13:00', '13:30', '14:00'])
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.xlabel("时间")
    plt.ylabel("车站")
    plt.xlim([0, num_T])
    plt.ylim([0, num_real_station - 1])
    cycle = []
    for i in range(num_real_station):
        cycle.append(i)
        cycle.append(i)
    for i in range(num_real_station):
        cycle.append(num_real_station - i - 1)
        cycle.append(num_real_station - i - 1)
    for i in timetable_p:
        plt.plot(timetable_p[i], cycle, color="k")
    for i in timetable_f:
        plt.plot(timetable_f[i], cycle, color="r")
    plt.show()
