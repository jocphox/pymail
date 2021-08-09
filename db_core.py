import sqlite3
from datetime import datetime, timedelta
import random
import os.path
from settings import log
import settings
from guess_core import guess
from core_data_process import *


class MWTransForm(object):
    def __init__(self):
        self.qid_time_format = settings.gets('qid_time_format')
        self.fulltime_format = settings.gets('fulltime_format')
        self.recordtime_format = settings.gets('recordtime_format')


    # this is the middle ware for the transform of rawdata and dbdata
    def build_id(self, rawdata):
        return rawdata[3] + rawdata[0].strftime(self.qid_time_format)

    def datetime_to_formatstr(self, v_datetime):
        return v_datetime.strftime(self.fulltime_format)
        pass

    def rawdata_to_record(self, rawdata):
        return tuple([self.build_id(rawdata), rawdata[0].strftime(self.recordtime_format)] + list(rawdata[1:]))
        pass

    def record_to_rawdata(self, record):
        return tuple([datetime.strptime(record[1], self.recordtime_format)] + list(record)[2:])
        pass

    def formatstr_to_datetime(self, s_datetime):
        return datetime.strptime(s_datetime, self.fulltime_format)

    def element(self, i):
        return lambda x: x[i]

    def dtstr2id(self, viewitem):
        # viewtiem has 'YmdHM'
        # return record[3] + datetime.strptime(record[1],settings.recordtime_format).strftime(settings.qid_time_format)
        pass


class db(object):
    # the core function is add, delete, update, search, group
    def __init__(self, dbname="dbfile.db"):

        self.conn = sqlite3.connect(dbname)
        self.curs = self.conn.cursor()
        self.mw = MWTransForm()
        if len(open(dbname, "rb").read()) == 0:
            tblcmd = 'create table records (' \
                          'qid char(12),' \
                          'qdt char(20), ' \
                          'qdate char(12), ' \
                          'qacc char(15), ' \
                          'qsrc char(10), ' \
                          'qsubject char(50), ' \
                          'qduration floot(3), ' \
                          'qguesser char(50), ' \
                          'qbody char(50), ' \
                          'qnote char(4))'
            self.curs.execute(tblcmd)
            self.conn.commit()
            tblbuilt = 'create table sub_records ( ' \
                            'bid char(12), ' \
                            'bready char(1), '\
                            'bchrome char(1), ' \
                            'blocal char(1), ' \
                            'boutbox char(1), ' \
                            'bcalendar char(1), ' \
                            'binbox char(1))'
            self.curs.execute(tblbuilt)
            self.conn.commit()
            log("DB initialized.")
        self.recordtime_format = settings.gets('recordtime_format')
        self.builddb()
        self.refresh_jump_list = settings.gets('jump_when_build_data_list')


    def search(self, ref=9):  # 9 columns in db
        self.curs.execute("select * from records")
        fall = self.curs.fetchall()
        if ref == 9:
            return fall
        else:
            return list(map(self.mw.element(ref), fall))

    # add part
    def add_rawdata(self, rawdatas, force=False):
        self.curs.execute("select * from records")
        names = self.search(0)
        # log("add_rawdata in {} mode.".format('force add' if force else 'free add'), ">>")
        for rawdata in rawdatas:
            recordname = self.mw.build_id(rawdata)
            if force:
                if recordname in names:
                    self.delete([recordname])
                self.curs.execute('insert into records values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                  self.mw.rawdata_to_record(rawdata))
                names.append(recordname)
            else:
                if recordname not in names:
                    self.curs.execute('insert into records values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                      self.mw.rawdata_to_record(rawdata))
                names.append(recordname)
        self.conn.commit()
        # log('raw data input succeed.', ">")

    def count(self):  # 返回数据数量
        return len(self.search(0))

    # middle ware
    def record_to_rawdata(self, record):
        return self.mw.record_to_rawdata(record)

    def close(self):
        self.conn.close()

    # delete part
    def delete(self, qids):
        self.curs.execute('delete from records where qid = ? ', qids)
        self.conn.commit()

    def delete_bydate(self, sdate):
        self.curs.execute('select * from records where qdata= ?', [sdate])
        qs = self.curs.fetchall()
        qids = [q[0] for q in qs]
        self.delete(qids)
        log("data at {} has been deleted.".format(sdate))  # log here

    def delete_byday(self, day):
        dt = (datetime.today() - timedelta(days=day)).strftime('%Y-%m-%d')
        self.delete_bydate(dt)

    def clean(self):
        self.curs.execute('delete from records')
        self.conn.commit()

    # search part
    def build_sub(self):
        cmd = []
        for src in settings.source_list[:]:
            cmd.append("sum(CASE WHEN qsrc= \'" + src + "\' THEN 1 ELSE 0 END) " + src)
        totalcmd = "select qdate, " + ",".join(cmd) + " from records group by qdate"
        # log(totalcmd)
        self.curs.execute(totalcmd)
        qs = self.curs.fetchall()
        return qs

    def build_sub2(self, dt, byacc=True):
        cmd = []
        if byacc:
            for src in settings.source_list[:]:
                cmd.append("sum(CASE WHEN qsrc= \'" + src + "\' THEN 1 ELSE 0 END) " + src)
            totalcmd = "select qacc, " + ",".join(cmd) + " from records where qdate = ? group by qacc "
        else:
            for acc in settings.account_list[:]:
                cmd.append("sum(CASE WHEN qacc= \'" + acc + "\' THEN 1 ELSE 0 END) " + acc)
            totalcmd = "select qsrc, " + ",".join(cmd) + " from records where qdate = ? group by qsrc "
        # log(totalcmd)
        self.curs.execute(totalcmd, [dt])
        return self.curs.fetchall()

    def add_subs(self):
        self.curs.execute('select * from sub_records')
        names = [data[0] for data in self.curs.fetchall()]  # 获取 sub record 的信息
        rawdatas = self.build_sub()
        for rawdata in rawdatas:
            if rawdata[0] in names:  # 校验增加
                self.delete_sub(rawdata[0])
            self.curs.execute("insert into sub_records values (?,'y' ,?, ?, ?, ?, ?)", rawdata)
        self.conn.commit()
        return len(self.get_subs())

    def add_subs_none(self,dt):
        self.curs.execute("insert into sub_records values (?,'y' ,?, ?, ?, ?, ?)", [dt,0,0,0,0,0])
        self.conn.commit()


    def get_subs(self):
        self.curs.execute('select * from sub_records')
        qs = self.curs.fetchall()
        qs.sort(key=lambda x: x[0])
        return qs

    def delete_sub(self, qid):
        self.curs.execute("delete from sub_records where bid= ?", [qid])

    def isready(self, day=0, date=""):
        try:
            if date == "":
                dt = (datetime.today() - timedelta(days=day)).strftime('%Y-%m-%d')
            else:
                dt = date
            self.curs.execute("select bready from sub_records where bid = ?", [dt])
            qs = self.curs.fetchall()
            return qs[0][0] == 'y'
        except:
            return False

    def find2(self, dt, source, acc):
        if source != '' and acc != '':
            self.curs.execute("select * from records where qsrc = :sql_source and qacc = :sql_acc",
                          {'sql_source': source, 'sql_acc': acc})
        elif source != '' and acc == '':
            self.curs.execute("select * from records where qsrc = :sql_source", {'sql_source': source})
        elif source == '' and acc != '':
            self.curs.execute("select * from records where qacc = :sql_acc", {'sql_acc': acc})
        else:
            self.curs.execute("select * from records")
        qs = self.curs.fetchall()
        if dt != '':
            record_find = list(filter(lambda record: datetime.strptime(record[1],
                                                    self.recordtime_format).strftime("%Y%m%d")
                                                     == datetime.strptime(dt, "%Y-%m-%d").strftime("%Y%m%d"), qs))
        else:
            record_find =list(qs)
        return record_find

    def find(self, dt="", source="", acc=""):
        cmddt = " qdate = :sql_date " if dt != "" else "true"
        cmdsource = " qsrc = :sql_source " if source != "" else "true"
        cmdaccount = "qacc = :sql_account " if acc != "" else "true"
        totalcmd = " select * from records where " + " and ".join([cmddt, cmdsource, cmdaccount])
        self.curs.execute(totalcmd, {'sql_source': source, 'sql_account': acc, 'sql_date': dt})
        # log("finding date = {0} ,source = {1}, account =  {2}".format(dt,source,acc) + totalcmd)
        qs = list(self.curs.fetchall())
        # print(qs)
        return qs

    def get_long_record(self, duration=10):
        self.curs.execute("select * from records where qduration > ? ", [duration])
        qs = self.curs.fetchall()
        return list(qs)

    def builddb(self):
        if os.path.getsize("dbfile.db") < 10000:
            pass

    def getrecord(self, qids):
        self.curs.execute("select * from records")
        qs = self.curs.fetchall()
        if qids == []:
            return list(qs)
        else:
            return list(filter(lambda x: x[0] in qids, qs))

    def getrecordbyday(self, day=2, source="", account=""):
        dt = (datetime.today() - timedelta(days=day)).strftime('%Y-%m-%d')
        log('Get Record at Day {}.'.format(dt))
        return self.find(dt, source, account)

    # revise part
    def update_account(self, qids, acc):
        self.curs.execute("select * from records")
        names = [q[0] for q in self.curs.fetchall()]
        for qid in qids:
            if qid in names:
                self.curs.execute('update records set qacc=? where qid=?', [acc, qid])
        self.conn.commit()

    def update_account_auto(self, qids):
        qids = self.search(0) if qids == [] else qids
        j = 0
        for qid in qids:
            j = j+1
            self.progress = round(j/len(qids) * 100, 0)
            # log(self.progress)
            self.curs.execute("select qid, qsubject, qguesser, qbody from records where qid= ?", [qid])
            qs = self.curs.fetchall()
            for i in range(len(qs)):
                guessed = guess().get(qs[i][1], qs[i][2], qs[i][3])
                self.curs.execute("update records set qacc = ? where qid= ? ", [guessed, qs[i][0]])
        self.conn.commit()

    def update_duration(self, qids, minute):
        self.curs.execute("select * from records")
        names = [q[0] for q in self.curs.fetchall()]
        for qid in qids:
            if qid in names:
                self.curs.execute('update records set qduration=? where qid=?', [minute, qid])
        self.conn.commit()

    def refresh(self, day=0, force_sub=False, force_record=False):
        if int(day) < -1:
            return 0
        else:
            dt2 = (datetime.today() - timedelta(days=day)).strftime("%Y-%m-%d")
            if force_sub:
                log("Try to refresh, force refresh{}.".format(dt2))
            else:
                if self.isready(day):
                    log("Try to refresh {}, exists and not force, exit.".format(dt2))
                    return 0
                else:
                    log("Try to refresh {}, not force and not exists.".format(dt2))
            # log('{} is in refreshing.'.format(dt2))
            self.add_rawdata(geteverythingresult(day, day-1), force_record)  if 'local' not in self.refresh_jump_list else 0
            # log("dbcore > \t refresh local done." + ">")
            self.add_rawdata(read_outlook_mailbox(day, day-1, 'outbox'), force_record) if 'outbox' not in self.refresh_jump_list else 0
            # log('> \t refresh outbox done.' + ">")
            self.add_rawdata(read_outlook_mailbox(day, day - 1, 'calendar'), force_record) if 'calendar' not in self.refresh_jump_list else 0
            self.add_rawdata(read_outlook_mailbox(day, day - 1, 'inbox'), force_record) if 'inbox' not in self.refresh_jump_list else 0
            # log('> \t refresh calendar done.' + ">")
            self.add_rawdata(get_history_data(day, day-1), force_record) if 'chrome' not in self.refresh_jump_list else 0
            # log('> \t refresh chrome done.' + "\n")
            qs = self.find(dt2, "", "")
            # log('dbcore > \t find the records qids done',">")
            qids = list(map(lambda record: record[0], qs))
            self.update_account_auto(qids)
            # log('> \t self auto find account done.' + ">")
            # log('> \t refresh done.')
            self.add_subs_none(dt2) if self.add_subs() else 0
            return len(qids)

    # view part
    def load(self, day, needbuild=True):
        if needbuild:
            self.refresh(day)
            self.update_account_auto([])
        dt = (datetime.today() - timedelta(days=day)).strftime('%Y-%m-%d')
        cr = self.getrecord_converted(dt)
        ed = self.expand_data(cr)
        return ed

    def getrecord_converted(self, dt):
        records = self.find(dt, "", "")
        converted_record = [self.record_to_rawdata(record) for record in records]
        return converted_record

    def expand_data(self, converted_records):
        newrecords = []
        for record in converted_records:
            if record[5] >= 5:
                times = record[5]//5
                for _ in range(0, times):
                    newrecord = tuple([record[0] + timedelta(minutes=5*_)] +
                                      list(record)[1:5] + [record[5]-5*_] + list(record)[6:])
                    # print(newrecord)
                    newrecords.append(newrecord)
        # newrecords.sort(key = lambda x: x[0])
        return newrecords

    def load2tw(self):
        return [x[1:] for x in self.getrecord([])]

    def listprint(self, lst):
        print('-------------------------------------------------')
        for i in range(len(lst)):
            print(lst[i])
        print('-------------------------------------------------')


if __name__ == '__main__':
    a = db()
    date = '2021-08-03'
    source = 'outbox'
    account = 'kuaishou'
    # a.listprint(list(a.build_sub2(date, True)))
    # a.listprint(list(a.build_sub2(date, False)))
    from datetime import datetime
    t0= datetime.now()
    print(len(a.getrecord([])))
    for i in range(5):
        a.refresh(i,True,True)
    print(datetime.now() - t0)
    # print(a.find(12))
    print(a.get_subs())

