from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import settings
import matplotlib.dates as mdates
from db_core import db
from PyQt5.QtWidgets import QWidget,QApplication,QPushButton,QVBoxLayout,QTextBrowser,QLabel,QHBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
sns.set()


def hourshow(hour, minute):
    return str(hour).zfill(2) + ":" + str(minute).zfill(2)

def standmark(hour, minute):
    return datetime.strptime(str(hour*100+minute+202001010000),"%Y%m%d%H%M")

def build_time_axis(starthour=8, endhour=24):
    minuteseries= [str(i*100+j+202001010000) for i in range(starthour,endhour)for j in range(0,60)]
    xs= [datetime.strptime(d,"%Y%m%d%H%M") for d in minuteseries]
    return xs

def expand(originlist, listaxis, fill=settings.fill_blank):
    # expand the originlist along the listaxis, if no data, fill the fill
    dictlst = dict(zip(list(a[0] for a in originlist), list(list(b[1:]) for b in originlist)))
    filledlist = list(dictlst[x] if x in dictlst.keys() else list(fill) for x in listaxis)
    expandedlist = list([a] + b for (a, b) in list(zip(listaxis, filledlist)))
    return expandedlist

class ShowWidget(QWidget):
    def __init__(self,parent=None):
        super(ShowWidget, self).__init__(parent)
        self.parent= parent
        self.fig = Figure((17,8), dpi=100)
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.day = 2
        self.heightmode=1
        self.displaymode=1
        self.srccount=4
        plt.rcParams['font.sans-serif'] = ['SimHei']
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.tb=QTextBrowser(self)
        self.lb=QLabel(self)
        self.lb.setText(settings.legend())
        self.tb.setText('The epxlanation heres.')
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.hbox = QHBoxLayout()
        self.vbox = QVBoxLayout()
        self.hbox.addLayout(self.vbox)
        self.hbox.addWidget(self.tb)
        self.vbox.addWidget(self.toolbar)
        self.vbox.addWidget(self.canvas)
        self.vbox.addWidget(self.lb)
        self.tb.setMinimumWidth(200)
        self.setLayout(self.hbox)

        # self.showdata = self.data_reorganised()
        # self.axis= self.xaxisdata()



    def data_reorganised(self):
        reshape= lambda item: (standmark(item[0].hour,item[0].minute),settings.f_account(item[2]),settings.f_source(item[3]),
                               (item[0].strftime('%H:%M') + '\n' + '\n'.join([str(x) for x in item[1:]])))
        return list(map(reshape,db().load(self.day,False)))

    def xaxisdata(self):
        return [data[0] for data in self.showdata ]

    def showheight(self,source_value,account_value=0):
        if self.heightmode==1 and source_value !=0:
            return list(x[1] + x[2] * settings.source_gap if x[2]==source_value else 0 for x in self.showdata)
        elif self.heightmode==1 and account_value !=0:
            return list(x[1] + x[2] * settings.source_gap if x[1] == account_value else 0 for x in self.showdata)
        elif self.heightmode==2 and source_value !=0:
            return list(x[1] * settings.account_gap + x[2] if x[2]==source_value else 0 for x in self.showdata)
        elif self.heightmode==2 and account_value !=0:
            return list(x[1] * settings.account_gap + x[2] if x[1]==account_value else 0 for x in self.showdata)


    def gen_legend(self):
        return settings.legend()

    def draw2(self):
        self.ax.cla()
        self.showdata = self.data_reorganised()
        self.axis = self.xaxisdata()
        self.dayshow = (datetime.now() - timedelta(days=self.day)).strftime('%A %Y-%m-%d')
        self.ax.set_title(self.dayshow)
        self.ax.set_ylim(int(settings.gets('ylim_min')),int(settings.gets('ylim_max')))
        self.ax.set_xlim(standmark(int(settings.gets('start_hour_of_the_day')), 0), standmark(int(settings.gets('end_hour_of_the_day')), 59))
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        self.ax.xaxis.set_major_locator(mdates.HourLocator()) # HourLocator use hour as ticks
        sz = int(settings.gets('basic_point_size'))
        marker_list = settings.gets('marker_style_list')
        if self.heightmode == 1 and self.displaymode == 1:
            self.sclist = [self.ax.scatter(self.axis, self.showheight(i, 0), s=sz , marker=marker_list[i]) for i in
                           range(1, self.srccount + 1)]
        elif self.heightmode ==2 and self.displaymode == 1 :
            self.sclist = [self.ax.scatter(self.axis, self.showheight(0, i), s=sz, marker=marker_list[i]) for i in
                       range(1, self.srccount + 1)]
        elif self.heightmode ==1 and self.displaymode == 2 :
            self.sclist = [self.ax.scatter(self.axis, self.showheight(0, i), s=sz, marker=marker_list[i]) for i in
                           range(1, self.srccount + 1)]
        elif self.heightmode ==2 and self.displaymode == 2 :
            self.sclist = [self.ax.scatter(self.axis, self.showheight(0, i), s=sz, marker=marker_list[i]) for i in
                           range(1, self.srccount + 1)]
        plt.gcf().autofmt_xdate()
        self.fig.canvas.mpl_connect("motion_notify_event", self.hover)
        return len(self.showdata)

    def update_exp(self,ind,sc):
        indx=ind['ind'][0]
        text = self.showdata[indx]
        self.tb.setText(str(text[3]) + "\n" + str(text[2]) + "\n" + str(text[1]))
        try:
            pass
        except:
            pass

    def hover(self,event):
        if event.inaxes == self.ax :
            for sc in self.sclist:
                cont, ind= sc.contains(event)
                if cont:
                    self.update_exp(ind,sc)

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    class Window(QWidget):
        def __init__(self, parent=None):
            super().__init__()
            self.resize(1200, 1200)
            self.btn = QPushButton(self)
            self.sw = ShowWidget(self)
            self.setup_ui()

        def setup_ui(self):
            self.btn.move(50, 20)
            self.btn.resize(500, 40)
            self.sw.move(50, 100)
            self.sw.resize(1000, 700)
            self.btn.clicked.connect(self.loaddata)

        def loaddata(self):
            self.sw.draw2()

    showWin = Window()
    showWin.show()
    sys.exit(app.exec_())

