from datetime import datetime
from guess_core import guess
import configparser as configparser
# the settings to uniform the key words
config = configparser.ConfigParser()
config.read('settings.ini', encoding='utf-8')

# this the function part of the key settings
account_dict = guess().initiate_setting()
account_list = list(account_dict.keys())
source_list = ['chrome', 'local', 'outbox', 'calendar','inbox']
account_gap = round(1/(len(account_list)+1)*100, 0)/100
source_gap = round(1/(len(source_list)+1)*100, 0)/100
account_value = list(account_dict.values())
source_value = range(1, len(source_list)+1)
account_value_dict= dict(zip(account_value, account_list))
source_dict = dict(zip(source_list, source_value))
source_value_dict = dict(zip(source_value, source_list))

f_account= lambda acc:   account_dict[acc] if acc in account_dict.keys() \
    else (account_value_dict[acc] if acc in account_value_dict.keys() else 0)
f_source= lambda src:   source_dict[src] if src in source_dict.keys() \
    else (source_value_dict[src] if src in source_value_dict.keys() else 0)

fill_blank=('unallocated', 'input', 'subject', 5, 'with', "body", "input_info_if_any")
time, develop, draw, data = (0, 0, 0, 0)
# start of setting.ini
[time]
s_recordtime_format = "%Y-%m-%d %H:%M"
s_fulltime_format = "%Y-%m-%d %H:%M:%S %f"
s_qid_time_format = "%Y%m%d%H%M%S%f"
# 高级别的功能，"%Y%m%d%H%M%" 会大幅减少网页浏览数量

[draw]
s_marker_style_list = ["_", ">", "s", "o", "D", "<", "v", "^"]
# 画图的各标记的样式
s_start_hour_of_the_day = 8
# 画图时横坐标的下限（不低于0,0即为0：00）
s_end_hour_of_the_day = 23
# 画图时横坐标的上限（不超过23，23即为23：59）
s_basic_lasting = 5
# 设置 单个获得持续期间
s_basic_point_size = 5
# 设定 画图的点的大小
s_ylim_min = 0
# 设立y 轴的下相
s_ylim_max = 7
# 设立y 轴的上限
s_surf_with_drawing = "yes"
# yes 在更新数据的时候，同时更新 图片； no, 不同时更新，加快阅读速度

[data]
s_everything_dll_pos = "C:\\Users\\David Z Yang\\PycharmProjects\\pymail\\desktop_py\\Everything-SDK\\DLL\\Everything64.dll"
# everything dll 的位置
s_exclude_word_list = ["venv", "roaming" ,"pyc", "everything", "programdata","appdata"]
# 在读取本地文件修改记录时，包含以上单词的路径/文件名的文件会被忽略，系统安装文件时会新增大量文件修改，这修改并非来自你的修改
# 读取文件跟Everything 本身的设置有关
s_guess_model_list= ["search", "weighted"]
# 仅作提示，无意义
s_guess_model_value= 2
# 1 是 search, 速度快； 2 是 加权算法，更准确
s_jump_when_build_data_list = [""]
s_testmode = "no"
# 如果no，可以在log.txt 看到一些日志

[develop]
s_application_name = "TimeAnalyser"
s_author = "David Yang"
s_version = "0.01"
s_core_package = "sqlite3, win32com,..."
s_devdate = "2021-08"
s_organization = "Zhengzhou WEST Data Consultation Limited"
# 不要修改
# end of settings.ini
# end of setting.ini

def legend():
    return "\t".join(list(map(lambda x: x[0] + ":" + str(x[1]) + "~" + str(x[2]) + "\t",
                              list(zip(account_list, account_value, [x+1 for x in account_value])))))
def addtime():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log(content="", end= "\n"):
    testmode = True if gets('testmode') == 'yes' else False
    try:
        if testmode:
            print("log ", end=" >\t ")
            if content.__class__ == [].__class__:
                print('list is in print...')
                for _ in content:
                    print(_)
            elif content == '':
                print("--------------------------------")
            else:
                print(content, end=end)
        else:

            with open('log.txt','a') as f:
                f.write("\nlog[" + addtime() + '] >\t')
                if content.__class__ == [].__class__:
                    f.write('list is in print...')
                    for _ in content:
                        f.write(_)
                else:
                    f.write(content)
                f.write("\n--------------------------------")

    except:
        pass

def gets(attr2):
    try:
        return get_ini(attr2)
    except:
        return get_default(attr2)

def get_ini(attr2):
    for sec in config.sections():
        try:
            if 'list' in attr2:
                return list(eval(config.get(sec, attr2)))
            elif 'time' in attr2:
                newconfig = configparser.RawConfigParser()
                newconfig.read('settings.ini', encoding='utf-8')
                return str(eval(newconfig.get(sec, attr2)))
            else:
                return str(eval(str(config.get(sec, attr2))))
        except:
            pass

def get_default(attr2):
    try:
        if 'list' not in attr2:
            return str(eval('s_' + attr2))
        else:
            return str.split(str(eval('s_' + attr2)), ',')
    except:
        return

def generate_settings():
    line_no = 0
    start_row, end_row = (10000, 10000)
    start_wording = '# start of setting.ini'
    end_wording = '# end of setting.ini'
    clean_list = lambda s : str(s).replace('[',"").replace(']',"")
    rowput = lambda w: clean_list(w)[2:] if w[:2] == 's_' else w
    with open('settings.py','r', encoding='utf-8') as f:
        with open('settings.ini', 'w', encoding='utf-8') as s:
            for line in f.readlines():
                if start_wording in line:
                    start_row = line_no
                elif end_wording in line:
                    end_row = line_no
                line_no = line_no + 1
                if start_row < line_no < end_row:
                    s.write(rowput(line))
    # print(clean_list("['_', '>', 's', 'o', 'D', '<', 'v', '^']"))

def testsettings():
    import settings
    import os
    if not os.path.exists('settings.ini'):
        generate_settings()
    else:
        for pword in dir(settings):
            if "__" not in pword and 's_' in pword:
                sword = pword[2:]
                isword = get_ini(sword)
                dsword = get_default(sword)
                if isword == dsword:
                    print(sword, end=' \t \t  ok \n ')
                else:
                    try:
                        if len(isword) == len(dsword):
                            print(sword, len(isword), end=' \t \t   ok \n ')
                        else:
                            print(sword, '\t\t\t', len(get_ini(sword)), '\t\t\t', len(get_default(sword)))
                            print(sword, '\t\t\t', get_ini(sword)[:20], '\t\t\t', get_default(sword)[:20])
                    except:
                        pass

if __name__ == '__main__':
    # generate_settings()
    for i in range(10):
        log(str(i))



