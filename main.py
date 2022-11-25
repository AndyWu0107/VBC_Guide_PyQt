import numpy as np

from VBCDatGenerators import VehOrg, Irregularity, RailsLoc, SolPara, SubBri, NonSpring, SubVeh, WindCoe
import PyQt5

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # VehMatrix = [[1, 2], [3, 4, 4, 3], [5, 6, 7]]
    # # print(VehMatrix)
    # OrgMatrix = [[[1, 1],  # 车队号、车道号
    #               [200, 0, 0, 0, 0],
    #               [250, 0, 0, 0, 0],
    #               [300, 0, 0, 0, 0],
    #               [350, 0, 0, 0, 0],
    #               [400, 0, 0, 0, 0],
    #               [420, 0, 0, 0, 0]],
    #              [[1, 2],
    #               [200, 0, 0, 0, 0],
    #               [250, 0, 0, 0, 0],
    #               [300, 0, 0, 0, 0],
    #               [350, 0, 0, 0, 0],
    #               [400, 0, 0, 0, 0],
    #               [420, 0, 0, 0, 0]],
    #              ]
    # # print(OrgMatrix[1, :, :])
    # vo = VehOrg()
    # vo.define(VehMatrix, OrgMatrix)
    # vo.write_dat('.\\')

    # irr = Irregularity(spectrum_level=7, random_seed=1, wave_length_min=2, wave_length_max=80, sample_length=4096,
    #                    interval=0.5, wave_length_filter=0, sample_source=1, smooth_distance=50, ratio1=1, ratio2=1,
    #                    ratio3=1)
    # irr.write_dat()

    # Rail1 = [[45, -9.591, 2.5, 0, 0, 45, 0],
    #          [200, -9.591, 2.5, 0, 0, 200, 0],
    #          [344, -9.591, 2.5, 0, 0, 344, 0],
    #          [348, -9.591, 2.5, 0, 0, 348, 0],
    #          [352, -9.591, 2.5, 0, 0, 348, 0],
    #          [358, -9.591, 2.5, 0, 0, 348, 0]
    #          ]
    # Rail2 = [[45, -9.591, -2.5, 0, 0, 45, 0],
    #          [200, -9.591, -2.5, 0, 0, 200, 0],
    #          [344, -9.591, -2.5, 0, 0, 344, 0],
    #          [348, -9.591, -2.5, 0, 0, 348, 0],
    #          [352, -9.591, -2.5, 0, 0, 348, 0],
    #          [358, -9.591, -2.5, 0, 0, 348, 0]
    #          ]
    # Rail3 = [[45, 9.591, 0, 0, 0, 45, 0],
    #          [1235, 9.591, 0, 0, 0, 1235, 0]
    #          ]
    # RailMatrix = [Rail1, Rail2, Rail3]
    # # print(len(RailMatrix[2]))
    # rails_loc = RailsLoc(rail_matrix=RailMatrix, interpolation_interval=0.05, interpolation_method=0,
    #                      consider_vertical_curve=0)
    # rails_loc.write_dat()
    # SolPara(integral_method=4, dt_integration=0.5e-3, iter_num=2, iter_tol=0.1e-2, step_num_each_output=2,
    #         w_r_contact_opt=1, bridge_coord_opt=1, fem_software_opt=1, rail_elastic_opt=1, rail_vertical_stiff=0.75e8,
    #         rail_vertical_damp=0.9e5, track_width=1.5).write_dat()

    # id_rail_nodes = [6141, 6142, 6143, 6110, 6111, 6112, 6144, 6145, 6149, 6148, 6146, 6147, 6140]
    # post_nodes = [[6131, 'a'], [6132, 'b'], [6133, 'c'], [6111, 'd'], [6112, 'e'], [6110, 'f'],
    #               [6134, 'g'], [6135, 'h'], [6139, 'i'], [6138, 'j'], [6136, 'k'], [6137, 'l'], [6130, 'm']]
    # mode_files_path = ["D:\\西沱江大桥", "D:\\西沱江小桥"]
    # mode_files_name = ["daqiaomode.dat", "xiaoqiaomode.dat"]
    #
    # sb = SubBri()
    # sb.define(nodes_info_source='midas', nodes_info_sourcefile='成达万高铁资阳西沱江大桥MODAL2.mct',
    #           id_rail_nodes=id_rail_nodes, post_nodes=post_nodes,
    #           nonlinear_springs=[[6141, 6142, 0, 3], [6143, 6144, 0, 3]], sync_output_dofs=[[6131, 2], [6131, 4]],
    #           bri_rail_mode_num=500, excluded_modes=[401, 500],
    #           mode_files_path=mode_files_path, mode_files_name=mode_files_name,
    #           modes_in_each_file=[300, 200], damps_in_each_file=[[2, 2, 0.05, 0.05], [402, 402, 0.05, 0.05]])
    # sb.write_dat('.\\')

    # sb = SubBri()
    # sb.read_dat('.\\')
    # # print(sb.__dict__)
    # # print(sb.num_post_nodes)
    # print(sb.name_post_nodes)
    # sb.write_dat(compute_stage=2)
    #
    # vo = VehOrg()
    # vo.read_dat('D:\\')
    # print(vo.train_name_vec)
    #
    # rl = RailsLoc()
    # rl.read_dat('D:\\Xituojiang Bridge\\VBC\\con318')
    # print(rl.track_width_name_vec)

    # sp = SolPara()
    # sp.read_dat('D:\\Xituojiang Bridge\\VBC\\con318')

    # non_spring_class_dict = {0: ['无', None, []],
    #                          1: ['线性弹簧阻尼', 1, ['线弹性刚度K', '粘滞阻尼系数C']],
    #                          2: ['双线性粘滞阻尼', 2, ['阻尼力F1', '卸荷速度V1', '阻尼力F2', '卸荷速度V2']],
    #                          3: ['扣件非线性弹性', 3, ['压刚度', '拉刚度', '临界位移', '阻尼系数/刚度']],
    #                          4: ['线性弹簧+指数形式粘滞阻尼', 4, ['K', 'C', 'alf']],
    #                          5: ['三次非线性', 5, ['非线性系数cs']],
    #                          6: ['库伦摩擦阻尼', 6, ['阻力F0']],
    #                          7: ['双线性弹簧', 100, ['初始刚度K0', '屈服后刚度KU', '屈服荷载FU']]}
    # ns = NonSpring(non_spring_class_dict)
    # # non_spring_list = [[[1, 5, 8], [0], [0], [3, 30.0, 0.0, 0.0], [0], [0]],
    # #                    [[0], [2, 4.0, 5.0e3], [3, 30.0, 0.0, 0.0], [4, 9.0e5], [0], [0]]]
    # # ns.define(non_spring_list)
    # # ns.write_dat()
    # ns.read_dat('D:\\板轨分开建模')
    # print(ns.non_spring_id_in_dat)

    # non_spring_class_dict = {0: ['线性', []],
    #                               1: ['线性阻尼', ['线弹性刚度', '粘滞阻尼系数']],
    #                               2: ['抗蛇行减振器', ['饱和力', '卸荷速度']],
    #                               3: ['双线性弹簧', ['初始刚度', '屈服后刚度', '屈服荷载']],
    #                               4: ['三次抛物线刚度', ['刚度系数']],
    #                               5: ['库伦摩擦阻尼', ['摩擦力']]}
    # ns = NonSpring(non_spring_class_dict)
    # non_spring_list = [[[1, 1.0, 2.0], [0], [0], [0], [0], [0]]]
    # non_spring_name_vec = ['新弹簧/阻尼单元']
    # ns.define(non_spring_list, non_spring_name_vec)
    # ns.write_dat('D:\\板轨分开建模')

    # veh = SubVeh()
    # veh.read_dat('C:\\Users\\Andy_\\Desktop\\vbc3.3.8')
    # print(veh.vehicle_type_dict)
    # print(len(veh.vehicle_type_dict))

    wind_coe = WindCoe()
    air_dens = 1.25
    ave_wind_speed = 30
    wind_direction_in_rad = 3.1415926
    wind_field_start_x = 15
    consider_fluctuating = 1
    roughness = 0.01
    reference_altitude = 10
    deck_altitude = 60
    space_pt_num = 50
    space_length = 200
    max_freq = 15
    random_seed = 2
    last_time = 60
    smooth_dist = 15
    smooth_time = 2.0
    wind_coe_dict_bri = {'桥面板风荷载-风洞结果1': [[1.0, 2.0, 1.0], [1.0], [0], [0], [0, 6], [0], [0]],
                         '桥面板风荷载-风洞结果2': [[1.0, 2.0, 1.0], [1.0], [0], [0], [0, 7], [0], [0]]}
    wind_node_group_dict = {'钢箱梁': [1, 5, 20, 60, 70, 80, 101],
                            '桥塔': [11, 15, 120, 160, 170, 180, 1101, 1201]}
    wind_load_assign_list_bri = ['桥面板风荷载-风洞结果1', '桥面板风荷载-风洞结果2']
    wind_coe_dict_veh = {'CRH3拖车迎风侧': [[4.0, 2.0, 5.0], [1.0], [0, 2], [0], [0, 8], [0], [0]],
                         'CRH3动车迎风侧': [[4.0, 2.0, 5.0], [3.0], [0, 2], [0], [0, 8], [0], [0]]}
    wind_field_ctrl_pt = [10, 15, 30, 45]
    wind_load_assign_list_veh = [[['CRH3拖车迎风侧', 'CRH3拖车迎风侧', 'CRH3拖车迎风侧', 'CRH3拖车迎风侧'],
                                  ['CRH3动车迎风侧', 'CRH3动车迎风侧', '无风荷载', 'CRH3动车迎风侧'],
                                  ['CRH3拖车迎风侧', 'CRH3拖车迎风侧', 'CRH3拖车迎风侧', 'CRH3拖车迎风侧'],
                                  ['CRH3拖车迎风侧', '无风荷载', 'CRH3拖车迎风侧', 'CRH3拖车迎风侧']],
                                 [['CRH3拖车迎风侧', 'CRH3拖车迎风侧', 'CRH3拖车迎风侧', 'CRH3拖车迎风侧'],
                                  ['CRH3动车迎风侧', 'CRH3动车迎风侧', '无风荷载', 'CRH3动车迎风侧'],
                                  ['CRH3拖车迎风侧', 'CRH3拖车迎风侧', 'CRH3拖车迎风侧', 'CRH3拖车迎风侧'],
                                  ['CRH3拖车迎风侧', '无风荷载', 'CRH3拖车迎风侧', 'CRH3拖车迎风侧']]
                                 ]
    # wind_coe.define(air_dens, ave_wind_speed, wind_direction_in_rad, wind_field_start_x,
    #                 consider_fluctuating, roughness, reference_altitude, deck_altitude, space_pt_num, space_length,
    #                 max_freq, random_seed, last_time, smooth_dist, smooth_time,
    #                 wind_coe_dict_bri, wind_node_group_dict, wind_load_assign_list_bri,
    #                 wind_coe_dict_veh, wind_field_ctrl_pt, wind_load_assign_list_veh)
    # wind_coe.write_dat('D:\\')

    wind_coe2 = WindCoe()
    wind_coe2.read_dat('D:\\')
    print(wind_coe2.wind_coe_dict_veh)
    print(wind_coe2.wind_coe_dict_bri)
    wind_coe2.write_dat('D:\\')
