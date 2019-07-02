#!/usr/bin/env python
# encoding: utf-8

from urllib import request
from urllib import error
from pathlib import Path
import re
import gzip
import time
import random
import db
import antiobfuscate


# settings
# dddddd
# 第二次修改
# 第三次修改
url_domain = 'https://www.autohome.com.cn/'
url_series = url_domain + '%s/'
url_spec = url_domain + 'spec/%s/'
url_config = 'https://car.autohome.com.cn/config/series/%s.html'
urls = (
    'a00/',     # 微型车
    'a0/',      # 小型车
    'a/',       # 紧凑型车
    'b/',       # 中型车
    'c/',       # 中大型车
    'd/',       # 大型车fff
    'suva0/',   # 小型SUV
    'suva/',    # 紧凑型SUV
    'suvb/',    # 中型SUV
    'suvc/',    # 中大型SUV
    'suvd/',    # 大型SUV
    'mpv/',     # MPV
    's/',       # 跑车
    'p/',       # 皮卡
    # 'mb/',      # 微面
    # 'qk/',      # 轻客
)
time_interval_min = 10
time_interval_max = 20
headers = {
    "Accept-Encoding": "gzip",
    "Cache-Control": "max-age=0",
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36',
    "Accept-Language": "zh-CN,zh;q=0.8,en;q=0.6,en-US;q=0.4,zh-TW;q=0.2",
    "Connection": "keep-alive",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "referer": url_domain
}

# 各类搜索用正则表达式
# 车系列表页 - 所有车系编号  跳过所有含有 class="greylink" 的车系
pattern_series_ids = re.compile(r'www.autohome.com.cn/(\d+)/#levelsource=[^"]+"(?!\sclass="greylink")>[^<]')
# 车系配置页 - 车系
pattern_series_name = re.compile(r'<title>【(.+)参数配置表】')
# 车系配置页 - 官方配置表
pattern_official_config = re.compile(r'a id="btnDownLoadConfig" href="([^"]+)"')

# 车系配置页 - 基本参数
pattern_config = re.compile(r'var config =(.+)')
# 基本参数 - 所有参数
pattern_config_params = re.compile(r'{"id":(\d+),"name":"([^"]+)","pnid":"([^"]+)",(.*?)}]}')
# 基本参数 - 每参数所有车型的值
pattern_config_specs = re.compile(r'"specid":(\d+),"value":"([^"]+)"')

# 车系配置页 - 配置
pattern_config_option = re.compile(r'var option =(.+)')
# 配置 - 所有参数
pattern_config_option_params = re.compile(r'{"name":"([^"]+)",(.*?),"id":(\d+),"pnid":"([^"]+)"')
# 配置 - 每参数所有车型的值
pattern_config_option_specs = re.compile(r'"specid":(\d+),("price":\[{"price":(\d+),"subname":"[^"]*"}\],)?"value":"([^"]+)"')

# 车系配置页 - 外观颜色
pattern_config_color = re.compile(r'var color =(.+)')
# 外观颜色 - 所有车型
pattern_config_color_specs = re.compile(r'"specid":(\d+),"coloritems":(.*?)}]}')
# 外观颜色 - 各车型所有颜色
pattern_config_color_colors = re.compile(r'"name":"([^"]+)"')

# 车系配置页 - 内饰颜色
pattern_config_innerColor = re.compile(r'var innerColor =(.+)')

# 车系配置页 - 选装包
pattern_config_bag = re.compile(r'var bag =(.+)')
# 选装包 - 所有选装包
pattern_config_bag_bags = re.compile(r'"price":(\d+),"name":"([^"]+)",(.*?),"description":"([^"]+)","id":\d+')
# 选装包 - 各选装包所有车型的值
pattern_config_bag_specs = re.compile(r'"specid":(\d+),"value":"([^"]+)"')


# 所有车系编号
series_ids = ['341']  # 341 是雷克萨斯LS，因为配置项最齐全，因此首先获取以便得到正确的列顺序
# 数据库中已有的列名
columns_done = ''
# 数据库中已处理的车系编号列表
series_ids_done = []
# 新增的列名列表，每一项是一个 tuple，格式：('item_100', '上市时间')
columns_todo = []
# 当前车系中出现的所有列名
columns_current = []


def get_list_index_by_specid(list_specs, spec_id):
    for i in range(len(list_specs)):
        if list_specs[i][4] == spec_id:
            return i
    return -1


# 价格处理
def get_price(origin_word):
    i = origin_word.find('万')
    if i >= 0:
        return origin_word[0:i]
    else:
        return origin_word


def get_simple_word(origin_word):
    return origin_word.replace('"', '”').replace('&nbsp;', '')


# 添加列 当添加该车系已经添加过的列时返回 False，否则返回 True
def add_column(item_id, item_name):
    global columns_done
    if item_id in columns_current:
        return False
    columns_current.append(item_id)
    if columns_done.find(item_id + ' ') < 0 and columns_done.find(item_id + ']') < 0:
        columns_todo.append((item_id, get_simple_word(item_name)))
        columns_done = columns_done + item_id + ' '
    return True


# 找到所有车系编号
def get_series_ids():
    global series_ids

    for url in urls:
        req = request.Request(url_domain + url)
        req.headers = headers

        try:
            res = request.urlopen(req)
            content = gzip.decompress(res.read()).decode('gb2312', 'ignore')
            ids = pattern_series_ids.findall(content)
            # 去重
            ids = sorted(set(ids), key=ids.index)
            series_ids = series_ids + ids
            print('在 %s 下找到 %d 个车系' % (url, len(ids)))
        except error.HTTPError as e:
            print('series_ids request error:' + e.code)

    # 再次去重
    series_ids = sorted(set(series_ids), key=series_ids.index)
    print('一共找到 %d 个车系' % len(series_ids))


# 抓取车系配置
def get_configs():
    global columns_todo, columns_current
    
    count_series = len(series_ids)
    count_index = 0
    count_series_done = 0
    count_specs_done = 0

    # 循环抓取所有车系配置
    for series_id in series_ids:
        count_index = count_index + 1
        print('开始处理车系 %s 进度：%d/%d ' % (series_id, count_index, count_series))
        
        if series_id in series_ids_done:
            # 该车系已经处理过，跳过
            continue

        # 每个车系下各车型的配置数据列表，每个元素又是一个 list，代表一个车型
        list_specs = []
        # 跟上面的列表一一对应，存储对应车型的列名
        list_specs_columns = []
        # 初始化列表
        columns_todo = []
        columns_current = ['series_id', 'series_link', 'series_name', 'official_config', 'spec_id', 'spec_link']
        # 该车系下的车型数量
        count_spec = 0

        req = request.Request(url_config % series_id)
        req.headers = headers
        # 每个车系之间间隔若干秒
        time.sleep(random.randint(time_interval_min, time_interval_max))
        try:
            res = request.urlopen(req)
            content = gzip.decompress(res.read()).decode('utf-8')
            # 反混淆
            content = antiobfuscate.get_complete_text(content)

            # 车系
            match = pattern_series_name.search(content)
            series_name = match.group(1).replace('"', '”')
            # 官方配置表
            match = pattern_official_config.search(content)
            if match:
                official_config_link = match.group(1)
            else:
                official_config_link = ''
            # 基本参数
            match = pattern_config.search(content)
            if not match:
                # 该车系下没有车型数据 插入一条空数据用于记录
                db.db_insert_nodata(series_id, url_series % series_id, series_name)
                continue
            str_config = match.group(1)
            # 配置
            match = pattern_config_option.search(content)
            if not match:
                print('车系 %s 中没有配置数据' % series_id)
                continue
            str_config_option = match.group(1)
            # 外观颜色
            match = pattern_config_color.search(content)
            if not match:
                print('车系 %s 中没有外观颜色数据' % series_id)
                continue
            str_config_color = match.group(1)
            # 内饰颜色
            match = pattern_config_innerColor.search(content)
            if not match:
                print('车系 %s 中没有内饰颜色数据' % series_id)
                continue
            str_config_inner_color = match.group(1)
            # 选装包
            match = pattern_config_bag.search(content)
            if not match:
                print('车系 %s 中没有选装包数据' % series_id)
                continue
            str_config_bag = match.group(1)

            # 基本参数
            config_params = pattern_config_params.findall(str_config)
            for one_config_param in config_params:
                item_id = 'item_' + one_config_param[0]
                item_name = one_config_param[1]

                # 针对 item_id 为 0 的特殊处理
                if item_id == 'item_0':
                    if item_name == '能源类型':
                        item_id = 'energy_type'
                    elif item_name == '上市时间':
                        item_id = 'sell_date'
                    elif item_name == '纯电续航里程':
                        # 跟【工信部续航里程(km)】相同
                        item_id = 'item_1013'
                    elif item_name == '变速箱':
                        item_id = 'gear_box'
                    elif item_name == '后排车门开启方式':
                        item_id = 'back_door_open'
                    elif item_name == '货箱尺寸(mm)':
                        item_id = 'cargo_size'
                    elif item_name == '最大载重质量(kg)':
                        item_id = 'max_load'
                    elif item_name == '排量(L)':
                        item_id = 'displacement_L'
                    elif item_name == '电机类型':
                        item_id = 'e_engine_type'
                    elif item_name == '系统综合功率(kW)':
                        item_id = 'system_power_sum'
                    elif item_name == '系统综合扭矩(N·m)':
                        item_id = 'system_torque_sum'
                    elif item_name == '驱动电机数':
                        item_id = 'e_engine_num'
                    elif item_name == '电机布局':
                        item_id = 'e_engine_layout'
                    elif item_name == '电池类型':
                        item_id = 'battery_type'
                    elif item_name == '百公里耗电量(kWh/100km)':
                        item_id = 'power_use'
                    elif item_name == '电池组质保':
                        item_id = 'battery_quality'
                    elif item_name == '电池充电时间':
                        item_id = 'battery_charge_time'
                    elif item_name == '快充电量(%)' or item_name == '快充电量百分比':
                        item_id = 'quick_charge'
                    elif item_name == '充电桩价格':
                        item_id = 'charger_price'
                    elif item_name == '电动机':
                        # 重复字段，跳过
                        continue
                    else:
                        print('车系 %s 中出现未知的 item_0，item_name：%s' % (series_id, item_name))
                        continue

                str_specs = one_config_param[3]
                if not add_column(item_id, item_name):
                    # 该参数已经添加过，跳过
                    continue
                config_specs = pattern_config_specs.findall(str_specs)
                if count_spec == 0:
                    count_spec = len(config_specs)
                if count_spec == 0:
                    print('该参数没有车型数据，车系：%s 基本参数：%s' % (series_id, item_id))
                    continue
                # 第一次执行循环时初始化 list_specs
                if len(list_specs) == 0:
                    # 有多少个车型，则添加多少个 list_specs 元素
                    for i in range(count_spec):
                        list_specs.append([])
                        list_specs_columns.append([])
                list_specs_index = 0
                for one_config_spec in config_specs:
                    spec_id = one_config_spec[0]
                    item_value = one_config_spec[1]
                    if item_id == 'item_219':
                        # 价格处理
                        item_value = get_price(item_value)
                    else:
                        item_value = get_simple_word(item_value)
                    one_spec = list_specs[list_specs_index]
                    one_column = list_specs_columns[list_specs_index]
                    if len(one_spec) == 0:
                        # 第一次添加车型数据时初始化列表
                        one_spec.append(series_id)
                        one_spec.append(url_series % series_id)
                        one_spec.append(series_name)
                        one_spec.append(official_config_link)
                        one_spec.append(spec_id)
                        one_spec.append(url_spec % spec_id)
                        one_column.extend(['series_id', 'series_link', 'series_name'])
                        one_column.extend(['official_config', 'spec_id', 'spec_link'])
                    elif one_spec[4] != spec_id:
                        print('spec_id 不符，车系：%s 基本参数：%s' % (series_id, item_id))
                        item_value = '#'
                    one_spec.append(item_value)
                    one_column.append(item_id)
                    list_specs_index = list_specs_index + 1
            
            if len(list_specs) == 0:
                print('车系 %s 下没有车型' % series_id)
                continue

            # 配置
            config_option_params = pattern_config_option_params.findall(str_config_option)
            for one_config_option_param in config_option_params:
                item_id = 'item_' + one_config_option_param[2]
                item_name = one_config_option_param[0]

                # 针对 item_id 为 0 的特殊处理
                if item_id == 'item_0':
                    if item_name == '疲劳驾驶提示':
                        item_id = 'tired_drive'
                    elif item_name == '自动驾驶技术':
                        item_id = 'auto_drive'
                    elif item_name == '上坡辅助':
                        item_id = 'up_assist'
                    elif item_name == '电磁感应悬架':
                        item_id = 'em_feel'
                    elif item_name == '多天窗':
                        item_id = 'multi_window'
                    elif item_name == '感应后备厢':
                        item_id = 'feel_rear_box'
                    elif item_name == '车顶行李架':
                        item_id = 'top_box'
                    elif item_name == '远程启动':
                        item_id = 'remote_start'
                    elif item_name == '皮质方向盘':
                        item_id = 'steeling_texture'
                    elif item_name == '方向盘记忆':
                        item_id = 'steeling_memory'
                    elif item_name == '全液晶仪表盘':
                        item_id = 'liquid_view'
                    elif item_name == '内置行车记录仪':
                        item_id = 'drive_recorder'
                    elif item_name == '主动降噪':
                        item_id = 'noise_down'
                    elif item_name == '手机无线充电':
                        item_id = 'remote_charge'
                    elif item_name == '座椅材质':
                        item_id = 'seat_texture'
                    elif item_name == '副驾驶位后排可调节按钮':
                        item_id = 'sub_driver_button'
                    elif item_name == '第二排独立座椅':
                        item_id = 'second_seat'
                    elif item_name == '可加热/制冷杯架':
                        item_id = 'heater_cup'
                    elif item_name == '中控台彩色大屏尺寸':
                        item_id = 'screen_size'
                    elif item_name == '手机互联/映射':
                        item_id = 'mobile_link'
                    elif item_name == '车联网':
                        item_id = 'car_net'
                    elif item_name == '220V/230V电源':
                        item_id = 'power_220v'
                    elif item_name == '外接音源接口':
                        item_id = 'audio_interface'
                    elif item_name == 'CD/DVD':
                        item_id = 'cd_dvd'
                    elif item_name == '近光灯':
                        item_id = 'low_beam'
                    elif item_name == '远光灯':
                        item_id = 'high_beam'
                    elif item_name == 'LED日间行车灯':
                        item_id = 'led_daylight'
                    elif item_name == '自适应远近光':
                        item_id = 'adapter_beam'
                    elif item_name == '转向头灯':
                        item_id = 'turn_beam'
                    elif item_name == '车窗一键升降':
                        item_id = 'one_touch_window'
                    elif item_name == '流媒体车内后视镜':
                        item_id = 'streaming_rear_mirror'
                    elif item_name == '车载空气净化器':
                        item_id = 'air_purifier'
                    else:
                        print('车系 %s 中出现未知的 item_0，item_name：%s' % (series_id, item_name))
                        continue

                str_specs = one_config_option_param[1]
                if not add_column(item_id, item_name):
                    # 该参数已经添加过，跳过
                    continue
                config_option_specs = pattern_config_option_specs.findall(str_specs)
                for one_config_option_spec in config_option_specs:
                    spec_id = one_config_option_spec[0]
                    item_price = one_config_option_spec[2]
                    item_value = get_simple_word(one_config_option_spec[3])
                    if item_price and item_price != '0':
                        item_value = item_value + '选装¥' + item_price
                    list_specs_index = get_list_index_by_specid(list_specs, spec_id)
                    if list_specs_index == -1:
                        print('没找到对应的 spec_id，车系：%s 配置：%s spec：%s' % (series_id, item_id, spec_id))
                        continue
                    one_spec = list_specs[list_specs_index]
                    one_column = list_specs_columns[list_specs_index]
                    one_spec.append(item_value)
                    one_column.append(item_id)
            
            # 外观颜色
            config_color_specs = pattern_config_color_specs.findall(str_config_color)
            for one_config_color_spec in config_color_specs:
                item_id = 'outer_color'
                item_name = '外观颜色'
                add_column(item_id, item_name)
                spec_id = one_config_color_spec[0]
                list_specs_index = get_list_index_by_specid(list_specs, spec_id)
                if list_specs_index == -1:
                    print('没找到对应的 spec_id，车系：%s 外观颜色 spec：%s' % (series_id, spec_id))
                    continue
                one_spec = list_specs[list_specs_index]
                config_color_colors = pattern_config_color_colors.findall(one_config_color_spec[1])
                item_value = ' '.join(config_color_colors)
                item_value = get_simple_word(item_value)
                one_spec.append(item_value)
                one_column = list_specs_columns[list_specs_index]
                one_column.append(item_id)
            
            # 内饰颜色
            config_color_specs = pattern_config_color_specs.findall(str_config_inner_color)
            for one_config_color_spec in config_color_specs:
                item_id = 'inner_color'
                item_name = '内饰颜色'
                add_column(item_id, item_name)
                spec_id = one_config_color_spec[0]
                list_specs_index = get_list_index_by_specid(list_specs, spec_id)
                if list_specs_index == -1:
                    print('没找到对应的 spec_id，车系：%s 内饰颜色 spec：%s' % (series_id, spec_id))
                    continue
                one_spec = list_specs[list_specs_index]
                config_color_colors = pattern_config_color_colors.findall(one_config_color_spec[1])
                item_value = ' '.join(config_color_colors)
                item_value = get_simple_word(item_value)
                one_spec.append(item_value)
                one_column = list_specs_columns[list_specs_index]
                one_column.append(item_id)
            
            # 选装包
            config_bag_bags = pattern_config_bag_bags.findall(str_config_bag)
            bag_index = 0
            for one_config_bag_bag in config_bag_bags:
                item_id = 'bag_%d' % bag_index
                item_name = '选装包%d' % bag_index
                item_price = one_config_bag_bag[0]
                bag_name = one_config_bag_bag[1]
                bag_desc = one_config_bag_bag[3]
                bag_name = '选装[%s]¥%s[%s]' % (bag_name, item_price, bag_desc)
                str_specs = one_config_bag_bag[2]
                add_column(item_id, item_name)
                config_bag_specs = pattern_config_bag_specs.findall(str_specs)
                for one_config_bag_spec in config_bag_specs:
                    spec_id = one_config_bag_spec[0]
                    item_value = one_config_bag_spec[1]
                    if item_value != '-':
                        item_value = item_value + get_simple_word(bag_name)
                    list_specs_index = get_list_index_by_specid(list_specs, spec_id)
                    if list_specs_index == -1:
                        print('没找到对应的 spec_id，车系：%s 选装包：%d spec：%s' % (series_id, bag_index, spec_id))
                        continue
                    one_spec = list_specs[list_specs_index]
                    one_spec.append(item_value)
                    one_column = list_specs_columns[list_specs_index]
                    one_column.append(item_id)
                bag_index = bag_index + 1
            
            count_series_done = count_series_done + 1
            count_specs_done = count_specs_done + len(list_specs)

            # 配置全部读取完成，进行数据库操作
            # 先添加新找到的列
            if len(columns_todo) > 0:
                db.db_add_columns(columns_todo)
            # 将数据存入数据库
            db.db_insert(list_specs_columns, list_specs)
            print('成功处理车系 %s ---------- %s' % (series_id, series_name))

        except error.HTTPError as e:
            print('-- %s -- HTTPError:%s' % (series_id, e.reason))
            continue
        except error.URLError as e:
            print('-- %s -- URLError:%s' % (series_id, e.reason))
            continue

    print('已完成车系：%d，车型：%d' % (count_series_done, count_specs_done))


if __name__ == "__main__":
    if not Path(db.db_name).exists():
        # 初始化数据库
        db.db_init()

    columns_done = db.db_get_columns()
    series_ids_done = db.db_get_series_ids_done()

    get_series_ids()
    get_configs()
