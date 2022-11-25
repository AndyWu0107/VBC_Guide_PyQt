from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from UIPostTableShow import Ui_PostTableShow


class GuidePostTableShowDialog(QDialog, Ui_PostTableShow):
    def __init__(self, condition_name_list, veh_type_dict,
                 veh_acc_method, bri_acc_method, wheel_force_method,
                 veh_acc_filt_range, bri_acc_filt_range, wheel_force_filt_range,
                 attend_post_node_list, baseline_post_node_dict_for_table,
                 max_reduction_ration_dict_by_veh_type, max_vertical_wheel_force_dict_by_veh_type,
                 max_derail_factor_dict_by_veh_type, max_horizontal_wheel_force_dict_by_veh_type,
                 max_dynamic_irr_vertical_dict_by_veh_type, max_dynamic_irr_horizontal_dict_by_veh_type,
                 max_dynamic_irr_yaw_dict_by_veh_type, max_wheel_rail_dis_vertical_dict_by_veh_type,
                 max_wheel_rail_dis_horizontal_dict_by_veh_type, max_wheel_rail_dis_yaw_dict_by_veh_type,
                 max_veh_acc_vertical_front_dict_by_veh_type, max_veh_acc_vertical_rear_dict_by_veh_type,
                 max_veh_acc_horizontal_front_dict_by_veh_type, max_veh_acc_horizontal_rear_dict_by_veh_type,
                 veh_sperling_vertical_front_dict_by_veh_type, veh_sperling_vertical_rear_dict_by_veh_type,
                 veh_sperling_horizontal_front_dict_by_veh_type, veh_sperling_horizontal_rear_dict_by_veh_type,
                 max_bri_dx_list, max_bri_dy_list, max_bri_dz_list, max_bri_rx_list,
                 max_bri_ry_list, max_bri_rz_list, max_bri_ax_list, max_bri_ay_list,
                 max_bri_az_list, max_bri_arx_list, max_bri_ary_list, max_bri_arz_list):
        super(GuidePostTableShowDialog, self).__init__()
        self.setupUi(self)
        self.setWindowFlag(Qt.WindowMinMaxButtonsHint)

        def get_processing_method_name(method_text, filt_range=None):
            if method_text == 'max':
                method_name_text = '时程数据最大值'
            elif method_text == 'filt_max':
                method_name_text = '时程数据%.2fHz~%.2fHz带通滤波后取最大值' % (filt_range[0], filt_range[1])
            else:
                method_name_text = method_text
            return method_name_text

        veh_acc_method_name = get_processing_method_name(veh_acc_method, veh_acc_filt_range)
        bri_acc_method_name = get_processing_method_name(bri_acc_method, bri_acc_filt_range)
        wheel_force_method_name = get_processing_method_name(wheel_force_method, wheel_force_filt_range)

        # 车体加速度及平稳性表格-首先把车体不同部位的测试结果进行融合，没有人会分别关心车体各个部位的加速度最大值
        max_veh_acc_vertical_total_dict_by_veh_type = \
            self.fuse_data_of_different_position(max_veh_acc_vertical_front_dict_by_veh_type,
                                                 max_veh_acc_vertical_rear_dict_by_veh_type)
        max_veh_acc_horizontal_total_dict_by_veh_type = \
            self.fuse_data_of_different_position(max_veh_acc_horizontal_front_dict_by_veh_type,
                                                 max_veh_acc_horizontal_rear_dict_by_veh_type)
        max_veh_sperling_vertical_total_dict_by_veh_type = \
            self.fuse_data_of_different_position(veh_sperling_vertical_front_dict_by_veh_type,
                                                 veh_sperling_vertical_rear_dict_by_veh_type)
        max_veh_sperling_horizontal_total_dict_by_veh_type = \
            self.fuse_data_of_different_position(veh_sperling_horizontal_front_dict_by_veh_type,
                                                 veh_sperling_horizontal_rear_dict_by_veh_type)

        page_text_in_html = ''

        page_text_in_html += self.write_html_table_veh(condition_name_list, veh_type_dict,
                                                       veh_acc_method_name, wheel_force_method_name,
                                                       max_reduction_ration_dict_by_veh_type, max_derail_factor_dict_by_veh_type,
                                                       max_vertical_wheel_force_dict_by_veh_type, max_horizontal_wheel_force_dict_by_veh_type,
                                                       max_wheel_rail_dis_horizontal_dict_by_veh_type,
                                                       max_veh_acc_vertical_total_dict_by_veh_type, max_veh_acc_horizontal_total_dict_by_veh_type,
                                                       max_veh_sperling_vertical_total_dict_by_veh_type,
                                                       max_veh_sperling_horizontal_total_dict_by_veh_type
                                                       )

        page_text_in_html += '<h2>2.结构动力响应计算结果</h2>'

        if not max_bri_dx_list[0]:
            page_text_in_html += '<p>未指定参与汇总的结构关心结点。</p>'
        else:
            page_text_in_html += self.write_html_table_bri(condition_name_list, bri_acc_method_name,
                                                           attend_post_node_list, baseline_post_node_dict_for_table,
                                                           max_bri_dx_list, max_bri_dy_list, max_bri_dz_list,
                                                           max_bri_rx_list, max_bri_ry_list, max_bri_rz_list,
                                                           max_bri_ax_list, max_bri_ay_list, max_bri_az_list)

        self.show_page(page_text_in_html)

    @staticmethod
    def fuse_data_of_different_position(dict_obj_1, dict_obj_2):
        # 用于将不同测点的车体响应融合，即仅保留相对较大的那个结果
        total_dict_obj = {}
        for i_veh in dict_obj_1.keys():
            i_total_data_list = []
            for h_condition in range(0, len(dict_obj_1[i_veh])):
                h_1_data_list = dict_obj_1[i_veh][h_condition]
                h_2_data_list = dict_obj_2[i_veh][h_condition]
                h_total_data_list = [max(h_1_data_list[x], h_2_data_list[x])
                                     for x in range(0, len(h_1_data_list))]
                i_total_data_list.append(h_total_data_list)
            total_dict_obj[i_veh] = i_total_data_list
        return total_dict_obj

    @staticmethod
    def generate_veh_table_list_from_dict(dict_obj):
        # 输入：按车型存储的各档速度下某一指标的评价值
        # 输出：根据html展示表格的格式排列的list
        data_table_list = [dict_obj[i_veh] for i_veh in dict_obj.keys()]
        # [[[1车工况1速度1数据, 1车工况1速度2数据, ...], [1车工况2速度1数据, 1车工况2速度2数据, ...]],
        #  [[2车工况1速度1数据, 2车工况1速度2数据, ...], [2车工况2速度1数据, 2车工况2速度2数据, ...]], ...]

        veh_id_list = [i_veh for i_veh in dict_obj.keys()]

        return data_table_list, veh_id_list

    @staticmethod
    def write_html_table_veh(condition_name_list, veh_type_dict,
                             veh_acc_method_name, wheel_force_method_name,
                             max_reduction_ration_dict_by_veh_type, max_derail_factor_dict_by_veh_type,
                             max_vertical_wheel_force_dict_by_veh_type, max_horizontal_wheel_force_dict_by_veh_type,
                             max_wheel_rail_dis_horizontal_dict_by_veh_type,
                             max_veh_acc_vertical_total_dict_by_veh_type, max_veh_acc_horizontal_total_dict_by_veh_type,
                             max_veh_sperling_vertical_total_dict_by_veh_type, max_veh_sperling_horizontal_total_dict_by_veh_type
                             ):
        # 把车辆的动力响应结果整理在一张表中，一种车型列一张表，包含表格前段落标题
        col_name_html_text = \
            '''<tr align="center"><th rowspan="2">工况</th><th rowspan="2">车速档位</th><th rowspan="2">减载率</th><th rowspan="2">脱轨系数</th><th rowspan="2">轮轨竖向力<br>(kN)</th><th rowspan="2">轮轨横向力<br>(kN)</th><th rowspan="2">轮轨横向相对位移<br>(mm)</th><th colspan="2">车体加速度<br>(m/s<sup>2</sup>)</th><th colspan="2">车体平稳性</th>
            <tr align="center"><th>竖向</th><th>横向</th><th>竖向</th><th>横向</th></tr></tr>'''
        chapter_html_text = '<h2>1.车辆动力响应</h2>'
        k = 1
        for k_veh in max_reduction_ration_dict_by_veh_type.keys():
            k_table_html_text_temp = ''
            k_table_caption = '<caption>%s</caption>' % veh_type_dict[k_veh][0]
            k_chapter_title = '<h3>1.%d %s</h3>' % (k, veh_type_dict[k_veh][0])
            k += 1
            for h_cond in range(len(condition_name_list)):
                h_speed_num = len(max_reduction_ration_dict_by_veh_type[k_veh][h_cond])
                if h_speed_num == 0:  # 一种特殊情形：某辆车没有出现在某个工况中
                    k_table_html_text_temp += '<tr align="center"><th>%s</th><td colspan="10">%s未参与此工况</td></tr>'\
                                              % (condition_name_list[h_cond], veh_type_dict[k_veh][0])
                else:
                    k_table_html_text_temp += '<tr align="center"><th rowspan="%d">%s</th>' % (h_speed_num, condition_name_list[h_cond])
                    for i_speed in range(h_speed_num):
                        i_table_html_text_temp = '''<td>档位%d</td><td>%.2f</td><td>%.2f</td><td>%.2f</td><td>%.2f</td>
                                             <td>%.2f</td><td>%.2f</td><td>%.2f</td><td>%.2f</td><td>%.2f</td></tr>''' \
                                             % ((i_speed+1),
                                                max_reduction_ration_dict_by_veh_type[k_veh][h_cond][i_speed],
                                                max_derail_factor_dict_by_veh_type[k_veh][h_cond][i_speed],
                                                max_vertical_wheel_force_dict_by_veh_type[k_veh][h_cond][i_speed] * 0.001,
                                                max_horizontal_wheel_force_dict_by_veh_type[k_veh][h_cond][i_speed] * 0.001,
                                                max_wheel_rail_dis_horizontal_dict_by_veh_type[k_veh][h_cond][i_speed] * 1000.0,
                                                max_veh_acc_vertical_total_dict_by_veh_type[k_veh][h_cond][i_speed],
                                                max_veh_acc_horizontal_total_dict_by_veh_type[k_veh][h_cond][i_speed],
                                                max_veh_sperling_vertical_total_dict_by_veh_type[k_veh][h_cond][i_speed],
                                                max_veh_sperling_horizontal_total_dict_by_veh_type[k_veh][h_cond][i_speed])
                        if i_speed == 0:
                            k_table_html_text_temp += i_table_html_text_temp
                        else:
                            k_table_html_text_temp += ('<tr align="center">'+i_table_html_text_temp)
            k_table_html_text = '<table border="1" cellspacing="0"  align="center">%s</table>' % (k_table_caption + col_name_html_text + k_table_html_text_temp)
            chapter_html_text += (k_chapter_title+k_table_html_text)
            chapter_remark_html_text = '''<p><pre>    <b>注：</b><br>    1.轮轨力相关指标(减载率、脱轨系数、轮轨力)采用的数据处理方法：%s；<br>    2.车体加速度采用的数据处理方法：%s。</pre></p>''' % (wheel_force_method_name, veh_acc_method_name)
            chapter_html_text += chapter_remark_html_text
        return chapter_html_text

    @staticmethod
    def write_html_table_bri(condition_name_list, bri_acc_method_name,
                             attend_post_node_list, baseline_post_node_dict_for_table,
                             max_bri_dx_list, max_bri_dy_list, max_bri_dz_list, max_bri_rx_list,max_bri_ry_list,
                             max_bri_rz_list, max_bri_ax_list, max_bri_ay_list,max_bri_az_list):
        # 把车辆的动力响应结果整理在一张表中，一种车型列一张表，包含表格前段落标题
        col_name_html_text = '''<tr align="center"><th>工况</th><th width="80">车速档位</th>
        <th width="80">dx<br>(mm)</th><th width="80">dy<br>(mm)</th><th width="80">dz<br>(mm)</th>
        <th width="80">ax<br>(m/s<sup>2</sup>)</th><th width="80">ay<br>(m/s<sup>2</sup>)</th><th width="80">az<br>(m/s<sup>2</sup>)</th>
        <th width="80">rx<br>(10<sup>-4</sup>rad)</th><th width="80">ry<br>(10<sup>-4</sup>rad)</th><th width="80">rz<br>(10<sup>-4</sup>rad)</th></tr>'''
        chapter_html_text = ''
        table_html_text_temp = ''
        for h_cond in range(len(condition_name_list)):
            h_speed_num = len(max_bri_dx_list[h_cond][0])
            table_html_text_temp += '<tr align="center"><th rowspan="%d">%s</th>'\
                                    % (h_speed_num, condition_name_list[h_cond])
            for i_speed in range(h_speed_num):
                i_data_in_table = (i_speed+1,
                                   max([x[i_speed] for x in max_bri_dx_list[h_cond]])*1000.0,
                                   max([x[i_speed] for x in max_bri_dy_list[h_cond]])*1000.0,
                                   max([x[i_speed] for x in max_bri_dz_list[h_cond]])*1000.0,
                                   max([x[i_speed] for x in max_bri_ax_list[h_cond]]),
                                   max([x[i_speed] for x in max_bri_ay_list[h_cond]]),
                                   max([x[i_speed] for x in max_bri_az_list[h_cond]]),
                                   max([x[i_speed] for x in max_bri_rx_list[h_cond]])*10000.0,
                                   max([x[i_speed] for x in max_bri_ry_list[h_cond]])*10000.0,
                                   max([x[i_speed] for x in max_bri_rz_list[h_cond]])*10000.0)
                '''明天的工作：把上面已经取好的每一行的数据塞进表格'''
                i_table_html_text_temp = '''<td>档位%d</td><td>%.3f</td><td>%.3f</td><td>%.3f</td><td>%.3f</td>
                <td>%.3f</td><td>%.3f</td><td>%.3f</td><td>%.3f</td><td>%.3f</td></tr>''' % i_data_in_table
                if i_speed == 0:
                    table_html_text_temp += i_table_html_text_temp
                else:
                    table_html_text_temp += ('<tr align="center">'+i_table_html_text_temp)
        table_html_text = '<table border="1" cellspacing="0"  align="center">%s</table>'\
                               % (col_name_html_text+table_html_text_temp)
        post_node_remark_text_list = ['%d(%s)' % (i, baseline_post_node_dict_for_table[i])
                                      for i in attend_post_node_list]
        post_node_remark_text = ','.join(post_node_remark_text_list)
        chapter_remark_html_text = '''<p><pre>    <b>注：</b><br>    1.结构关心结点加速度采用的数据处理方法：%s；<br>    2.参与统计的结构节点范围：%s。</pre></p>'''\
                                   % (bri_acc_method_name, post_node_remark_text)
        chapter_html_text += (table_html_text+chapter_remark_html_text)
        return chapter_html_text

    def show_page(self, table_text_in_html):
        # 加载html代码(这里注意html代码是用三个单引号包围起来的)
        total_html_text = '''<!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta http-equiv="X-UA-Compatible" content="IE=edge">
            <title></title>
            <link rel="stylesheet" href="">
        </head>
        <body>
            
        %s
        </body>
        </html>''' % table_text_in_html
        self.browser.setHtml(total_html_text)


# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     win = GuidePostTableShowDialog()
#     win.show()
#     app.exit(app.exec_())
