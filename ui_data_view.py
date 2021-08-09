
from PyQt5.QtWidgets import QAction,QActionGroup,QTableWidget \
    ,QMenu,QApplication,QWidget,QPushButton,QAbstractItemView,\
    QTableWidgetItem, qApp, QSizePolicy, QVBoxLayout
from PyQt5.QtCore import Qt
from db_core import db
from datetime import datetime, timedelta
import settings
from settings import log
import copy
from Public.v_timestamp import day000


def Acts(obj,actlist,cbb=True):
    #为了减少代码量，一次性生成多个Action并附在对象背后
    if len(actlist) != 0:
        acts=[]
        for i in range(len(actlist)):
            act = QAction(actlist[i], obj)
            obj.addAction(act)
            act.setVisible(True)
            act.setCheckable(cbb)
            act.setText(actlist[i])
            acts.append(act)
        return acts


class MenuTW(QTableWidget):
    def __init__(self,parent=None):
        super().__init__()
        self.setParent(parent)
        self.setup_ui()
        self.db = db()
        self.day= 0
        self.data = []
        self.columntitle = ['id','时间', '日期', '项目', '来源', '主题', '时长', '信息1', '信息2', '备注']
        self.setHorizontalHeaderLabels(self.columntitle)
        self.setColumnCount(len(self.columntitle))
        self.setCW([0,120,0,60,60,100,40,300,300,200])
        # log('MenuTW 完成加载。')
        self.setup_ui()

    def setup_ui(self):
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showMenu)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)


    def loaddata(self, source="", account=""):
        self.data = self.sort(self.db.getrecordbyday(self.day, source, account))
        newdata=self.data
        return self.loaddata_core(newdata)

    def setCW(self,cws):
        for i in range(len(cws)):
            self.setColumnWidth(i,cws[i])

    def refresh(self):
        self.db.refresh(self.day)

    def sort(self,data):
        rawdata= copy.deepcopy(data)
        rawdata.sort(key= lambda x: x[1])
        return rawdata

    def showbyaccount(self,account):
        self.data= self.sort(self.db.getrecordbyday(self.day,"",account))
        return self.loaddata_core(self.data)

    def showbysource(self,source):
        self.data = self.sort(self.db.getrecordbyday(self.day, source, ""))
        return self.loaddata_core(self.data)

    def loaddata_core(self, newdata):
        self.setHorizontalHeaderLabels(self.columntitle)
        self.setRowCount(len(newdata)) if len(newdata) != 0 else self.setRowCount(10)
        for i in range(self.rowCount()):
            for j in range(self.columnCount()):
                self.setItem(i, j, QTableWidgetItem(str(newdata[i][j]))) if len(newdata) != 0 else self.setItem(i, j, QTableWidgetItem(""))
        # log('Data load to view.')
        return len(newdata)


    def showMenu(self,pos):
        xys=self.selectionModel().selection().indexes()
        if True:
            self.menu = QMenu()
            self.setauto=Acts(self.menu,['自动识别','自动识别并保存'],False)
            list(map(QActionGroup(self).addAction,self.setauto))
            self.menu.addSeparator()
            self.setacc=Acts(self.menu,settings.account_list,False)
            list(map(QActionGroup(self).addAction,self.setacc))
            self.menu.addSeparator()
            self.reads = Acts(self.menu, [u"强制刷新", u"增量刷新", u"删除重刷",u"帮助"],False)
            self.menu.addSeparator()
            action = self.menu.exec_(self.mapToGlobal(pos))
            try:
                self.takeaction(action.text(),xys)
            except:
                pass



    def takeaction(self,order,xys):
        if order in settings.account_list:
            self.changeaccount(order,xys)
        elif order in ['自动识别','自动识别并保存']:
            self.changeaccountauto(order,xys)
        else:
            self.otherorder(order)

    def changeaccount(self,order,xys):
        qids=[]
        for xy in xys:
            r,c=(xy.row(),xy.column())
            self.setItem(r,3,QTableWidgetItem(order))
            qids.append(str(self.item(r,0).text()))
        self.db.update_account(qids,order)
        # log("account 手工修改。")

    def changeaccountauto(self,order,xys):
        qids=[]
        for xy in xys:
            r, c = (xy.row(), xy.column())
            qids.append(str(self.item(r,0).text()))
        self.db.update_account_auto(qids)
        self.loaddata()
        # log("account 自动识别。")

    def otherorder(self,order):
        if order == '强制刷新':
            self.db.refresh(self.day,True,True)
        elif order == '增量刷新':
            self.db.refresh(self.day,True,False)
        elif order == '删除重刷':
            self.db.delete_byday(self.day)
            self.db.refresh(self.day,True,True)
        else:
            pass

    def quit(self):
        qApp.quit()
        sys.exit()

    def select(self,dt):
        pass


class TWstat(QWidget):
    def __init__(self, database, day=0):
        super().__init__()
        self.vbox = QVBoxLayout()
        self.setLayout(self.vbox)
        self.sub, self.btn1, self.btn2 = (QTableWidget(), QPushButton(), QPushButton())
        self.db = database
        self.btn1.setText('行列转换')
        self.btn2.setText('逐日信息')
        self.day = day
        self.vbox.addWidget(self.btn1)
        self.vbox.addWidget(self.btn2)
        self.vbox.addWidget(self.sub)
        self.rotate= True
        self.btn1.clicked.connect(self.getview)
        self.btn2.clicked.connect(self.getview_day)
        # log('Build Stat Interface OK.')
        self.getview()

    def getview(self):
        self.rotate = not self.rotate
        byacc = self.rotate
        dt = (datetime.today() - timedelta(days=self.day)).strftime('%Y-%m-%d')
        columnlist = settings.source_list if byacc else settings.account_list
        rowlist = settings.account_list if byacc else settings.source_list
        self.sub.setWindowTitle('Statistic Information at Day')
        self.sub.setRowCount(len(rowlist))
        self.sub.setColumnCount(len(columnlist))
        self.sub.setHorizontalHeaderLabels(columnlist)
        a=[self.sub.setColumnWidth(i, 80) for i in range(len(columnlist))]
        self.sub.setVerticalHeaderLabels(rowlist)
        data=self.db.build_sub2(dt, byacc)
        datarow= [data[i][0] for i in range(len(data))]
        for i in range(self.sub.rowCount()):
            if rowlist[i] in datarow:
                row= datarow.index(rowlist[i])
                for j in range(self.sub.columnCount()):
                    self.sub.setItem(i, j, QTableWidgetItem(str(data[row][j+1])))
            else:
                for j in range(self.sub.columnCount()):
                    self.sub.setItem(i, j, QTableWidgetItem("0"))

    def getview_day(self):
        columnlist = settings.source_list
        self.sub.setColumnCount(len(columnlist))
        self.sub.setHorizontalHeaderLabels(columnlist)
        self.sub.setWindowTitle('Statistic Information By Days')
        a = [self.sub.setColumnWidth(i, 80) for i in range(len(columnlist))]
        datas = list(self.db.get_subs())
        # print(datas)
        rowlist = [data[0] for data in datas]
        self.sub.setRowCount(len(rowlist))
        self.sub.setVerticalHeaderLabels(rowlist)
        for i in range(self.sub.rowCount()):
            for j in range(self.sub.columnCount()):
                self.sub.setItem(i, j, QTableWidgetItem(str(datas[i][j+2])))




if __name__ == '__main__':
    import sys
    class Window(QWidget):

        def __init__(self, parent=None):
            super().__init__()
            self.resize(600, 600)
            self.btn = QPushButton(self)
            self.btn1 = QPushButton(self)
            self.btn2 = QPushButton(self)
            self.tw = MenuTW(self)

            self.setup_ui()

        def setup_ui(self):
            self.btn.move(50, 20)
            self.btn.resize(500, 30)
            self.btn1.move (50,60)
            self.btn1.resize(200,30)
            self.btn2.move(300, 60)
            self.btn2.resize(200, 30)
            self.tw.move(50, 100)
            self.tw.resize(500, 400)
            self.btn.setText('刷新')
            self.btn1.setText('上一日')
            self.btn2.setText('下一日')
            self.btn.clicked.connect(self.loaddata)
            self.btn1.clicked.connect(self.dateup)
            self.btn2.clicked.connect(self.datedown)

        def loaddata(self):
            if self.tw.loaddata()==0:
                self.tw.refresh()
                self.tw.loaddata()

        def dateup(self):
            self.tw.day= self.tw.day +1
            self.loaddata()

        def datedown(self):
            self.tw.day=self.tw.day -1 if self.tw.day>=1 else 0
            self.loaddata()

        def testview(self):
            self.bg = TWstat(self.tw.db,0)
            pos = self.mapToGlobal(self.pos())
            left= pos.x()
            top = pos.y()
            lefto= self.pos().x()
            topo= self.pos().y()
            self.bg.move(lefto+ self.width(),topo)
            self.bg.show()





    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())