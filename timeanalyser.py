import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import settings
from ui_dart import Ui_MainWindow
import about
from datetime import datetime, timedelta
from ui_data_view import MenuTW, TWstat
from ui_graph_view import ShowWidget
from db_core import db
import settings
from settings import log
# Entropy must increase.


class ShowMainWindow(QtWidgets.QMainWindow,Ui_MainWindow):
    def __init__(self,parent=None):
        QtWidgets.QMainWindow.__init__(self,parent)
        # 调用父对象的设置方法，这才将所有的东西给传过来了
        self.setupUi(self)
        # 调用自身额外的一些操作，在QtDesigner中无法实现的操作在此处实现
        #翻译
        self.trans=QTranslator()
        self.startday=5
        self.endday=0
        self.today2=QDate.currentDate()
        self.tw = MenuTW(self.splitter_3)
        self.plw = ShowWidget(self.splitter_3)
        self.tw.day=self.endday
        self.plw.day=self.endday
        self.dart_label.setText("DART " + self.showday())
        self.db = self.tw.db
        self.surf_with_drawing = settings.gets('surf_with_drawing')
        # print(self.surf_with_drawing)
        self.acc = ""
        self.src = ""
        # log('主界面完成加载。')
        self.setup_UI()

    def normalday(self, day):
        return (datetime.today() - timedelta(days=day)).strftime('%Y-%m-%d')

    def showday(self):
        self.endday = self.tw.day
        return (datetime.today() - timedelta(days=self.endday)).strftime('%Y-%m-%d %A')

    def setup_UI(self):
        self.tw.setFixedWidth(600)
        self.dateEdit_end.setDate(self.today2)
        self.comboBox_period.addItems(['', '今天', '当天', '昨天', '过去一周', '过去半月', '过去一月', '过去三个月'])
        self.cb_language.addItems(['English', "中文"])
        self.cb_src.addItems([""] + settings.source_list)
        self.cb_acc.addItems([""] + settings.account_list)
        self.comboBox_period.setCurrentIndex(0)
        self.dateEdit_start.dateChanged.connect(self.upinfo)
        self.dateEdit_end.dateChanged.connect(self.setcomboboxperiod)
        self.comboBox_period.currentIndexChanged.connect(self.setcomboboxperiod)
        self.btn_web.clicked.connect(self.loadchrome)
        self.btnlocal.clicked.connect(self.loadlocal)
        self.btn_inbox.clicked.connect(self.loadmailin)
        self.btn_outbox.clicked.connect(self.loadmailout)
        self.btn_output.clicked.connect(self.logout)
        self.btn_getdata.clicked.connect(self.load_data_analyser)
        self.btn_getpl.clicked.connect(self.load_pic_analyser)
        self.btn_up.clicked.connect(self.dayup)
        self.btn_down.clicked.connect(self.daydown)
        self.btn_show_ini.clicked.connect(self.showini)
        self.btn_run.clicked.connect(self.showstat) # 花了时间
        self.btnabout.clicked.connect(self.showabout)
        self.cb_src.currentIndexChanged.connect(self.showbysource)
        self.cb_acc.currentIndexChanged.connect(self.showbyaccount)
        self.tw.itemSelectionChanged.connect(self.tw2tb) # 花了时间
        # log("首次加载成功。")
        pass

    def qdatediff(self, qdt1, qdt2):
        return (qdt1.toPyDate()-qdt2.toPyDate()).days

    def showbysource(self):
        self.src = settings.source_list[self.cb_src.currentIndex()-1] if self.cb_src.currentIndex() > 0 else ""
        self.tw.showbysource(self.src)

    def showbyaccount(self):
        self.acc = settings.account_list[self.cb_acc.currentIndex()-1] if self.cb_acc.currentIndex() > 0 else ""
        self.tw.showbyaccount(self.acc)

    def showstat(self):
        self.st = TWstat(self.tw.db,self.tw.day)
        self.st.move(self.tw.pos().x()+self.tw.width(),self.tw.pos().y())
        self.st.resize(450,400)
        self.st.show()

    def autoupdateaccount(self):
        self.db.update_account_auto()

    def autorefresh(self):
        for i in range(30):
            self.db.refresh(i)

    def tw2tb(self):
        row= self.tw.selectionModel().selection().indexes()[0].row()
        msg= "\n -------------------------\n".join([str(self.tw.item(row,i).text()) for i in range(self.tw.columnCount())])
        self.plw.tb.setText(msg)

    def setcomboboxperiod(self):
        ci=self.comboBox_period.currentIndex()
        dategap=[0,0,-1,-2,-7,-15,-30,-90]
        self.dateEdit_start.setDate(self.dateEdit_end.date().addDays(dategap[ci]))
        self.upinfo()

    def d2s(self, qd):
        return qd.toString('YYYY-MM-DD')

    def upinfo(self):
        self.startday= self.qdatediff(self.today2,self.dateEdit_start.date())
        self.endday=self.qdatediff(self.today2,self.dateEdit_end.date())-1
        self.tw.day=self.endday
        self.plw.day=self.endday

    def loadview(self,src):
        viewdata=[]
        # print(self.startday,self.endday,-1)
        for i in range(self.startday,self.endday,-1):
            # log(self.normalday(i))
            viewdata = viewdata + self.db.find(self.normalday(i),source=src, acc="")
        title = ['id','时间', '日期', '项目', '来源', '主题/标题/文件名', '时长', '信息', '信息2', '备注']
        obj=[self.tv_web,self.tv_local, self.tv_mail,self.tv_mail,self.tv_mail]
        sourcelist=['chrome','local','outbox','calendar','inbox']
        ind= sourcelist.index(src)
        self.loaddata(obj[ind],[x for x in viewdata],title)
        self.tw.setColumnWidth(0,0)

    def loadmailin(self):
        self.loadview('inbox')

    def loadmailout(self):
        self.loadview('outbox')

    def loadmailcal(self):
        self.loadview('local')

    def loadchrome(self):
        self.loadview('chrome')

    def loadlocal(self):
        self.loadview('local')

    def logout(self):
        with open('log.txt','r') as f:
            log = f.read()
        self.msg = QtWidgets.QTextBrowser()
        self.msg.resize(450,self.height())
        self.msg.move(self.pos().x() + self.width(),self.pos().y())
        self.msg.setText(log)
        self.msg.show()

    def loaddata(self,tv,data,title):
        tv.model = QStandardItemModel(len(data), len(title))
        tv.model.setHorizontalHeaderLabels(title) if title else ""
        tv.setColumnWidth(3,200)
        for i in range(len(data)):
            for j in range(len(title)):
                item=QStandardItem(str(data[i][j]))
                tv.model.setItem(i,j,item)
        tv.setModel(tv.model)

    def load_data_analyser(self):
        # source=([""] + settings.source_list)[self.cb_src.currentIndex()]
        # account=([""] + settings.account_list)[self.cb_acc.currentIndex()]
        # log('load data {0}{1}'.format(source, account))
        try:
            if self.tw.loaddata(self.src, self.acc) == 0:
                self.tw.refresh()
                self.tw.loaddata(self.src, self.acc)
            self.load_pic_analyser() if self.surf_with_drawing == 'yes' else 0
        except:
            # print(self.tw.loaddata())
            pass

    def dayup(self):
        if self.tw.day >= -1:
            self.tw.day = self.tw.day+1
            self.load_data_analyser()
        else:
            self.tw.loaddata_core([])
            self.tw.day = self.tw.day + 1
        self.dart_label.setText("DART" + self.showday())

    def daydown(self):
        if self.tw.day > 0:
            self.tw.day = self.tw.day - 1
            self.load_data_analyser()
        else:
            self.tw.loaddata_core([])
            self.tw.day = self.tw.day - 1
        self.dart_label.setText("DART" + self.showday())

    def load_pic_analyser(self):
        self.plw.day = self.tw.day
        self.plw.ax.cla()
        if self.plw.draw2() == 0:
            self.plw.draw2()

    def runfinal(self):
        pass

    def showabout(self):
        about.aboutMessage('Entropy must increase!')

    def clicktoimage(self):
        pass

    def showinfo(self,info,pos):
        pass
    def showini(self):
        pass
     # 选择语种的时候
    # def comboBoxChange(self):
    #     self._trigger_english() if str(self.comboBox.currentText()) == "English" else self._trigger_zh_cn()

    def _trigger_english(self):
        #print("[MainWindow] Change to English")
        self.trans.load("en")
        _app = QCoreApplication.instance()  # 获取app实例
        _app.installTranslator(self.trans)
        # 重新翻译界面
        self.retranslateUi(self)

    def _trigger_zh_cn(self):
        #print("[MainWindow] Change to zh_CN")
        self.trans.load("zh_cn")
        _app = QCoreApplication.instance()
        _app.installTranslator(self.trans)
        self.retranslateUi(self)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    showWin = ShowMainWindow()
    showWin.show()
    sys.exit(app.exec_())