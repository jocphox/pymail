import datetime
import time


def day000(day):
    # start is the search date gapp from today, end is -1 for now
    # start is in, and end is ok
    # 获取今天0点的日期
    now = datetime.datetime.now()
    now_000 = time.strftime('%Y-%m-%d', datetime.datetime.timetuple(now))
    # 获取昨天0点的日期
    today = datetime.datetime.strptime(now_000, '%Y-%m-%d')
    return today - datetime.timedelta(days=day)



if __name__ == '__main__':
    print(day000(0))
