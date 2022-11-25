import re
import shutil
# 取一个int整数对应二进制数的指定位数的01状态
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox, QApplication


def get_bit_val(number, index):
    if number & (1 << (index - 1)) > 0:
        return 1
    else:
        return 0


def list_widget_order_up(list_obj):
    old_row = list_obj.currentRow()
    if (old_row != -1) and (old_row != 0):
        item = list_obj.currentItem()
        list_obj.takeItem(old_row)
        list_obj.insertItem(old_row-1, item)
        list_obj.setCurrentRow(old_row-1)


def list_widget_order_down(list_obj):
    old_row = list_obj.currentRow()
    if (old_row != -1) and (old_row != list_obj.count()-1):
        item = list_obj.currentItem()
        list_obj.takeItem(old_row)
        list_obj.insertItem(old_row+1, item)
        list_obj.setCurrentRow(old_row+1)


def table_select_range(table_obj):
    # 区域选中
    select_rect = table_obj.selectedRanges()
    if select_rect:  # 判断是否为空
        for r in select_rect:  # 获取范围边界
            top = r.topRow()
            left = r.leftColumn()
            bottom = r.bottomRow()
            right = r.rightColumn()
    else:
        top = -1
        left = -1
        bottom = -1
        right = -1
    return top, left, bottom, right


def table_copy(table_obj):
    top, left, bottom, right = table_select_range(table_obj)
    column_n = right - left + 1
    row_n = bottom - top + 1
    number = row_n * column_n
    c = []
    for i in range(number):
        c.append(' \t')  # 注意，是空格+\t
        if (i % column_n) == (column_n - 1):
            c.append('\n')
        else:
            pass
        # 这里生成了一个列表，大小是：行X（列+1），换行符占了一列。默认情况下，列表中全部是空格
    # c.pop()  # 删去最后多余的换行符
    # 不删了，因为excel默认最后一行末尾有一个换行符
    range1 = range(top, bottom + 1)
    range2 = range(left, right + 1)
    for row in range1:
        for column in range2:
            try:
                # 计算出单元格的位置，替换掉原来的空格；每行最后一个\t省略
                data = table_obj.item(row, column).text()
                number2 = (row - top) * (column_n + 1) + (column - left)
                if column != range2[-1]:
                    c[number2] = data + '\t'
                else:
                    c[number2] = data
            except:
                pass
    str_to_clipboard = str()
    for s in c:
        str_to_clipboard = str_to_clipboard + s
    return str_to_clipboard


def table_paste(data, table_obj, tables_ban_paste=None):
    # print('enter paste')
    if tables_ban_paste is None:
        tables_ban_paste = []
    try:  # 有时会误触ctrl+v，避免报错，所以就try了。典型场景：复制了不符合表格格式的东西，就会报错
        # 禁止粘贴操作的表格黑名单
        if table_obj in tables_ban_paste:
            return 1
        top, left, bottom, right = table_select_range(table_obj)
        if (top != bottom) or (left != right):
            return 2
        if data.hasText():
            content = data.text()
            if content[-1] != '\n':
                content.append('\n')
        else:
            content = ''
        # 计算剪贴板数据的行列数，用于：(1)判断粘贴位置是否有误（列是否超界）；(2)表格不够大时自动增加行
        content_row_num = content.count('\n')  # 复制时最后一行末尾都有个换行，但下面粘贴的时候是要省略掉的
        content_col_num = int(content.count('\t') / content_row_num + 1)
        if left + content_col_num > table_obj.columnCount():
            return 3
        # 不得在禁止编辑的单元格粘贴
        for i_row in range(top, top + content_row_num):
            for i_col in range(left, left + content_col_num):
                if table_obj.item(i_row, i_col):
                    if get_bit_val(int(table_obj.item(i_row, i_col).flags()), 2) == 0:
                        return 3

        if top + content_row_num > table_obj.rowCount():
            row_num_to_add = top + content_row_num - table_obj.rowCount()
            for i_row_to_add in range(0, row_num_to_add):
                table_obj.insertRow(table_obj.rowCount())

        # 正式粘贴：根据\t和\n识别数据格式，依次放入单元格
        b = str()
        i = top
        j = left
        if content:  # 只要content不为空，末尾一定是一个换行，要把这个换行删掉
            content = content[0:len(content) - 1]
        for a in content:
            if a != '\n':
                if a != '\t':
                    b = b + a
                else:
                    table_obj.item(i, j).setText(b)
                    b = ''
                    j += 1
            else:
                table_obj.item(i, j).setText(b)
                b = ''
                i += 1
                j = left
            table_obj.item(i, j).setText(b)
        return 0
    except:
        return 0


def table_set_align_center_readonly(table_obj, rows_to_align, cols_readonly=None, cols_skip_process=None):
    if cols_readonly is None:
        cols_readonly = []
    if cols_skip_process is None:
        cols_skip_process = []
    for i_row in rows_to_align:
        for i_col in range(0, table_obj.columnCount()):
            # 表格控件离谱的初始化，留意！
            if i_col in cols_skip_process:
                continue
            if not table_obj.item(i_row, i_col):
                i_item = QTableWidgetItem('')
                table_obj.setItem(i_row, i_col, i_item)
            table_obj.item(i_row, i_col).setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            if i_col in cols_readonly:
                table_obj.item(i_row, i_col).setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)


def table_add_row(table_obj, always_to_last=False):
    if (table_obj.currentRow() == -1) or always_to_last:
        row_to_insert = table_obj.rowCount()
    else:
        row_to_insert = table_obj.currentRow()
    table_obj.insertRow(row_to_insert)


def table_delete_row(target_table_obj, rows_to_ign=[]):
    top, left, bottom, right = table_select_range(target_table_obj)
    if top != -1:
        for i_row in range(bottom, top - 1, -1):
            if i_row not in rows_to_ign:
                target_table_obj.removeRow(i_row)


def table_auto_numbering(table_obj, row_to_start=0):
    for i_row in range(row_to_start, table_obj.rowCount()):
        table_obj.item(i_row, 0).setText(str(i_row - row_to_start + 1))


# 把表格的指定行上移一个，默认移动鼠标选中的行，亦可在参数中直接指定
def table_row_order_up(window_obj, table_obj, row_to_order=None, rows_to_ign=[]):
    if row_to_order is not None:
        top = row_to_order
    else:
        top, left, bottom, right = table_select_range(table_obj)
        if top != bottom:
            QMessageBox.warning(window_obj, "警告", "不支持同时移动多行。")
            return 0
        if top == -1:
            QMessageBox.warning(window_obj, "警告", "请先选中一行。")
            return 0
        if top in rows_to_ign:
            return 0
    if top > 0:
        table_obj.insertRow(top + 1)
        for i_col in range(0, table_obj.columnCount()):
            if table_obj.item(top - 1, i_col):
                i_item = table_obj.takeItem(top - 1, i_col)
                table_obj.setItem(top + 1, i_col, i_item)
            if table_obj.cellWidget(top - 1, i_col):
                i_widget = table_obj.cellWidget(top - 1, i_col)
                table_obj.removeCellWidget(top + 1, i_col)
                table_obj.setCellWidget(top + 1, i_col, i_widget)
        table_obj.removeRow(top - 1)
        return 1
    else:  # 到顶了就不上移
        return 2


def table_row_order_down(window_obj, table_obj, row_to_order=None, rows_to_ign=[]):
    if row_to_order is not None:
        top = row_to_order
    else:
        top, left, bottom, right = table_select_range(table_obj)
        if top != bottom:
            QMessageBox.warning(window_obj, "警告", "不支持同时移动多行。")
            return 0
        if top == -1:
            QMessageBox.warning(window_obj, "警告", "请先选中一行。")
            return 0
        if top in rows_to_ign:
            return 0
    if top < table_obj.rowCount() - 1:
        table_obj.insertRow(top)
        for i_col in range(0, table_obj.columnCount()):
            if table_obj.item(top + 2, i_col):
                i_item = table_obj.takeItem(top + 2, i_col)
                table_obj.setItem(top, i_col, i_item)
            if table_obj.cellWidget(top + 2, i_col):
                i_widget = table_obj.cellWidget(top + 2, i_col)
                table_obj.removeCellWidget(top, i_col)
                table_obj.setCellWidget(top, i_col, i_widget)
        table_obj.removeRow(top + 2)
        return 1
    else:  # 到底了就不下移
        return 2


def monitor_key_press_event(window_obj, event, clipboard, tables_ban_paste=None):
    if window_obj.focusWidget().__class__.__name__ == "QTableWidget" and (event.key() == Qt.Key_C) \
            and QApplication.keyboardModifiers() == Qt.ControlModifier:
        # 按键事件，ctrl+c时触发，复制。
        current_table_to_handle = window_obj.focusWidget()  # 强行把当前选中的表格指向被拖动的表格，否则直接块选时clicked信号识别不到，造成复制时闪退
        str_to_clipboard = table_copy(current_table_to_handle)
        clipboard.setText(str_to_clipboard)
    else:
        pass
    if window_obj.focusWidget().__class__.__name__ == "QTableWidget" and (event.key() == Qt.Key_V) \
            and QApplication.keyboardModifiers() == Qt.ControlModifier:
        data = clipboard.mimeData()
        current_table_to_handle = window_obj.focusWidget()  # 强行把当前选中的表格指向被拖动的表格，否则直接块选时clicked信号识别不到，造成粘贴到错误表格
        if tables_ban_paste is None:
            tables_ban_paste = []
        err_code = table_paste(data, current_table_to_handle, tables_ban_paste)
        if err_code == 1:
            QMessageBox.warning(window_obj, "警告", "此表格不支持粘贴操作。")
        elif err_code == 2:
            QMessageBox.warning(window_obj, "警告", "块选时不允许粘贴。\n请选中目标粘贴区域的左上角。")
        elif err_code == 3:
            QMessageBox.warning(window_obj, "警告", "粘贴范围超过可编辑边界。")
    else:
        pass


def delete_all_rows(table_obj):
    for i_row in range(0, table_obj.rowCount()):
        print(table_obj.rowCount())
        table_obj.removeRow(0)


# 根据midas格式的字符串，获取排好序的节点号list
def get_num_list_from_text(text):
    # 1.根据逗号、分号、空格、制表、回车符号分割
    annotation_idx = text.find('!')
    if annotation_idx != -1:
        text = text[0:annotation_idx - 1]
    text_list = re.split('[,; \n\t，；]', text)
    result1 = list(filter(None, text_list))
    # result = list(map(float, result))
    # return result

    # 2.把分好的各个小字符串，根据to、by、-关键词分割
    result2 = []
    for i_text in result1:
        i_text = i_text.replace('by', 'b', 1)
        i_text = i_text.replace('to', 't', 1)
        i_text = i_text.replace('-', 't', 1)
        i_text = re.split('[bt]', i_text)
        result2.append(i_text)

    # 3.检查分好的各个小字符串是否非法
    # 后期用正则优化，先这样用着
    result3 = result2
    # 4.根据各个小字符串，得到各个小字符串对应的数字list
    result4 = []
    for i_list in result3:
        if len(i_list) == 1:
            i_num = int(i_list[0])
            result4.append(i_num)
        if len(i_list) == 2:
            i_num_start = int(i_list[0])
            i_num_end = int(i_list[1])
            [result4.append(i) for i in range(i_num_start, i_num_end + 1)]
        if len(i_list) == 3:
            i_num_start = int(i_list[0])
            i_num_end = int(i_list[1])
            i_num_interval = int(i_list[2])
            [result4.append(i) for i in range(i_num_start, i_num_end + 1, i_num_interval)]
    # 5.给所有数字排序
    result4.sort()
    return result4


def path_verify(path):
    path = path.replace('/', '\\')
    if path[-1] != '\\':
        path = path + '\\'
    return path


# 从文件的完整路径中获取其所在目录的路径
def get_dir_name(path):
    list1 = path.split('/')
    dir_path = '/'.join(list1[0:-1]) + '/'
    return dir_path


def get_data_from_fileline(text):
    # text = '200, 250 300  350,400         420\n'
    annotation_idx = text.find('!')
    if annotation_idx != -1:
        text = text[0:annotation_idx - 1]
    text_list = re.split('[, \n\t]', text)
    data_result = list(filter(None, text_list))
    data_result = list(map(float, data_result))
    if len(data_result) == 1:
        data_result = data_result[0]
    return data_result


def get_denotation_from_fileline(text):
    annotation_idx = text.find('!')
    if annotation_idx != -1 and annotation_idx != len(text) - 1:
        text_result = text[annotation_idx + 1: len(text)]
    else:
        text_result = '未命名'
    return text_result


def skip_blank_lines(file_text_list):
    result = (''.join(file_text_list)).splitlines(False)
    result = list(filter(None, result))
    line_num_deleted = 0
    for i in range(0, len(result)):
        if result[i - line_num_deleted].isspace():
            result.remove(result[i - line_num_deleted])
            line_num_deleted += 1
    return result


def take_id(elem):
    return elem[0]


class SubBri:
    def define(self, bridge_nodes_info, id_rail_nodes, post_nodes,
               nonlinear_springs, sync_output_dofs, bri_rail_mode_num,
               excluded_modes, mode_files_path, mode_files_name, modes_in_each_file, damps_in_each_file):

        self.bridge_nodes_info = bridge_nodes_info
        self.id_rail_nodes = id_rail_nodes
        self.nonlinear_springs = nonlinear_springs
        self.num_nonlinear_springs = len(self.nonlinear_springs)
        self.id_non_spring_nodes = []
        for i_spring in self.nonlinear_springs:
            self.id_non_spring_nodes.append(i_spring[0])
            self.id_non_spring_nodes.append(i_spring[1])
        self.id_post_nodes = []
        self.name_post_nodes = []
        for i_post_node in post_nodes:
            self.id_post_nodes.append(i_post_node[0])
            self.name_post_nodes.append(i_post_node[1])

        self.id_bridge_nodes = [i[0] for i in self.bridge_nodes_info]

        self.num_rail_nodes = len(self.id_rail_nodes)
        self.num_post_nodes = len(self.id_post_nodes)
        self.num_bridge_nodes = len(self.bridge_nodes_info)

        # 处理同步输出结点信息
        self.sync_output_dofs = sync_output_dofs
        self.num_sync_output_dofs = len(self.sync_output_dofs)

        # 处理不予考虑的模态
        self.excluded_modes = excluded_modes

        # 处理模态文件信息
        self.mode_files_path = mode_files_path
        self.mode_files_name = mode_files_name
        self.num_mode_files = len(mode_files_name)
        self.modes_in_each_file = modes_in_each_file
        self.damps_in_each_file = damps_in_each_file

        # 传输其它简单控制参数
        self.bri_rail_mode_num = bri_rail_mode_num

    @staticmethod
    def get_node_info_from_midas(mct_file_path, nodes_to_get=None):
        f_mct = open(mct_file_path, 'r')

        num_this_line = 0
        num_unit_title_line = -100
        num_node_title_line = -100
        flag_unit_got = False
        flag_node_got = False
        nodes_str = []
        for i_line in f_mct.readlines():  # 读取一遍mct文件，获取单位、结点行范围
            num_this_line += 1  # 被读取的行号计数，从1开始
            this_line = i_line.strip()

            # 1.获取mct文件中的量纲
            if this_line[0:5] == '*UNIT':
                num_unit_title_line = num_this_line
            if num_this_line == num_unit_title_line + 2:
                units = this_line.split(",")
                for i in range(0, len(units)):
                    units[i] = units[i].strip()
                flag_unit_got = True

            # 2.获取mct文件中的所有结点信息
            if this_line[0:5] == '*NODE':
                num_node_title_line = num_this_line
                num_node_line_start = num_node_title_line + 2
            if (num_this_line >= num_node_title_line + 2) & (num_node_title_line != -100):
                if len(this_line) == 0:
                    num_node_line_end = num_this_line - 1
                    flag_node_got = True
                elif this_line[0].isdigit() is False:
                    num_node_line_end = num_this_line - 1
                    flag_node_got = True
                else:
                    this_node = this_line.split(",")
                    for i in range(0, len(this_node)):
                        this_node[i] = this_node[i].strip()
                    nodes_str.append(this_node)

            # 3.判断是否已经读到所有必需信息
            if (flag_unit_got & flag_node_got) is True:
                break

        f_mct.close()

        nodes = []
        nodes_id = []
        for i_node in range(0, len(nodes_str)):
            this_node_float = list(map(float, nodes_str[i_node]))
            this_node_float[0] = int(this_node_float[0])
            nodes.append(this_node_float)
            nodes_id.append(this_node_float[0])

        if nodes_to_get:
            nodes_to_return = []
            nodes_id_to_return = []
            for j_node_to_get in nodes_to_get:
                idx_in_list = nodes_id.index(j_node_to_get)
                nodes_to_return.append(nodes[idx_in_list])
                nodes_id_to_return.append(nodes_id[idx_in_list])
        else:
            nodes_to_return = nodes
            nodes_id_to_return = nodes_id

        return nodes_to_return, nodes_id_to_return

    @staticmethod
    def bridge_node_matrix_verify(bridge_node_matrix):
        # 把桥梁结点矩阵按结点号排个序
        def sort_by_node_no(elem):
            return elem[0]

        # bridge_node_matrix.sort(key=sort_by_node_no)  # 注释于2021.1.22，vbc3.3.5已不必排序
        bridge_node_matrix_verified = bridge_node_matrix
        return bridge_node_matrix_verified

    def write_dat(self, dat_path):  # compute_stage：计算阶段，前处理为1，后处理为2：主要涉及到利用ansys计算时须中途换文件的问题
        filename = path_verify(dat_path) + "Modal_Substructure_Bridge.dat"
        f_msb = open(filename, 'w')
        # os.chmod(filename, 0o777)

        # 1.写入第一批控制参数
        line1 = [self.num_bridge_nodes, self.num_rail_nodes, self.num_nonlinear_springs, self.num_sync_output_dofs,
                 self.bri_rail_mode_num]
        if len(self.excluded_modes) == 0:
            line1.append(0)
        else:
            line1.append(1)
            line1.append(self.excluded_modes[0])
            line1.append(self.excluded_modes[1])
        line1_str_out = '\t'.join(str(i) for i in line1)
        f_msb.write(line1_str_out)
        f_msb.write('\n\n')

        # 2.写入“桥梁结点”（此处即为output，rail和post的并集）
        for i_bri_node in range(0, self.num_bridge_nodes):
            line2_i = self.bridge_nodes_info[i_bri_node]
            line2_i_str_out = ',\t'.join(str(i) for i in line2_i)
            f_msb.write(line2_i_str_out)
            f_msb.write('\n')

        f_msb.write('\n\n')
        # 3.写入rail结点
        for i_rail_node in range(0, self.num_rail_nodes):
            f_msb.write(str(self.id_rail_nodes[i_rail_node]))
            f_msb.write('\n')
        f_msb.write('\n\n')

        # 4.写入非线性弹簧信息
        if self.num_nonlinear_springs > 0:
            for i_spring in range(0, self.num_nonlinear_springs):
                line4_i = self.nonlinear_springs[i_spring]
                line4_i_str_out = ',\t'.join(str(i) for i in line4_i)
                f_msb.write(line4_i_str_out)
                f_msb.write('\n')
        f_msb.write('\n\n')

        # 5.写入同步输出结点信息
        if self.num_sync_output_dofs > 0:
            for i_sync in range(0, self.num_sync_output_dofs):
                line5_i = self.sync_output_dofs[i_sync]
                line5_i_str_out = ',\t'.join(str(i) for i in line5_i)
                f_msb.write(line5_i_str_out)
                f_msb.write('\n')
        f_msb.write('\n\n')

        # 6.写入结构模态信息
        # if compute_stage == 1:
        f_msb.write(str(self.num_mode_files))
        f_msb.write('\n')
        for i_mode_file in range(0, self.num_mode_files):
            f_msb.write(self.mode_files_path[i_mode_file])
            f_msb.write('\n')
            f_msb.write(self.mode_files_name[i_mode_file])
            f_msb.write('\n')
            f_msb.write(str(self.modes_in_each_file[i_mode_file]))
            f_msb.write('\n')
            line6_i = self.damps_in_each_file[i_mode_file]
            line6_i_str_out = '\t'.join(str(i) for i in line6_i)
            f_msb.write(line6_i_str_out)
            f_msb.write('\n')
        f_msb.write('\n\n')
        # elif compute_stage == 2:
        #     f_msb.write(str(1))
        #     f_msb.write('\n')
        #     f_msb.write(self.post_mode_file_path)
        #     f_msb.write('\n')
        #     f_msb.write(self.post_mode_file_name)
        #     f_msb.write('\n')
        #     f_msb.write(str(sum(self.modes_in_each_file)))
        #     f_msb.write('\n')
        #     line6 = self.damps_in_post_file
        #     line6_str_out = '\t'.join(str(i) for i in line6)
        #     f_msb.write(line6_str_out)
        #     f_msb.write('\n')
        #     f_msb.write('\n\n')

        # 7.写入后处理结点信息
        f_msb.write("Post\n\n")
        f_msb.write(str(self.num_post_nodes))
        f_msb.write("\n")
        for i_post in range(0, len(self.id_post_nodes)):
            line7_i = [str(self.id_post_nodes[i_post]), str(self.id_post_nodes[i_post]), '1',
                       ('!' + self.name_post_nodes[i_post])]
            line7_i_str_out = '\t'.join(line7_i)
            f_msb.write(line7_i_str_out)
            f_msb.write('\n')
        f_msb.write('\n\n0')  # 暂未支持内力后处理，直接写0，读取(read_dat)同

    def read_dat(self, dat_path):
        # 1.读取文件
        filename = path_verify(dat_path) + "Modal_Substructure_Bridge.dat"
        # with open(filename, "r", errors='ignore') as f_msb:
        with open(filename, "r") as f_msb:
            # os.chmod(filename, 0o777)
            dat_text = skip_blank_lines(f_msb.readlines())  # 读取文件所有行，并进行预处理，每个有效行均为list的一个元素
            '''
            预留：被读入的文件的正确性验证(考虑在主函数调用的时候直接try，这里不再进行检验)
            '''
            # 1.1 第一行控制参数
            line1 = get_data_from_fileline(dat_text[0])
            num_bridge_nodes, num_rail_nodes = int(line1[0]), int(line1[1])
            num_nonlinear_springs, num_sync_output_dofs = int(line1[2]), int(line1[3])
            bri_rail_mode_num = int(line1[4])
            if line1[5] == 0:
                excluded_modes = []
            else:
                excluded_modes = list(map(int, line1[6:8]))
            # 1.2 根据控制参数读取桥梁结点信息
            bridge_nodes_info = []
            for i_bri_node in range(1, num_bridge_nodes + 1):
                this_bridge_node = get_data_from_fileline(dat_text[i_bri_node])
                this_bridge_node[0] = int(this_bridge_node[0])
                bridge_nodes_info.append(this_bridge_node)
            # 1.3 根据控制参数读取轨道结点号
            id_rail_nodes = []
            for i_rail_node in range(1, num_rail_nodes + 1):
                line_idx_this_rail_node = num_bridge_nodes + i_rail_node
                this_rail_node = int(get_data_from_fileline(dat_text[line_idx_this_rail_node]))
                id_rail_nodes.append(this_rail_node)
            # 1.4 根据控制参数读取非线性弹簧信息
            nonlinear_springs = []
            if num_nonlinear_springs > 0:
                for i_spring in range(1, num_nonlinear_springs + 1):
                    line_idx_this_spring = num_bridge_nodes + num_rail_nodes + i_spring
                    this_spring = list(map(int, get_data_from_fileline(dat_text[line_idx_this_spring])))
                    nonlinear_springs.append(this_spring)
            # 1.5 根据控制参数读取同步输出响应的结点及DOF信息
            sync_output_dofs = []
            if num_sync_output_dofs > 0:
                for i_sync in range(1, num_sync_output_dofs + 1):
                    line_idx_this_sync = num_bridge_nodes + num_rail_nodes + num_nonlinear_springs + i_sync
                    this_sync_node = list(map(int, get_data_from_fileline(dat_text[line_idx_this_sync])))
                    sync_output_dofs.append(this_sync_node)
            # 1.6 根据控制参数读取模态文件信息
            line_idx_num_mode_files = (num_bridge_nodes + num_rail_nodes + num_nonlinear_springs + num_sync_output_dofs
                                       + 1)
            num_mode_files = int(get_data_from_fileline(dat_text[line_idx_num_mode_files]))
            mode_files_path = []
            mode_files_name = []
            modes_in_each_file = []
            damps_in_each_file = []
            for i_mode_file in range(1, num_mode_files + 1):
                line_idx_this_mode_file_path = line_idx_num_mode_files + (i_mode_file - 1) * 4 + 1
                mode_files_path.append(dat_text[line_idx_this_mode_file_path])
                mode_files_name.append(dat_text[line_idx_this_mode_file_path + 1])
                modes_in_each_file.append(int(get_data_from_fileline(dat_text[line_idx_this_mode_file_path + 2])))
                damps_in_this_file = get_data_from_fileline(dat_text[line_idx_this_mode_file_path + 3])
                damps_in_this_file[0] = int(damps_in_this_file[0])
                damps_in_this_file[1] = int(damps_in_this_file[1])
                damps_in_each_file.append(damps_in_this_file)
            # 1.7 读取后处理结点信息
            line_idx_num_post_nodes = (num_bridge_nodes + num_rail_nodes + num_nonlinear_springs + num_sync_output_dofs
                                       + num_mode_files * 4 + 3)
            num_post_nodes = int(get_data_from_fileline(dat_text[line_idx_num_post_nodes]))
            # id_post_nodes = []
            # name_post_nodes = []
            post_nodes = []
            for i_post_node in range(1, num_post_nodes + 1):
                line_idx_post_nodes = line_idx_num_post_nodes + i_post_node
                this_line_post_node = list(map(int, get_data_from_fileline(dat_text[line_idx_post_nodes])[0:3]))
                this_line_post_nodes_name = get_denotation_from_fileline(dat_text[line_idx_post_nodes])
                this_group_post_nodes = range(this_line_post_node[0], this_line_post_node[1] + 1,
                                              this_line_post_node[2])
                num_post_node_this_group = len(this_group_post_nodes)
                for i_post_node_this_group in range(1, num_post_node_this_group + 1):
                    # id_post_nodes.append(this_group_post_nodes[i_post_node_this_group - 1])
                    # name_post_nodes.append(this_line_post_nodes_name)
                    post_nodes.append([this_group_post_nodes[i_post_node_this_group - 1], this_line_post_nodes_name])
        # 2.将读取到的信息赋给实例属性
        # 2.1 根据指定的信息源获取模型结点信息
        self.bridge_nodes_info = bridge_nodes_info
        self.id_bridge_nodes = [x[0] for x in bridge_nodes_info]
        # 2.2 根据指定的rail和post结点号，整理待输出结点（即桥梁结点）的信息
        # id_rail_nodes.sort()
        self.id_rail_nodes = id_rail_nodes
        # post_nodes.sort(key=take_id)
        self.id_post_nodes = []
        self.name_post_nodes = []
        for i_post_node in post_nodes:
            self.id_post_nodes.append(i_post_node[0])
            self.name_post_nodes.append(i_post_node[1])
        self.num_rail_nodes = num_rail_nodes
        self.num_post_nodes = num_post_nodes
        self.num_bridge_nodes = num_bridge_nodes
        # 2.3 处理非线性弹簧参数
        self.nonlinear_springs = nonlinear_springs
        self.num_nonlinear_springs = num_nonlinear_springs
        # 2.4 处理同步输出结点信息
        self.sync_output_dofs = sync_output_dofs
        self.num_sync_output_dofs = num_sync_output_dofs
        # 2.5 处理不予考虑的模态
        self.excluded_modes = excluded_modes
        # 2.6 处理模态文件信息
        self.mode_files_path = mode_files_path
        self.mode_files_name = mode_files_name
        self.num_mode_files = num_mode_files
        self.modes_in_each_file = modes_in_each_file
        self.damps_in_each_file = damps_in_each_file
        # 2.7 传输其它简单控制参数
        self.bri_rail_mode_num = bri_rail_mode_num


class SolPara:

    def define(self, integral_method, dt_integration, step_num_each_output, w_r_contact_opt,
               bridge_coord_opt, rail_elastic_opt, rail_vertical_stiff, rail_vertical_damp):
        self.integral_method = int(integral_method)
        self.dt_integration = dt_integration
        self.step_num_each_output = int(step_num_each_output)
        self.w_r_contact_opt = int(w_r_contact_opt)
        self.bridge_coord_opt = int(bridge_coord_opt)
        self.rail_elastic_opt = int(rail_elastic_opt)
        self.rail_vertical_stiff = rail_vertical_stiff
        self.rail_vertical_damp = rail_vertical_damp

    def write_dat(self, dat_path):
        filename = path_verify(dat_path) + "SolutionParameters.dat"
        f_sol_para = open(filename, 'w')
        # os.chmod(filename, 0o777)
        # 第一行控制参数
        f_sol_para.write(str(self.integral_method))
        f_sol_para.write("\t\t\t!Integral Method (Wilson:0;Newmark:1;New Explicit:2;Rugge-kutta:4;PostPro:-1)\n")
        # 第二行控制参数
        f_sol_para.write(str(self.dt_integration))
        f_sol_para.write("\t\t\t!Time step for integration\n")
        # 第三行控制参数(已删除)

        # 第四行控制参数
        f_sol_para.write(str(self.step_num_each_output))
        f_sol_para.write("\t\t\t!Output Result Every N Steps\n")
        # 第五行控制参数
        f_sol_para.write(str(self.w_r_contact_opt))
        f_sol_para.write("\t\t\t!Option for wheel-rail contact (Spatial:1;Vertical only:0;Moving load:-1)\n")
        # 第六行控制参数
        f_sol_para.write(str(self.bridge_coord_opt))
        f_sol_para.write("\t\t\t!Coordination_sys_bridge (Z axis upward:1;Y axis upward:0)\n")
        # 第七行控制参数(已删除)
        # 第八行控制参数
        line8 = (self.rail_elastic_opt, self.rail_vertical_stiff, self.rail_vertical_damp)
        line8_str_out = '\t'.join(str(i) for i in line8)
        f_sol_para.write(line8_str_out)
        f_sol_para.write("\t\t\t!IsContact,StiContact and DamContact of track contact,for wheel-rail jump\n")
        # 第九行控制参数(已删除)

        f_sol_para.close()

    def read_dat(self, dat_path):
        filename = path_verify(dat_path) + "SolutionParameters.dat"
        # with open(filename, "r", errors='ignore') as f_sol_para:
        with open(filename, "r") as f_sol_para:
            # os.chmod(filename, 0o777)
            dat_text = skip_blank_lines(f_sol_para.readlines())  # 读取文件所有行，并进行预处理，每个有效行均为list的一个元素
            '''
            预留：被读入的文件的正确性验证
            '''
            # 1.第一行控制参数
            integral_method = int(get_data_from_fileline(dat_text[0]))
            # 2.第二行控制参数
            dt_integration = get_data_from_fileline(dat_text[1])
            # 3.第三行控制参数
            step_num_each_output = int(get_data_from_fileline(dat_text[2]))
            # 4.第四行控制参数
            w_r_contact_opt = int(get_data_from_fileline(dat_text[3]))
            # 5.第五行控制参数
            bridge_coord_opt = int(get_data_from_fileline(dat_text[4]))
            # 6.第六行控制参数
            line8 = get_data_from_fileline(dat_text[5])
            rail_elastic_opt = int(line8[0])
            rail_vertical_stiff, rail_vertical_damp = line8[1], line8[2]

            # 9.第九行控制参数
            # 10.根据读入的信息，给实例幅值
            self.define(integral_method, dt_integration, step_num_each_output, w_r_contact_opt,
                        bridge_coord_opt, rail_elastic_opt, rail_vertical_stiff, rail_vertical_damp)


class RailsLoc:

    # 用嵌套list存储各条轨道信息，这样不必保证每条轨道的点数相同
    def define(self, rail_matrix, track_width_name_vec, interpolation_interval, consider_vertical_curve=0,
               interpolation_method=0):
        self.interpolation_interval = interpolation_interval
        self.interpolation_method = interpolation_method
        self.consider_vertical_curve = consider_vertical_curve
        self.rail_matrix_verified = self.rail_matrix_verify(rail_matrix)
        self.track_width_name_vec = track_width_name_vec
        self.rail_num = len(self.rail_matrix_verified)
        self.max_point_num = 0
        for i_rail in range(0, self.rail_num):
            point_num_this_rail = len(self.rail_matrix_verified[i_rail])
            self.max_point_num = max(point_num_this_rail, self.max_point_num)

    def write_dat(self, dat_path):
        filename = path_verify(dat_path) + "Rails_Location.dat"
        f_rail = open(filename, 'w')
        # os.chmod(filename, 0o777)
        # 1.输出第一行控制参数
        line1 = [self.interpolation_interval, self.max_point_num]
        line1_str_out = ','.join(str(i) for i in line1)
        f_rail.write(line1_str_out)
        f_rail.write('\n')
        # 2.输出第二行控制参数（轨道总数）
        f_rail.write(str(self.rail_num))
        f_rail.write('\n\n')
        # 3.逐条轨道输出控制点信息
        for i_rail in range(0, self.rail_num):
            # 3.1 输出该条轨道的控制点数量、轨距及名称
            pt_num_this_rail = len(self.rail_matrix_verified[i_rail])
            f_rail.write(str(pt_num_this_rail) + '\t')
            track_width_this_rail = self.track_width_name_vec[i_rail][0]
            f_rail.write(str(track_width_this_rail) + '\t')
            name_this_rail = self.track_width_name_vec[i_rail][1]
            f_rail.write('!' + name_this_rail)
            f_rail.write('\n')
            # 3.2 输出该条轨道的控制点信息
            for i_pt in range(0, pt_num_this_rail):
                i_line = self.rail_matrix_verified[i_rail][i_pt]
                i_line_str_out = '\t'.join(str(i) for i in i_line)
                f_rail.write(i_line_str_out)
                f_rail.write('\n')
            f_rail.write('\n')
        # 4.输出最后一行控制参数（是否考虑竖曲线）
        if self.consider_vertical_curve == 1:
            f_rail.write("\n1")
        f_rail.close()

    def read_dat(self, dat_path):
        filename = path_verify(dat_path) + "Rails_Location.dat"
        # with open(filename, "r", errors='ignore') as f_rail:
        with open(filename, "r") as f_rail:
            # os.chmod(filename, 0o777)
            dat_text = skip_blank_lines(f_rail.readlines())  # 读取文件所有行，并进行预处理，每个有效行均为list的一个元素
            '''
            预留：被读入的文件的正确性验证
            '''
            # 1.第一行控制参数
            line1 = get_data_from_fileline(dat_text[0])
            interpolation_interval, max_pt_num = line1[0], int(line1[1])
            interpolation_method = 0
            # 2.第二行控制参数
            rail_num = int(get_data_from_fileline(dat_text[1]))
            # 3.根据控制参数，逐条轨道读取控制点信息
            pt_num_read = 0
            rail_matrix = []
            track_width_name_vec = []
            for i_rail in range(1, rail_num + 1):
                line_idx_pt_num_this_rail = i_rail + pt_num_read + 1
                pt_num_this_rail = int(get_data_from_fileline(dat_text[line_idx_pt_num_this_rail])[0])
                track_width_this_rail = float(get_data_from_fileline(dat_text[line_idx_pt_num_this_rail])[1])
                name_this_rail = get_denotation_from_fileline(dat_text[line_idx_pt_num_this_rail])
                track_width_name_vec.append([track_width_this_rail, name_this_rail])
                pt_matrix_this_rail = []
                for i_pt_this_rail in range(1, pt_num_this_rail + 1):
                    this_pt_list = get_data_from_fileline(dat_text[line_idx_pt_num_this_rail + i_pt_this_rail])
                    pt_matrix_this_rail.append(this_pt_list)
                rail_matrix.append(pt_matrix_this_rail)
                pt_num_read += pt_num_this_rail
            # 4.判断最后一个控制参数（是否考虑竖曲线效应），该参数的判定方式比较特别
            line_num_for_info_above = rail_num + pt_num_read + 2
            if len(dat_text) == line_num_for_info_above:
                consider_vertical_curve = 0
            else:
                consider_vertical_curve = int(get_data_from_fileline(dat_text[line_num_for_info_above]))
            # 5.根据读取的信息，定义实例
            self.define(rail_matrix, track_width_name_vec, interpolation_interval, consider_vertical_curve,
                        interpolation_method=0)

    @staticmethod
    def rail_matrix_verify(rail_matrix):
        rail_matrix_verified = rail_matrix
        return rail_matrix_verified


class Irregularity:

    def define(self, spectrum_level, random_seed, wave_length_min, wave_length_max, sample_length, interval,
               wave_length_filter=0.0, sample_source=1, smooth_distance=50.0, ratio1=1.0, ratio2=1.0, ratio3=1.0,
               sample_pt_list=[]):
        self.spectrum_level = spectrum_level
        self.random_seed = random_seed
        self.wave_length_min = wave_length_min
        self.wave_length_max = wave_length_max
        self.sample_length = sample_length
        self.interval = interval
        self.wave_length_filter = wave_length_filter
        self.sample_source = sample_source
        self.smooth_distance = smooth_distance
        self.ratio1 = ratio1
        self.ratio2 = ratio2
        self.ratio3 = ratio3
        self.sample_pt_list = sample_pt_list

    def write_dat(self, dat_path):
        filename = path_verify(dat_path) + "Irregularity.dat"
        f_irr = open(filename, 'w')
        # os.chmod(filename, 0o777)
        # 1.输出第一行（中文注释）
        f_irr.write("不平顺来源,谱等级,随机种子,最小波长,最大波长,模拟长度,间距,滤波波长\n")
        # 2.输出第二行（第一批控制参数）
        line2 = (self.sample_source, self.spectrum_level, self.random_seed, self.wave_length_min, self.wave_length_max,
                 self.sample_length, self.interval, self.wave_length_filter)
        line2_str_out = "\t".join(str(i) for i in line2)
        f_irr.write(line2_str_out)
        f_irr.write('\n')
        # 3.输出第三行（中文注释）
        f_irr.write("初始平滑处理距离\n")
        # 4.输出第四行（第二批控制参数）
        f_irr.write(str(self.smooth_distance))
        f_irr.write('\n')
        # 5.输出第五行（中文注释）
        f_irr.write("不平顺系数\n")
        # 6.输出第六行（第三批控制参数）
        line6 = [self.ratio1, self.ratio2, self.ratio3]
        line6_str_out = '\t'.join(str(i) for i in line6)
        f_irr.write(line6_str_out)
        f_irr.write('\n\n')
        # 7.输出剩下的样本数据点
        sample_text_to_write = ''
        for i_pt in self.sample_pt_list:
            i_pt_text_to_write = '\t'.join([str(i_pt[0]), str(i_pt[1]), str(i_pt[2]), '\n'])
            sample_text_to_write += i_pt_text_to_write
        f_irr.write(sample_text_to_write)
        f_irr.close()

    def read_dat(self, dat_path):
        filename = path_verify(dat_path) + "Irregularity.dat"
        # with open(filename, "r", errors='ignore') as f_irr:
        with open(filename, "r") as f_irr:
            # os.chmod(filename, 0o777)
            dat_text = skip_blank_lines(f_irr.readlines())  # 读取文件所有行，并进行预处理，每个有效行均为list的一个元素
            '''
            预留：被读入的文件的正确性验证
            '''
            # 1.第一批控制参数
            line2 = get_data_from_fileline(dat_text[1])
            sample_source = int(line2[0])
            spectrum_level = line2[1]
            random_seed = int(line2[2])
            wave_length_min = line2[3]
            wave_length_max = line2[4]
            sample_length = line2[5]
            interval = line2[6]
            wave_length_filter = line2[7]
            # 2.第二批控制参数
            smooth_distance = get_data_from_fileline(dat_text[3])
            # 3.第三批控制参数
            line6 = get_data_from_fileline(dat_text[5])
            ratio1, ratio2, ratio3 = line6[0], line6[1], line6[2]
            # 4.时程数据点
            sample_pt_list = []
            for i_pt in range(6, len(dat_text)):  # range(len)的写法可以直接包容没有数据点的情况
                i_line = get_data_from_fileline(dat_text[i_pt])
                i_pt_data = [i_line[0], i_line[1], i_line[2]]
                sample_pt_list.append(i_pt_data)
            # 5.根据读取的信息，定义实例
            self.define(spectrum_level, random_seed, wave_length_min, wave_length_max, sample_length, interval,
                        wave_length_filter, sample_source, smooth_distance, ratio1, ratio2, ratio3, sample_pt_list)


class VehOrg:

    def define(self, veh_matrix, train_name_vec, org_matrix):
        # 车列定义：二维数组
        self.veh_matrix_verified, self.veh_num_each_train = self.veh_matrix_verify(veh_matrix)
        self.train_num = len(self.veh_matrix_verified)  # 共定义了多少列车
        self.max_veh_num = max(self.veh_num_each_train)  # 每车列中最多有多少辆车
        self.train_name_vec = train_name_vec

        # 行车组织：三维数组，每车道的信息为一个二维数组：第一行为车列号、车道号，第二行及以后为车速、余振距离等信息
        self.org_matrix_verified = self.org_matrix_verify(org_matrix)
        self.train_num_on_way = len(self.org_matrix_verified)
        self.speed_num_on_way = len(self.org_matrix_verified[0]) - 1

    def write_dat(self, dat_path):
        filename = path_verify(dat_path) + "VehicleOrganization.dat"
        f_veh_org = open(filename, 'w')
        # os.chmod(filename, 0o777)
        # 1.输出被定义的列车的参数
        f_veh_org.write(str(self.train_num))
        f_veh_org.write(',')
        f_veh_org.write(str(self.max_veh_num))
        f_veh_org.write('\n\n')
        # 2.逐步输出被定义的每列车编组情况
        for i_train in range(0, self.train_num):
            # 2.1 输出这列车的车辆数、名称
            f_veh_org.write(str(self.veh_num_each_train[i_train]) + '\t')
            f_veh_org.write('!' + self.train_name_vec[i_train])
            f_veh_org.write('\n')
            # 2.2 输出这列车的详细编组
            for i_vehicle in range(0, self.veh_num_each_train[i_train]):
                f_veh_org.write(str(self.veh_matrix_verified[i_train][i_vehicle]))
                f_veh_org.write('\n')
            f_veh_org.write('\n')
        f_veh_org.write('\n\n')
        # 3. 输出上道车列参数
        f_veh_org.write(str(self.train_num_on_way))
        f_veh_org.write(',')
        f_veh_org.write(str(self.speed_num_on_way))
        f_veh_org.write('\n')
        # 4. 输出上道车列的车速信息
        for i_train_on_way in range(0, self.train_num_on_way):
            # 4.1 输出这列上道车的车列号、车道号
            f_veh_org.write(str(self.org_matrix_verified[i_train_on_way][0][0]))
            f_veh_org.write(',')
            f_veh_org.write(str(self.org_matrix_verified[i_train_on_way][0][1]))
            f_veh_org.write('\n')
            # 4.2 输出这列上道车的车速等运营信息
            for k_row in range(0, 5):
                for j_speed in range(0, self.speed_num_on_way):
                    f_veh_org.write(str(self.org_matrix_verified[i_train_on_way][j_speed + 1][k_row]) + '\t')
                f_veh_org.write('\n')
        f_veh_org.close()

    def read_dat(self, dat_path):
        filename = path_verify(dat_path) + "VehicleOrganization.dat"
        # with open(filename, "r", errors='ignore') as f_veh_org:
        with open(filename, "r") as f_veh_org:
            # os.chmod(filename, 0o777)
            dat_text = skip_blank_lines(f_veh_org.readlines())  # 读取文件所有行，并进行预处理，每个有效行均为list的一个元素
            '''
            预留：被读入的文件的正确性验证
            '''
            # 1.第一批控制参数：车列定义
            train_def_para = get_data_from_fileline(dat_text[0])
            train_num, max_veh_num = int(train_def_para[0]), int(train_def_para[1])
            # 2.根据控制参数，读取每列车的情况
            train_num_read = 0
            veh_num_read = 0
            veh_matrix = []  # np.zeros([train_num, max_veh_num], dtype=int)
            train_name_vec = []
            for i_train in range(1, train_num + 1):
                line_idx_veh_num_this_train = train_num_read + veh_num_read + 1
                veh_num_this_train = int(get_data_from_fileline(dat_text[line_idx_veh_num_this_train]))
                train_name_vec.append(get_denotation_from_fileline(dat_text[line_idx_veh_num_this_train]))
                veh_list_this_train = []
                for i_veh in range(1, veh_num_this_train + 1):
                    i_veh_type = get_data_from_fileline(dat_text[line_idx_veh_num_this_train + i_veh])
                    veh_list_this_train.append(int(i_veh_type))
                veh_matrix.append(veh_list_this_train)
                train_num_read += 1
                veh_num_read += veh_num_this_train
            line_num_for_train_def = train_num_read + veh_num_read + 1
            # 3.第二批控制参数：运营组织
            train_operation_para = get_data_from_fileline(dat_text[line_num_for_train_def])
            train_num_on_way, speed_num_on_way = int(train_operation_para[0]), int(train_operation_para[1])
            # 4.根据控制参数，读取上道车的运营组织情况
            # train_on_way_num_read = 0
            org_matrix = []
            for i_train_on_way in range(1, train_num_on_way + 1):
                i_org_matrix = []
                line_idx_way_no_this_train = line_num_for_train_def + 6 * (i_train_on_way - 1) + 1
                i_org_matrix.append(get_data_from_fileline(dat_text[line_idx_way_no_this_train]))
                # org_matrix[i_train_on_way - 1][0][0:2] = get_data_from_fileline(dat_text[line_idx_way_no_this_train])
                for j_speed in range(0, speed_num_on_way):
                    j_org_matrix = []
                    for k_para in range(0, 5):
                        if speed_num_on_way > 1:
                            para2append = get_data_from_fileline(dat_text[line_idx_way_no_this_train + k_para + 1])[
                                j_speed]
                        else:
                            para2append = get_data_from_fileline(dat_text[line_idx_way_no_this_train + k_para + 1])
                        j_org_matrix.append(para2append)
                    i_org_matrix.append(j_org_matrix)
                org_matrix.append(i_org_matrix)
            # 5.根据读取的信息，定义实例
            self.define(veh_matrix, train_name_vec, org_matrix)

    @staticmethod
    def veh_matrix_verify(veh_matrix):
        veh_matrix_verified = veh_matrix
        veh_num_each_train = []
        for i_train in veh_matrix_verified:
            veh_num_each_train.append(len(i_train))
        return veh_matrix_verified, veh_num_each_train

    @staticmethod
    def org_matrix_verify(org_matrix):
        org_matrix_verified = org_matrix
        return org_matrix_verified


class NonSpring:
    # 此类只负责读写桥梁结构的非线性弹簧，车辆上的非线性弹簧仅由开发人员内置于*_veh.dat中
    def __init__(self, non_spring_class_dict):
        self.non_spring_class_dict = non_spring_class_dict
        self.non_spring_class_para_num_dict = {}
        # 各个类型的非线性弹簧所需参数数量(指的是dat文件中的参数数量，包含了类型代码和本构参数，因此有+1)
        for i_class in self.non_spring_class_dict.keys():
            if i_class:  # i_class=0 代表无弹簧，0参数，仅在窗口中有用，不写入文件，此处直接跳过
                i_class_in_vbc = self.non_spring_class_dict[i_class][1]
                self.non_spring_class_para_num_dict[i_class_in_vbc] = len(self.non_spring_class_dict[i_class][2]) + 1

    def define(self, bri_spring_list, non_spring_name_vec):
        self.bri_spring_list = bri_spring_list
        self.non_spring_name_vec = non_spring_name_vec
        self.non_spring_num_bri = len(self.bri_spring_list)
        self.dof_nums_each_spring_bri = []
        para_nums_each_dof = []
        for i_spring in self.bri_spring_list:
            i_dof_num = 0
            for i_dof in i_spring:
                if i_dof:
                    para_nums_each_dof.append(self.non_spring_class_para_num_dict[i_dof[0]])
                    i_dof_num += 1
            self.dof_nums_each_spring_bri.append(i_dof_num)
        if para_nums_each_dof:
            self.max_para_num_bri = max(para_nums_each_dof)
        else:
            self.max_para_num_bri = 0

    def write_dat(self, dat_path):
        # 一、仅包含桥梁的
        filename1 = path_verify(dat_path) + "NonlinearSpringParameters_Bridge.dat"
        f_nsb = open(filename1, 'w', errors='ignore')
        # os.chmod(filename1, 0o777)
        # print('ns file1 opened')
        if self.non_spring_num_bri:
            # 1.控制参数
            f_nsb.write(str(self.non_spring_num_bri) + ',' + str(self.max_para_num_bri) + '\n\n\n')
            # 2.逐个弹簧输出
            i = 0
            for i_spring in self.bri_spring_list:
                print(i_spring)
                i_dof_num = self.dof_nums_each_spring_bri[i]
                f_nsb.write(str(i + 1) + ',' + str(i_dof_num) + ' !' + self.non_spring_name_vec[i] + '\n')
                i += 1
                for j_dof in range(0, 6):
                    if i_spring[j_dof]:
                        # 先输出该自由度的控制参数
                        f_nsb.write(str(j_dof + 1) + ',' + str(len(i_spring[j_dof])) + '\n')
                        # 再输出该自由度的具体参数取值
                        i_spring[j_dof][0] = int(i_spring[j_dof][0])
                        j_para_str = list(map(str, i_spring[j_dof]))
                        f_nsb.write(','.join(j_para_str) + '\n')
                f_nsb.write('\n')
        f_nsb.close()
        # 二、把车辆弹簧复制到目标目录下，仅用于计算，后期不读取
        # copy_cmd = 'copy .\\NonlinearSpringParameters_Vehicletypes.dat ' + path_verify(dat_path) + 'NonlinearSpringParameters_Vehicletypes.dat'
        # subprocess.Popen(copy_cmd, shell=True)
        source = '.\\NonlinearSpringParameters_Vehicletypes.dat'
        target = path_verify(dat_path)
        shutil.copy(source, target)

    def read_dat(self, dat_path):
        # 只读取桥梁弹簧，车辆弹簧封装在安装目录下，不对用户开放
        filename = path_verify(dat_path) + "NonlinearSpringParameters_Bridge.dat"
        # with open(filename, "r", errors='ignore') as f_nsb:
        with open(filename, "r") as f_nsb:
            # os.chmod(filename, 0o777)
            dat_text = skip_blank_lines(f_nsb.readlines())  # 读取文件所有行，并进行预处理，每个有效行均为list的一个元素
            # 1.第一行控制参数：弹簧数量、最大参数数量
            non_spring_def_para = get_data_from_fileline(dat_text[0])
            non_spring_num_bri, max_para_num_bri = int(non_spring_def_para[0]), int(non_spring_def_para[1])
            # 2.逐个弹簧读取
            bri_spring_list = []
            non_spring_name_vec = []
            line_idx_i_spring = 1  # 第i个弹簧的第一行所在行号(python规则，首行为0)
            # for i_spring in range(1, non_spring_num_bri+1):
            # vbc内核已经支持弹簧不连续编号，但只要读进窗口，就会变成从1开始连续编号
            self.non_spring_id_in_dat = []  # 需要依次记录dat文件中各个弹簧的编号，方便msb文件读取时识别
            while line_idx_i_spring + 1 <= len(dat_text):
                # print(line_idx_i_spring, len(dat_text))
                i_id_in_dat = get_data_from_fileline(dat_text[line_idx_i_spring])[0]
                self.non_spring_id_in_dat.append(i_id_in_dat)
                i_dof_num = get_data_from_fileline(dat_text[line_idx_i_spring])[1]
                current_line_idx = line_idx_i_spring + 1  # 第i个弹簧的第j个自由度的第一行
                non_spring_name_vec.append(get_denotation_from_fileline(dat_text[line_idx_i_spring]))
                i_spring_data = [[], [], [], [], [], []]
                i_dof_num_read = 0
                for j_dof in range(1, 7):
                    if i_dof_num_read < i_dof_num:
                        j_dof_id = get_data_from_fileline(dat_text[current_line_idx])[0]
                        if j_dof_id == j_dof:
                            i_spring_data[j_dof - 1] = get_data_from_fileline(dat_text[current_line_idx + 1])
                            current_line_idx += 2
                            i_dof_num_read += 1
                bri_spring_list.append(i_spring_data)
                line_idx_i_spring = current_line_idx  # 把行号指针跳到下一个弹簧的第一行
        self.define(bri_spring_list, non_spring_name_vec)


class SubVeh:
    """
    暂时仅支持读取车辆编号、名称、车轮数
    """

    def write_dat(self, dat_path):
        # 零、复制文件
        # copy_cmd = 'copy .\\Modal_Substructure_Vehicletypes.dat ' + path_verify(dat_path) + 'Modal_Substructure_Vehicletypes.dat'
        # subprocess.Popen(copy_cmd, shell=True)
        source = '.\\Modal_Substructure_Vehicletypes.dat'
        target = path_verify(dat_path)
        shutil.copy(source, target)

    def read_dat(self, dat_path):
        file_name = path_verify(dat_path) + 'Modal_Substructure_Vehicletypes.dat'
        # with open(file_name, 'r', errors='ignore') as f_msv:
        with open(file_name, 'r') as f_msv:
            # os.chmod(file_name, 0o777)
            """
            搜索所有!，并从所在行读取车辆的编号、名称、车轮数
            """
            self.vehicle_type_dict = {}
            dat_text = skip_blank_lines(f_msv.readlines())  # 读取文件所有行，并进行预处理，每个有效行均为list的一个元素
            for i_line in dat_text:
                i_name = get_denotation_from_fileline(i_line)
                if i_name != '未命名':
                    i_veh_id = int(get_data_from_fileline(i_line)[0])
                    i_wheel_num = int(get_data_from_fileline(i_line)[2])  # 轮子数，不是轮对数
                    # 根据车辆名称判断客货
                    if i_name.find('货') == -1:
                        i_if_locomotive = False
                    else:
                        i_if_locomotive = True
                    self.vehicle_type_dict[i_veh_id] = [i_name, i_wheel_num, i_if_locomotive]


class WindCoe:
    def __init__(self):
        pass

    def define(self, air_dens, ave_wind_speed, wind_direction_in_rad, wind_field_start_x,
               consider_fluctuating, roughness, reference_altitude, deck_altitude, space_pt_num, space_length,
               max_freq, random_seed, last_time, smooth_dist, smooth_time,
               wind_coe_dict_bri, wind_node_group_dict, wind_load_assign_list_bri,
               wind_coe_dict_veh, wind_field_ctrl_pt, wind_load_assign_list_veh):
        self.air_dens = air_dens
        self.ave_wind_speed = ave_wind_speed
        self.wind_direction_in_rad = wind_direction_in_rad
        self.wind_field_start_x = wind_field_start_x
        self.consider_fluctuating = consider_fluctuating
        self.roughness = roughness
        self.reference_altitude = reference_altitude
        self.deck_altitude = deck_altitude
        self.space_pt_num = space_pt_num
        self.space_length = space_length
        self.max_freq = max_freq
        self.random_seed = random_seed
        self.last_time = last_time
        self.smooth_dist = smooth_dist
        self.smooth_time = smooth_time
        self.wind_coe_dict_bri = wind_coe_dict_bri
        self.wind_node_group_dict = wind_node_group_dict
        self.wind_load_assign_list_bri = wind_load_assign_list_bri
        self.wind_coe_dict_veh = wind_coe_dict_veh
        self.wind_field_ctrl_pt = wind_field_ctrl_pt
        self.wind_load_assign_list_veh = wind_load_assign_list_veh

        # 风荷载系数及其id的对应关系：先零荷载，再桥，最后车
        self.wind_coe_total_idx_dict = {'无风荷载': 1}
        i_wind_coe_idx = 1  # 1号留给零荷载
        for i_coe_name in self.wind_coe_dict_bri.keys():
            i_wind_coe_idx = i_wind_coe_idx + 1
            self.wind_coe_total_idx_dict[i_coe_name] = i_wind_coe_idx
        for i_coe_name in self.wind_coe_dict_veh.keys():
            i_wind_coe_idx = i_wind_coe_idx + 1
            self.wind_coe_total_idx_dict[i_coe_name] = i_wind_coe_idx

    def write_dat(self, dat_path):
        filename = path_verify(dat_path) + "Wind_Coefficients.dat"
        f_wind = open(filename, 'w')
        # os.chmod(filename, 0o777)
        # 第一行控制参数
        paras_line_1 = [self.air_dens, self.ave_wind_speed, self.wind_direction_in_rad]
        paras_str_line_1 = [str(i) for i in paras_line_1]
        text_line_1 = '\t'.join(paras_str_line_1) + '\t!空气密度、平均风速、风向（与车辆坐标系Z轴夹角的弧度值）'
        f_wind.write(text_line_1 + '\n')
        # 第二行控制参数
        f_wind.write(str(self.wind_field_start_x) + '\t!风荷载开始的纵坐标X\n')
        # 第三行控制参数
        f_wind.write(str(self.consider_fluctuating) + '\t!是否考虑脉动风效应\n')
        # 第四行控制参数
        paras_line_4 = [self.roughness, self.reference_altitude, self.deck_altitude,
                        self.space_pt_num, self.space_length,
                        self.max_freq, self.random_seed, self.last_time, self.smooth_dist, self.smooth_time]
        paras_str_line_4 = [str(i) for i in paras_line_4]
        text_line_4 = '\t'.join(paras_str_line_4) + \
                      '\t!脉动风参数 (粗糙度、基准高度、桥面高度、空间点数、空间距离、最高频率、随机种子、持续时间、平滑处理距离、时间'
        f_wind.write(text_line_4 + '\n\n\n')
        # 第五行：风荷载系数总数，先零荷载，再桥，最后车
        wind_coe_total_num = 1 + len(self.wind_coe_dict_bri) + len(self.wind_coe_dict_veh)
        # 第六行开始：风荷载系数罗列，先零荷载，再桥，最后车
        zero_wind_coe_text = '1\t1\t1\t!无风荷载\n' + '1\n0\n1\n0\n1\n0\n1\n0\n1\n0\n1\n0\n' + '\n'
        bri_wind_coe_text = ''
        for i_coe_bri in self.wind_coe_dict_bri.keys():
            i_length_paras = self.wind_coe_dict_bri[i_coe_bri][0]
            i_length_paras_str = [str(i) for i in i_length_paras]
            i_length_paras_text = '\t'.join(i_length_paras_str) + '\t!' + i_coe_bri + '\n'
            bri_wind_coe_text = bri_wind_coe_text + i_length_paras_text
            for j_dof in range(0, 6):
                j_order_coes = self.wind_coe_dict_bri[i_coe_bri][j_dof + 1]
                j_order_coes_str = [str(i) for i in j_order_coes]
                j_order_coes_text = '\t'.join(j_order_coes_str)
                j_order_num = len(j_order_coes)
                j_paras_text = str(j_order_num) + '\n' + j_order_coes_text + '\n'
                bri_wind_coe_text = bri_wind_coe_text + j_paras_text
            bri_wind_coe_text = bri_wind_coe_text + '\n'
        veh_wind_coe_text = ''
        for i_coe_veh in self.wind_coe_dict_veh.keys():
            i_length_paras = self.wind_coe_dict_veh[i_coe_veh][0]
            i_length_paras_str = [str(i) for i in i_length_paras]
            i_length_paras_text = '\t'.join(i_length_paras_str) + '\t!' + i_coe_veh + '\n'
            veh_wind_coe_text = veh_wind_coe_text + i_length_paras_text
            for j_dof in range(0, 6):
                j_order_coes = self.wind_coe_dict_veh[i_coe_veh][j_dof + 1]
                j_order_coes_str = [str(i) for i in j_order_coes]
                j_order_coes_text = '\t'.join(j_order_coes_str)
                j_order_num = len(j_order_coes)
                j_paras_text = str(j_order_num) + '\n' + j_order_coes_text + '\n'
                veh_wind_coe_text = veh_wind_coe_text + j_paras_text
            veh_wind_coe_text = veh_wind_coe_text + '\n'
        f_wind.write(str(wind_coe_total_num) + '\n\n' + zero_wind_coe_text + bri_wind_coe_text + veh_wind_coe_text)
        # 车道沿线风场控制点
        ctrl_pt_num = len(self.wind_field_ctrl_pt)
        ctrl_pt_num_text = str(ctrl_pt_num) + '\t!车辆所受风力系数沿着桥梁纵向的控制点数\n'
        ctrl_pt_str = [str(i) for i in self.wind_field_ctrl_pt]
        ctrl_pt_text = '\t'.join(ctrl_pt_str) + '\t!风力系数沿着桥梁纵向的控制点X坐标\n'
        f_wind.write(ctrl_pt_num_text + ctrl_pt_text + '\n')
        # 车辆风荷载分配
        veh_wind_coe_assign_text = ''
        for i_train_coe_list in self.wind_load_assign_list_veh:
            for j_veh_coe_list in i_train_coe_list:
                j_coe_id_str = [str(self.wind_coe_total_idx_dict[i]) for i in j_veh_coe_list]
                j_coe_id_text = '\t'.join(j_coe_id_str) + '\n'
                veh_wind_coe_assign_text = veh_wind_coe_assign_text + j_coe_id_text
        f_wind.write(veh_wind_coe_assign_text + '\n')
        # 结构风荷载分配
        bri_wind_node_group_num = len(self.wind_node_group_dict)
        bri_wind_node_nums_each_group = [len(i) for i in self.wind_node_group_dict.values()]
        if bri_wind_node_nums_each_group:
            max_bri_wind_node_num_each_group = max(bri_wind_node_nums_each_group)
        else:
            max_bri_wind_node_num_each_group = 0
        bri_wind_coe_assign_text = str(bri_wind_node_group_num) + '\t' + str(max_bri_wind_node_num_each_group) + '\n'
        for i_group in range(0, len(self.wind_node_group_dict)):
            i_coe_name = self.wind_load_assign_list_bri[i_group]
            i_coe_id = self.wind_coe_total_idx_dict[i_coe_name]
            i_node_num = bri_wind_node_nums_each_group[i_group]
            i_group_name = list(self.wind_node_group_dict.keys())[i_group]
            bri_wind_coe_assign_text = bri_wind_coe_assign_text + str(i_coe_id) + '\t' + str(i_node_num) \
                                       + '\t!' + i_group_name + '\n'
            for j_node in self.wind_node_group_dict[i_group_name]:
                bri_wind_coe_assign_text = bri_wind_coe_assign_text + str(int(j_node)) + '\n'
            bri_wind_coe_assign_text = bri_wind_coe_assign_text + '\n'
        f_wind.write(bri_wind_coe_assign_text)
        f_wind.close()

    def read_dat(self, dat_path):
        filename = path_verify(dat_path) + "Wind_Coefficients.dat"
        try:
            f_wind = open(filename, 'r')
            # os.chmod(filename, 0o777)
            dat_text = skip_blank_lines(f_wind.readlines())  # 读取文件所有行，并进行预处理，每个有效行均为list的一个元素
            f_wind.close()
        except:
            dat_text = ''
        if dat_text:
            # 1.第一行控制参数
            paras_line_1 = get_data_from_fileline(dat_text[0])
            air_dens, ave_wind_speed, wind_direction_in_rad = paras_line_1[0], paras_line_1[1], paras_line_1[2]
            # 2.第二行
            wind_field_start_x = get_data_from_fileline(dat_text[1])
            # 3.第三行
            consider_fluctuating = int(get_data_from_fileline(dat_text[2]))
            # 4.第四行
            paras_line_4 = get_data_from_fileline(dat_text[3])
            roughness, reference_altitude, deck_altitude = paras_line_4[0], paras_line_4[1], paras_line_4[2]
            space_pt_num, space_length = int(paras_line_4[3]), paras_line_4[4]
            max_freq, random_seed, last_time = paras_line_4[5], int(paras_line_4[6]), paras_line_4[7]
            smooth_dist, smooth_time = paras_line_4[8], paras_line_4[9]
            # 5.风力系数读取，关键任务：要将零荷载、桥上荷载、车上荷载分开
            wind_coe_dict_bri = {}
            wind_coe_dict_veh = {}
            wind_coe_rev_dict_total = {}  # 记录当前读取的dat文件中的系数组序号及名称的对应关系，方便后续读取assign到各个位置的风荷载名称
            wind_coe_total_num_in_dat = int(get_data_from_fileline(dat_text[4]))
            for i_group in range(0, wind_coe_total_num_in_dat):
                i_line_idx_length_paras = 5 + 13*i_group
                i_coe_list = [get_data_from_fileline(dat_text[i_line_idx_length_paras])]
                i_group_name = get_denotation_from_fileline(dat_text[i_line_idx_length_paras])
                for j_dof in range(1, 7):
                    j_order_num = int(get_data_from_fileline(dat_text[i_line_idx_length_paras+2*j_dof-1]))
                    if j_order_num == 1:
                        j_coes = [get_data_from_fileline(dat_text[i_line_idx_length_paras+2*j_dof])]
                    else:
                        j_coes = get_data_from_fileline(dat_text[i_line_idx_length_paras+2*j_dof])
                    i_coe_list.append(j_coes)
                wind_coe_rev_dict_total[i_group+1] = i_group_name
                if i_coe_list[1:7] == [[0], [0], [0], [0], [0], [0]]:
                    continue  # 零荷载不需要用户定义，因此不予读取，最后define的时候直接就内置了
                elif i_coe_list[0][3] == 1:  # 根据车桥识别码判定风荷载属于谁：桥1车0
                    wind_coe_dict_bri[i_group_name] = i_coe_list
                else:
                    wind_coe_dict_veh[i_group_name] = i_coe_list
            # 6.车道沿线风场控制点读取
            line_idx_ctrl_pt_num = 5 + 13*wind_coe_total_num_in_dat
            ctrl_pt_num = int(get_data_from_fileline(dat_text[line_idx_ctrl_pt_num]))
            if ctrl_pt_num:
                wind_field_ctrl_pt = get_data_from_fileline(dat_text[line_idx_ctrl_pt_num+1])
                if ctrl_pt_num == 1:
                    wind_field_ctrl_pt = [wind_field_ctrl_pt]
            else:
                wind_field_ctrl_pt = []
            # 7.车辆荷载分配读取，必须有VehOrg加以配合
            veh_org = VehOrg()
            veh_org.read_dat(dat_path)
            veh_num_list = [len(i) for i in veh_org.veh_matrix_verified]
            train_on_way_id_in_vbc = [int(i[0][0]) for i in veh_org.org_matrix_verified]
            i_line_idx_wind_assign_veh = line_idx_ctrl_pt_num + 2
            wind_load_assign_list_veh = []
            for i_train_ow in train_on_way_id_in_vbc:
                i_veh_num = veh_num_list[i_train_ow-1]
                i_coe_list = []
                if ctrl_pt_num:  # 如果没有定义风场控制点，则车辆上一定没有风力系数，文件中对应行全空，就不要读了
                    for j_veh in range(0, i_veh_num):
                        j_coe_id_list = get_data_from_fileline(dat_text[i_line_idx_wind_assign_veh])
                        print(j_coe_id_list)
                        if (type(j_coe_id_list) == int) or (type(j_coe_id_list) == float):
                            print(j_coe_id_list)
                            j_coe_id_list = [j_coe_id_list]
                        print(j_coe_id_list)
                        j_coe_name_list = [wind_coe_rev_dict_total[i] for i in j_coe_id_list]
                        i_coe_list.append(j_coe_name_list)
                        i_line_idx_wind_assign_veh = i_line_idx_wind_assign_veh + 1
                wind_load_assign_list_veh.append(i_coe_list)
            # 8.结构受风荷载结点组及荷载分配信息读取
            line_idx_wind_node_group_num = i_line_idx_wind_assign_veh
            wind_node_group_num = int(get_data_from_fileline(dat_text[line_idx_wind_node_group_num][0]))
            wind_node_group_dict = {}
            wind_load_assign_list_bri = []
            line_idx_i_group_name = line_idx_wind_node_group_num + 1
            for i_group in range(0, wind_node_group_num):
                i_group_name = get_denotation_from_fileline(dat_text[line_idx_i_group_name])
                print(get_data_from_fileline(dat_text[line_idx_i_group_name]))
                i_coe_id, i_node_num = int(get_data_from_fileline(dat_text[line_idx_i_group_name])[0]), int(get_data_from_fileline(dat_text[line_idx_i_group_name])[1])
                i_coe_name = wind_coe_rev_dict_total[i_coe_id]
                wind_load_assign_list_bri.append(i_coe_name)
                i_node_list = []
                for j_node in range(0, i_node_num):
                    line_idx_j_node = line_idx_i_group_name + j_node + 1
                    j_node_id = get_data_from_fileline(dat_text[line_idx_j_node])
                    i_node_list.append(j_node_id)
                line_idx_i_group_name = line_idx_i_group_name + len(i_node_list) + 1
                wind_node_group_dict[i_group_name] = i_node_list
        else:
            air_dens = 1.25
            ave_wind_speed = 0.0
            wind_direction_in_rad = 0.0
            wind_field_start_x = 0.0
            consider_fluctuating = 0
            roughness = 0.00
            reference_altitude = 10.0
            deck_altitude = 0.0
            space_pt_num = 0
            space_length = 1.0
            max_freq = 0.0
            random_seed = 1
            last_time = 0.0
            smooth_dist = 0.0
            smooth_time = 0.0
            wind_coe_dict_bri = {}
            wind_node_group_dict = {}
            wind_load_assign_list_bri = []
            wind_coe_dict_veh = {}
            wind_field_ctrl_pt = []
            wind_load_assign_list_veh = []
        self.define(air_dens, ave_wind_speed, wind_direction_in_rad, wind_field_start_x,
                    consider_fluctuating, roughness, reference_altitude, deck_altitude, space_pt_num, space_length,
                    max_freq, random_seed, last_time, smooth_dist, smooth_time,
                    wind_coe_dict_bri, wind_node_group_dict, wind_load_assign_list_bri,
                    wind_coe_dict_veh, wind_field_ctrl_pt, wind_load_assign_list_veh)


class ExtForce:
    def define(self, node_dof_list, force_time_hist_list):
        self.node_dof_list = node_dof_list  # [[node, dof], [node, dof], [node, dof], ...]
        self.force_time_hist_list = force_time_hist_list  # [[[t1, f1], [t2, f2], ...], [], [], ...]
        self.dof_total_num = len(self.node_dof_list)
        self.pt_num_list = [len(i) for i in self.force_time_hist_list]
        if self.pt_num_list:
            self.max_pt_num = max(self.pt_num_list)
        else:
            self.max_pt_num = 0

    def write_dat(self, dat_path):
        filename = path_verify(dat_path) + 'ExternalForces.dat'
        f_ext_force = open(filename, 'w')
        # os.chmod(filename, 0o777)
        if len(self.node_dof_list):
            # 第一行控制参数
            f_ext_force.write(str(self.dof_total_num) + '\t!几个节点上需要施加地震力\n\n')
            # 逐个自由度输出力的时程
            for i_dof in range(0, self.dof_total_num):
                # 第i个节点的第一行控制参数
                i_paras_str_line_1 = [str(self.node_dof_list[i_dof][0]), str(self.node_dof_list[i_dof][1]), '1']
                i_text_line_1 = '\t'.join(i_paras_str_line_1) + '\t!节点号，力的方向，力的类型：1为时程\n'
                f_ext_force.write(i_text_line_1)
                # 第i个节点的第二行控制参数
                i_paras_str_line_2 = [str(self.max_pt_num), str(self.pt_num_list[i_dof])]
                i_text_line_2 = '\t'.join(i_paras_str_line_2) + '\t!时程数据点的最大个数，本节点上力的时程数据点数目\n'
                f_ext_force.write(i_text_line_2)
                # 第i个节点荷载的时程
                for j_pt in range(0, self.pt_num_list[i_dof]):
                    j_time = str(self.force_time_hist_list[i_dof][j_pt][0])
                    j_force = str(self.force_time_hist_list[i_dof][j_pt][1])
                    j_text = j_time + '\t' + j_force + '\n'
                    f_ext_force.write(j_text)
                f_ext_force.write('\n')
        else:
            f_ext_force.write('')
        f_ext_force.close()

    def read_dat(self, dat_path):
        filename = path_verify(dat_path) + 'ExternalForces.dat'
        f_ext_force = open(filename, 'r')
        # os.chmod(filename, 0o777)
        dat_text = skip_blank_lines(f_ext_force.readlines())  # 读取文件所有行，并进行预处理，每个有效行均为list的一个元素
        if dat_text:
            # 第一行控制参数
            dof_total_num = int(get_data_from_fileline(dat_text[0]))
            # 逐个自由度读取外力作用点及时程
            pt_num_read = 0  # 已读到的时间点总数，用于给当前行计数
            node_dof_list = []
            force_time_hist_list = []
            for i_dof in range(0, dof_total_num):
                # 第i个自由度的第一行控制参数
                idx_line_i1 = pt_num_read + i_dof*2 + 1
                paras_line_i1 = get_data_from_fileline(dat_text[idx_line_i1])
                i_node = int(paras_line_i1[0])
                i_dof_id = int(paras_line_i1[1])
                node_dof_list.append([i_node, i_dof_id])
                # 第i个自由度的第二行控制参数
                idx_line_i2 = pt_num_read + i_dof*2 + 2
                paras_line_i2 = get_data_from_fileline(dat_text[idx_line_i2])
                i_pt_num = int(paras_line_i2[1])
                print(idx_line_i1, idx_line_i2)
                # 第i个自由度的外力时程数据
                force_time_hist_list.append([])
                for j_pt in range(0, i_pt_num):
                    force_time_hist_list[i_dof].append([])
                    idx_line_ij = idx_line_i1 + j_pt + 2
                    paras_line_ij = get_data_from_fileline(dat_text[idx_line_ij])
                    j_time = paras_line_ij[0]
                    j_force = paras_line_ij[1]
                    force_time_hist_list[i_dof][j_pt] = [j_time, j_force]
                    pt_num_read += 1
        else:
            node_dof_list = []
            force_time_hist_list = []
        f_ext_force.close()
        self.define(node_dof_list, force_time_hist_list)

