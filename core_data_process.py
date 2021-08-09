import os
import sqlite3
import operator
from collections import OrderedDict
import time
from datetime import datetime, timedelta
import getpass
import settings
from settings import log
from Public.v_timestamp import day000
import re
import psutil

def parse(url):
    # url:http://www.baidu.con
    # This is the standard process
    try:
        parsed_url_components = url.split('//')  # ['http:', 'www.baidu.com/']
        sublevel_split = parsed_url_components[1].split('/', 1)  # ['www.baidu.com', '']
        domain = sublevel_split[0].replace("www.", "")  # 'baidu.com'
        return domain
    except IndexError:
        log('URL format error!')

def datetime_standard(pywindate):
    return datetime(pywindate.year, pywindate.month, pywindate.day, hour=pywindate.hour, minute=pywindate.minute, microsecond=pywindate.microsecond)

def getdate(pdatetime):
    return pdatetime.strftime("%Y-%m-%d")

def get_history_data(start, end):
    day_start,day_end=(day000(start),day000(end))
    # 获取当前系统登录用户名
    localuser = getpass.getuser()
    connstr = 'C:\\Users\\' + localuser + '\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\History'
    # 校验Chrome文件是否存在
    # log("chrome get_data in process from {0} to {1}".format(day_start,day_end))
    if not os.path.exists(connstr):
        raise Exception('Chrome History File does not exists!')

    conn = sqlite3.connect(connstr)
    cur = conn.cursor()
    # querystr = 'select urls.url,urls.title,visits.visit_time,visits.visit_duration from visits LEFT JOIN urls on visits.url = urls.id order by visits.visit_time desc'
    querystr = 'select urls.url,urls.title,visits.visit_time,visits.visit_duration, keyword_search_terms.term from (visits LEFT JOIN urls on visits.url = urls.id) JOIN \
     keyword_search_terms on keyword_search_terms.url_id=urls.id order by visits.visit_time desc'
    try:
        cur.execute(querystr)
    except sqlite3.OperationalError:
        log('please close chrome browser at first!')

    data_all = cur.fetchall()
    expectdata = []
    for data in data_all:
        # 微秒转换为秒
        last_visit_time = data[2] / 1000 / 1000
        last_visit= datetime(1601, 1, 1) + timedelta(seconds=last_visit_time, hours=8)
        # 获取昨天时间之后的内容，否则退出循环（查询数据已经倒序排列）
        if day_start <= last_visit < day_end:
            # 转换访问时间，UTC转换时区 + 8h
            visit_time = last_visit
            expectdata.append((visit_time,getdate(visit_time), "unallocated",'chrome',data[1],5,data[4],parse(data[0]),""))
    # if expectdata == []:
    #     raise Exception('there is no data.')

    cur.close()
    conn.close()
    # log("chrome get_data finished")
    return expectdata


def geteverythingresult(start,end=-1):
    import os
    import ctypes
    import struct

    #defines
    EVERYTHING_REQUEST_FILE_NAME = 0x00000001
    EVERYTHING_REQUEST_PATH = 0x00000002
    EVERYTHING_REQUEST_FULL_PATH_AND_FILE_NAME = 0x00000004
    EVERYTHING_REQUEST_EXTENSION = 0x00000008
    EVERYTHING_REQUEST_SIZE = 0x00000010
    EVERYTHING_REQUEST_DATE_CREATED = 0x00000020
    EVERYTHING_REQUEST_DATE_MODIFIED = 0x00000040
    EVERYTHING_REQUEST_DATE_ACCESSED = 0x00000080
    EVERYTHING_REQUEST_ATTRIBUTES = 0x00000100
    EVERYTHING_REQUEST_FILE_LIST_FILE_NAME = 0x00000200
    EVERYTHING_REQUEST_RUN_COUNT = 0x00000400
    EVERYTHING_REQUEST_DATE_RUN = 0x00000800
    EVERYTHING_REQUEST_DATE_RECENTLY_CHANGED = 0x00001000
    EVERYTHING_REQUEST_HIGHLIGHTED_FILE_NAME = 0x00002000
    EVERYTHING_REQUEST_HIGHLIGHTED_PATH = 0x00004000
    EVERYTHING_REQUEST_HIGHLIGHTED_FULL_PATH_AND_FILE_NAME = 0x00008000

    def get_size(filesize):
        return "{:.0f}".format(filesize/1000) +' K'

    def get_time(filetime):
        """Convert windows filetime winticks to python datetime.datetime."""
        winticks = struct.unpack('<Q', filetime)[0]
        microsecs = (winticks - WINDOWS_TICKS_TO_POSIX_EPOCH) / WINDOWS_TICKS
        return datetime.fromtimestamp(microsecs)

    #dll imports
    everything_dll_pos = settings.gets('everything_dll_pos')
    everything_dll = ctypes.WinDLL(everything_dll_pos)
    everything_dll.Everything_GetResultDateModified.argtypes = [ctypes.c_int,ctypes.POINTER(ctypes.c_ulonglong)]
    everything_dll.Everything_GetResultSize.argtypes = [ctypes.c_int,ctypes.POINTER(ctypes.c_ulonglong)]
    everything_dll.Everything_GetResultFileNameW.argtypes = [ctypes.c_int]
    everything_dll.Everything_GetResultFileNameW.restype = ctypes.c_wchar_p

    #convert a windows FILETIME to a python datetime
    #https://stackoverflow.com/questions/39481221/convert-datetime-back-to-windows-64-bit-filetime
    WINDOWS_TICKS = int(1/10**-7)  # 10,000,000 (100 nanoseconds or .1 microseconds)
    WINDOWS_EPOCH = datetime.strptime('1601-01-01 00:00:00',
                                               '%Y-%m-%d %H:%M:%S')
    POSIX_EPOCH = datetime.strptime('1970-01-01 00:00:00',
                                             '%Y-%m-%d %H:%M:%S')
    EPOCH_DIFF = (POSIX_EPOCH - WINDOWS_EPOCH).total_seconds()  # 11644473600.0
    WINDOWS_TICKS_TO_POSIX_EPOCH = EPOCH_DIFF * WINDOWS_TICKS  # 116444736000000000.0

    # create buffers
    filename = ctypes.create_unicode_buffer(260)
    date_modified_filetime = ctypes.c_ulonglong(1)
    file_size = ctypes.c_ulonglong(1)
    everythinginfo = []
    exclude_word_list = settings.gets('exclude_word_list')
    # time setting
    for day in range(start, end, -1):
        searchdate = day000(day).strftime("%Y-%m-%d")
        # log("core_data_process.geteverythingresult.find at day {}".format(searchdate))

        #setup search
        everything_dll.Everything_SetSearchW("dm:" + searchdate)
        everything_dll.Everything_SetRequestFlags(EVERYTHING_REQUEST_FILE_NAME | EVERYTHING_REQUEST_PATH | EVERYTHING_REQUEST_SIZE | EVERYTHING_REQUEST_DATE_MODIFIED)

        #execute the query
        everything_dll.Everything_QueryW(1)

        #get the number of results
        num_results = everything_dll.Everything_GetNumResults()

        #show the number of results
        # log("local file result count: {}".format(num_results))

        #show results
        for i in range(num_results):
            everything_dll.Everything_GetResultFullPathNameW(i,filename,260)
            everything_dll.Everything_GetResultDateModified(i,date_modified_filetime)
            everything_dll.Everything_GetResultSize(i,file_size)
            # if 9 < int(get_size(file_size)) < 10000000:
            if 10000 < file_size.value < 1000000:
                gather = True
                for kw in exclude_word_list:
                    if re.search(kw, ctypes.wstring_at(filename), re.I):
                        gather = False
                if gather:
                    filefullname= ctypes.wstring_at(filename)
                    filetime=get_time(date_modified_filetime)
                    everythinginfo.append(( filetime, getdate(filetime), 'unallocated', 'local', \
                                            os.path.basename(filefullname), 5, os.path.dirname(filefullname), get_size(file_size.value),""))
                    # print("Filename: {}\tDate Modified: {}\tSize: {}B\t".format(ctypes.wstring_at(filename), get_time(date_modified_filetime), get_size(file_size.value)))
    # log("core_data_process.geteverythingresult.find finished.")
    return everythinginfo

def read_outlook_mailbox(start, end= -1,where = "inbox"):
    from win32com.client.gencache import EnsureDispatch as Dispatch  # 读取邮件模块
    __batchmax__ = 1000
    _grid = 50
    defwhere = ['inbox', 'outbox', 'calendar']
    day_start,day_end =(day000(start),day000(end))
    """连接Outlook邮箱，读取收件箱内的邮件内容"""
    # 使用MAPI协议连接Outlook
    # log("Outlook read start at {} .".format(where))
    # log("startdate.at {0} , enddate.at {1}".format(day_start, day_end))
    account = Dispatch('Outlook.Application').GetNamespace('MAPI')
    # 获取收件箱所在位置
    if where == defwhere[0]:
        folder = account.GetDefaultFolder(6)  # 数字6代表收件箱
    elif where == defwhere[1]:
        folder= account.GetDefaultFolder(5) # 数字5 代表已发出邮件
    elif where == defwhere[2]:
        folder = account.GetDefaultFolder(9)
    # 获取收件箱下的所有邮件
    items = folder.Items
    if where == defwhere[2]:
        items.Sort('[Start]', True)  # 邮件按时间排序
    else:
        items.Sort('[ReceivedTime]', True)  # 邮件按时间排序
    itemcount=len(items)
    _lowerend= 1
    _upperend=itemcount
    for lr in range(0,_grid+1,1):
        _lowerend= int(lr/ _grid * itemcount)+1
        try:
            if where== defwhere[2]:
                if datetime_standard(items.Item(_lowerend).Start) < day_start:
                    break
            else:
                if datetime_standard(items.Item(_lowerend).ReceivedTime) < day_start:
                    break
        except:
            # log(_lowerend,'error lr')
            pass

    for ur in range(_grid,0-1,-1):
        _upperend= int(ur / _grid * itemcount)
        try:
            if where == defwhere[2]:
                if datetime_standard(items.Item(_upperend).Start) > day_end:
                    break
            else:
                if datetime_standard(items.Item(_upperend).ReceivedTime) > day_end :
                    break
        except:
            # log(_upperend, 'error ur')
            pass


    if _upperend > _lowerend:
        temp=_lowerend
        _lowerend=_upperend
        _upperend=temp

    mailinfos=[]
    # log("lowerend.at {0} , upperend.at {1}".format(str(_lowerend), str(_upperend)))
    # 读取收件箱内前3封邮件的所有信息（下标从1开始）
    for index in range(_lowerend, _upperend+1,-1):
        try:
            mailrt= datetime_standard(items.Item(index).Start) if where == defwhere[2] else  datetime_standard(items.Item(index).ReceivedTime)
            if day_start < mailrt <= day_end:
                mail = items.Item(index)
                try:
                    if where == defwhere[0]:
                        filetime= datetime_standard(mail.ReceivedTime)
                        mailinfos.append(
                            (filetime, getdate(filetime), 'unallocated', 'inbox', mail.Subject, 5, mail.SenderName, mail.Body[:300], ""))
                    elif where == defwhere[1]:
                        filetime=datetime_standard(mail.ReceivedTime)
                        mailinfos.append(
                            (filetime,getdate(filetime),'unallocated', 'outbox', mail.Subject, 5,  mail.To, mail.Body[:300], ""))
                    elif where == defwhere[2]:
                        username = account.Accounts.Item(1).CurrentUser.Name
                        joiners = list(it.Name for it in mail.Recipients)
                        if username in joiners:
                            filetime=datetime_standard(mail.Start)
                            mailinfos.append(
                                (filetime,getdate(filetime), 'unallocated','calendar', mail.Subject, mail.Duration, mail.Organizer, mail.Body[:300],''))
                except:
                    # log('读取第[{}]封邮件异常，没有SenderName...'.format(index))
                    pass

        except:
            # print('读取第[{}]封邮件异常，没有收件时间...'.format(index))
            pass
    # log("Outlook get_data finished at {} .".format(where))
    return mailinfos

def get_data_system():
    boot_time = psutil.boot_time()  # 返回一个时间戳
    boot_time_obj = datetime.fromtimestamp(boot_time)
    now_time = datetime.now()
    login_user = psutil.users()[0]
    data = (boot_time_obj, getdate(boot_time_obj),'unallocated' , 'system', "开机事件", 5, login_user.name ,'' ,'')
    print(data)


def cleanerror2():
    try:
        from win32com import client
        xl = client.gencache.EnsureDispatch('Excel.Application')
    except AttributeError:
        # Corner case dependencies.
        import os
        import re
        import sys
        import shutil
        # Remove cache and try again.
        MODULE_LIST = [m.__name__ for m in sys.modules.values()]
        for module in MODULE_LIST:
            if re.match(r'win32com\.gen_py\..+', module):
                del sys.modules[module]
        shutil.rmtree(os.path.join(os.environ.get('LOCALAPPDATA'), 'Temp', 'gen_py'))
        from win32com import client
        xl = client.gencache.EnsureDispatch('Excel.Application')

if __name__ == '__main__':
    # from datetime import datetime, timedelta
    # t0 = datetime.now()
    # for i  in range(5):
    #     print(len(geteverythingresult(i,i-1)),end="\t")
    #     print(len(get_history_data(i, i-1)),end="\t")
    #     print(len(read_outlook_mailbox(i, i-1, "inbox")),end="\t")
    #     print(len(read_outlook_mailbox(i, i-1, "outbox")),end="\n")
    # print( datetime.now() - t0 )
    get_data_system()
    pass