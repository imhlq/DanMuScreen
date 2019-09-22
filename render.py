import sys
if hasattr(sys, 'frozen'):
    os.environ['PATH'] = sys._MEIPASS + ";" + os.environ['PATH']
    
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel,
 QFileDialog, QDesktopWidget, QVBoxLayout, QInputDialog)
from PyQt5.QtCore import Qt, QPropertyAnimation, QPoint, QEasingCurve, QObject, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QFontMetrics
import time, threading
import danmu
import re



class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'Danmu Screen'
        self.DanMu = []
        self.initUI()

    def initUI(self):
        # Set Geometry
        self.setWindowTitle(self.title)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.screen = QDesktopWidget().screenGeometry()
        self.resize(self.screen.width(), self.screen.height())

        # Read Ass File
        fname = self.openFileNameDialog()
        self.StyleList, self.DanmuList = danmu.readAss(fname)
        print(len(self.DanmuList))

        # Go run
        self.shiftTime = 0 # in sec
        self.t0 = time.time()
        self.currentDanMuID = 0

        # for i in range(5):
        #     self.sendOne(self.DanmuList[i])
        # self.tick()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(200)

        

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        #options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","Ass Files (*.ass);; Xml Files (*.xml);; All Files (*.*)", options=options)
        return fileName

    def sendOne(self, danmu):
        # Danmu: ass.event
        TOP_MARGIN = - 50
        IN_MARGIN = 0.7
        #
        dura = (danmu.end - danmu.start) * 1000

        fontMetrics = QFontMetrics(QFont(danmu.fontname, danmu.fontsize))
        fontwidth = fontMetrics.width(danmu.text)
        fontheight = fontMetrics.height()
        
        startX = danmu.startX * self.screen.width() - fontwidth / 2
        endX = danmu.endX * self.screen.width() - fontwidth / 2

        if danmu.type != 3:
            startY = danmu.startY * self.screen.height() * IN_MARGIN + TOP_MARGIN
            endY = danmu.endY * self.screen.height() * IN_MARGIN + TOP_MARGIN
        else:
            startY = danmu.startY * self.screen.height()
            endY = danmu.endY * self.screen.height()


        newD = QLabel(danmu.text, self)
        newD.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        newD.setStyleSheet("font-family:{}; font-size: {}pt; color: {};opacity:0;".format(danmu.fontname, danmu.fontsize, danmu.color))
        newD.show() # NB
        self.fly(newD, dura, (startX,startY), (endX, endY))


    def fly(self, label, duration, sv, ev):
        anim = QPropertyAnimation(label, b"pos")
        did = len(self.DanMu)
        self.DanMu.append(anim)
        self.DanMu[did].setDuration(duration)
        self.DanMu[did].setStartValue(QPoint(*sv))
        self.DanMu[did].setEndValue(QPoint(*ev))
        self.DanMu[did].setEasingCurve(QEasingCurve.Linear)
        self.DanMu[did].start()

        self.DanMu[did].finished.connect(label.deleteLater)



    def tick(self):
        now = time.time()
        elps = now - self.t0 + self.shiftTime
        waitTime = self.DanmuList[self.currentDanMuID].start
        while elps >= waitTime:
            self.sendOne(self.DanmuList[self.currentDanMuID])
            self.currentDanMuID += 1
            waitTime = self.DanmuList[self.currentDanMuID].start
            # Output logging
            hours, rem = divmod(waitTime, 3600)
            minutes, seconds = divmod(rem, 60)
            print(self.currentDanMuID, ("{:0>2}:{:0>2}:{:05.2f}".format(int(hours),int(minutes),seconds)))



    def keyPressEvent(self, event):
        super(App, self).keyPressEvent(event)
        if event.text()== ',':
            if self.currentDanMuID > 5:
                self.shiftTime -= 2
                now = self.DanmuList[self.currentDanMuID].start
                while now - self.DanmuList[self.currentDanMuID-3] < 2:
                    self.DanMu.remove(self.DanMu[-1])
                    self.DanMu.remove(self.DanMu[-2])
                    self.DanMu.remove(self.DanMu[-3])
                    self.currentDanMuID -= 3

        elif event.text() == '.':
            self.shiftTime += 2
            now = self.DanmuList[self.currentDanMuID].start
            while self.DanmuList[self.currentDanMuID+5].start - now < 2:
                self.currentDanMuID += 5

        elif event.key() == Qt.Key_Space:
            i, okpressed = QInputDialog.getInt(self, "Please input progress", "percentage:", 0, 0, 100, 1)
            if okpressed:
                self.currentDanMuID = int(len(self.DanmuList) * (i / 100))
                self.shiftTime = self.DanmuList[self.currentDanMuID].start

if __name__ == "__main__":
    app = QApplication([])
    ex = App()
    ex.show()
    app.exec_()