import copy

from numpy import real, fromfile, single, cumsum, histogram
from numpy.fft import fft, ifft
from scipy import interpolate
from VBCDatGenerators import path_verify


def vbc_data_read(path, file, i_speed_switch=None, i_concerned=None):
    # 支持多档多指标同时输出
    # data_to_return = [[[速度1concern1], [速度1concern2], ...], [[速度2concern1], [速度2concern2], ...], ...]
    filename = path_verify(path) + file
    fid = open(filename, 'rb')
    fid.read(4)
    data = list(fromfile(file=filename, dtype=single, count=-1))
    fid.close()
    speed_count = int(data[0])
    dt_list = []  # 存储每个速度档的结果的dt
    nt_list = []  # 存储每个速度档的时间步数
    nd_list = []  # 存储每个速度档的每个dt的数据
    data_list = []  # 存储每个速度档的计算结果数据（按速度档分好；不含dt等数据；未进行每个响应指标的分离，依然是按时间&手册上的响应顺序排列）
    i_dt_idx = 1  # 定位用：每个速度档位的dt信息的所在index

    if not i_speed_switch:
        i_speed_switch = range(1, speed_count+1)
    if type(i_speed_switch) == float:
        i_speed_switch = int(i_speed_switch)
    if type(i_speed_switch) == int:
        i_speed_switch = [i_speed_switch]
    if max(i_speed_switch) > speed_count or min(i_speed_switch) < 1:
        return -1

    speed_count_for_loop = min(max(i_speed_switch), speed_count)

    for i_speed in range(0, speed_count_for_loop):
        i_dt = data[i_dt_idx]
        i_nt = int(data[i_dt_idx+1])
        i_nd = int(data[i_dt_idx+2])
        i_data_idx_start = i_dt_idx + 3 + 2*i_nd
        i_data_idx_end = i_data_idx_start + i_nd*i_nt - 1
        i_data = data[i_data_idx_start:i_data_idx_end+1]
        dt_list.append(i_dt)
        nt_list.append(i_nt)
        nd_list.append(i_nd)
        data_list.append(i_data)
        i_dt_idx = (i_data_idx_end + 1)

    data_list_to_return_temp = [data_list[i-1] for i in i_speed_switch]

    if not i_concerned:  # 暂时只考虑各速度档的Nd、dt等均相同
        i_concerned = range(1, nd_list[0]+1)
    if type(i_concerned) == float:
        i_concerned = int(i_concerned)
    if type(i_concerned) == int:
        i_concerned = [i_concerned]
    if max(i_concerned) > nd_list[0] or min(i_concerned) < 1:
        return -1

    data_list_to_return = []  # 暂时只考虑各速度档的Nd、dt等均相同
    for j_speed_data in data_list_to_return_temp:
        j_data_to_return = [j_speed_data[i-1:-1:nd_list[0]] for i in i_concerned]
        data_list_to_return.append(j_data_to_return)

    return data_list_to_return, dt_list[0], speed_count


def moving_average(y_raw, dt, speed, window_length):
    window_time_width = window_length/(speed/3.6)
    data_num_in_window = int(round(window_time_width/dt))
    if data_num_in_window % 2 == 0:
        data_num_in_window -= 1
    if len(y_raw) <= data_num_in_window:
        return -1
    smooth_start = int((data_num_in_window-1)/2)
    smooth_end = int(len(y_raw) - (data_num_in_window - 1) / 2)  # 这个end是直接用于range的，实际取不到，只能取到这个end-1
    half_window_width = (data_num_in_window-1)/2  # 除了中心点以外的半窗宽度
    y = copy.deepcopy(y_raw)
    for i_data in range(smooth_start, smooth_end):
        i_window_left = int(i_data-half_window_width)
        i_window_right = int(i_data+half_window_width+1)
        y[i_data] = sum(y_raw[i_window_left:i_window_right]) / data_num_in_window
    return y


def vbc_filter(y_raw, fn, dt):
    if fn[0] > fn[1]:
        fn[0], fn[1] = fn[1], fn[0]
    fs = 1.0/dt
    wn = [i/(fs/2.0) for i in fn]
    if wn[1] <= 1 and wn[0] >= 0:
        n1 = len(y_raw)
        n2 = round(n1/2.0)
        n_keep = [round(i*n2) for i in wn]

        x2 = fft(y_raw)
        x2[(n_keep[1]-1):(n1-n_keep[1]-1)] = 0

        if n_keep[0] >= 1:
            x2[0:(n_keep[0]-1)] = 0
            x2[(n1-n_keep[0]-1):(n1-1)] = 0

        y = ifft(x2)
        y = list(real(y))
        return y


def fft_for_plot(x, dt):
    # 仅返回作图用数据，不作图；仅支持一组输入信号x
    fs = 1.0/dt
    n1 = len(x)
    n2 = round(n1/2.0)
    f = [i/(n1+1)*fs for i in range(0, n2)]
    af = fft(x)
    af = af[0:n2]
    af = list(abs(af)/n2*2.0)
    return f, af


def get_data_from_cdf(signal, target_point):
    hist, bin_edges = histogram(signal, min(len(signal), 10000))  # 一般都要求取到的位置精度也就在0.01%，所以cdf数据点能到10000个的话就足够精准定位了
    cdf_y_axis = cumsum(hist)
    # cdf_x_axis = bin_edges[1:]
    # print(max(cdf_y_axis))
    idx_of_target_data = int(target_point * max(cdf_y_axis))
    signal.sort()
    target_data = signal[idx_of_target_data]

    return target_data


def get_data_for_table(y_raw, method, dt=None, freq_range=None, speed=None, abs_for_max = True):
    # 输入原始数据时程，根据method参数进行处理（直接取最大值or滤波后取最大值or取统计值）
    if method == 'filt_max':
        y_1 = vbc_filter(y_raw=y_raw, fn=freq_range, dt=dt)
    elif method == 'GB5599-2019':
        pt_count_raw = len(y_raw)
        if pt_count_raw < 10000:
            x_raw = [dt*i for i in range(0, pt_count_raw)]
            y_func = interpolate.interp1d(x_raw, y_raw, kind='linear')
            # 确定插值后的数据点位置及相应的dt
            n_interp = 0  # 在原先相邻数据点之间插n个点(采用这种复杂算法是为了保证保留原数据的尖点)
            pt_count = pt_count_raw
            dt_0 = dt
            while pt_count < 10000:
                n_interp += 1
                pt_count = pt_count_raw + n_interp*(pt_count_raw-1)
                dt_0 = dt/(n_interp+1)
            x_0 = [dt_0*i for i in range(0, pt_count)]
            y_0 = y_func(x_0)
        else:
            y_0 = y_raw
            dt_0 = dt
        y_1 = moving_average(y_raw=y_0, dt=dt_0, speed=speed, window_length=2.0)
    else:
        y_1 = y_raw

    if method == 'GB5599-2019':
        y_2 = get_data_from_cdf(signal=y_1, target_point=0.9975)
    else:
        if abs_for_max:
            y_2 = max([abs(i) for i in y_1])
        else:
            y_2 = max(y_1)
    return y_2


def sperling(x, if_vertical, dt):
    x = [i*100.0 for i in x]  # 转换单位
    Wz = 0

    N = len(x)
    x_abs = [abs(i) for i in x]
    maxvacc = max(x)

    i = 0
    while (x[i] < maxvacc*0.2) and (i < N - 1):
        i += 1
    istart = i

    i = N - 1
    while (x[i] > maxvacc*0.2) and (i > 0):
        i -= 1
    iend = i

    Neffect = iend - istart + 1
    x = x[istart:iend+1]
    N = Neffect

    N2 = round(N/2)
    K = range(0, N2)
    F = [i/(N+1)*(1/dt) for i in K]
    AF = fft(x)
    AF = AF[0:N2]
    AF = [abs(i)/Neffect*2.0 for i in AF]

    for LOC in range(1, round(50.0*(N+1)*dt)):
        A = AF[LOC]
        F0 = LOC/(N+1)*(1/dt)
        # 频率修正系数
        if if_vertical:
            if (F0 > 0.5) and (F0 <= 5.9):
                Ff = 0.325*F0*F0
            elif (F0 > 5.9) and (F0 <= 20):
                Ff = 400/F0/F0
            elif F0 > 20:
                Ff = 1
            else:
                Ff = 0
        else:
            if (F0 > 0.5) and (F0 <= 5.4):
                Ff = 0.8*F0*F0
            elif (F0 > 5.4) and (F0 <= 26):
                Ff = 650/F0/F0
            else:
                Ff = 0

        Wztemp = A**3 * Ff/F0
        Wz += Wztemp
    Wz = Wz**0.1 * 0.896
    return Wz


if __name__ == '__main__':
    data, dt = vbc_data_read('D:\\Nanpanjiang Bridge\\VBC\\con001', 'Res_BridgeResponseBulkDate_disacc.bin', 1, 3)
    # print(data[0])
