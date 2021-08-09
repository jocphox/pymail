# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets
from PyQt5.Qt import QApplication
import settings
author="David z Yang"
website="www.opentabwest.com"
devdate="2019-12-31"
organization="pwc"
version="0.01"

class aboutMessage(QtWidgets.QMessageBox):
    #此处用类声明，这样就不必非要去实例化了
    def __init__(self,info=""):
        #文字的折行展示
        super().__init__()
        msg="Author:\t\t{0} \nWebsite:\t{1} \
            \nDevdate:\t{2} \nOrganization:\t{3} \nVersion:\t{4} \n\n{5}"\
            .format(author,website,devdate,organization,version,info)
        aboutMessage.information(self,"About",msg)
        print(msg)

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    a=aboutMessage('还在开发中。。')
    sys.exit(app.exec_())