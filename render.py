from PyQt5.QtWidgets import (QApplication, QWidget, QLabel,
 QFileDialog, QDesktopWidget, QVBoxLayout)
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
        self.StyleList, self.Danmulist, self.playxy = danmu.readAss(fname)
        print(len(self.Danmulist))

        # Render Text
        self.Styles = {}
        for sty in self.StyleList:
            self.Styles[sty.name] = "font-family:{}; font-size: {}pt; color: rgba({},{},{},{});".format(sty.fontname, sty.fontsize*0.8, sty.primary_color.r, sty.primary_color.g, sty.primary_color.b, sty.primary_color.a)

        # Go run
        self.shiftTime = 0 # in sec
        self.t0 = time.time()
        self.currentDanMuID = 0

        # for i in range(5):
        #     self.sendOne(self.Danmulist[i])
        # self.tick()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(200)

        

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        #options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;Ass Files (*.ass)", options=options)
        return fileName

    def sendOne(self, danmu):
        # Danmu: ass.event
        TOP_Margin = - 50
        IN_Margin = 0.7
        #
        dura = (danmu.end - danmu.start).seconds * 1000
        sty = danmu.style
        text = "".join(danmu.text.split('}')[1:])

        fontMetrics = QFontMetrics(QFont('Microsoft YaHei UI', 25))
        fontwidth = fontMetrics.width(text)

        if sty == 'R2L':
            pos = re.findall(r"([-]?[0-9]{1,}[.]?[0-9]*)", danmu.text)[0:4]
            startX = self.screen.width() + float(pos[0]) - self.playxy[0]
            startY = float(pos[1]) * (self.screen.height() / self.playxy[1]) * IN_Margin + TOP_Margin
            endX = - fontwidth
            endY = float(pos[3]) * (self.screen.height() / self.playxy[1]) * IN_Margin + TOP_Margin
        else:
            pos = re.findall(r"([-]?[0-9]{1,}[.]?[0-9]*)", danmu.text)[0:2]
            startX = (self.screen.width() - fontwidth) / 2
            startY = float(pos[1]) * (self.screen.height() / self.playxy[1])
            endX = startX
            endY = startY

        newD = QLabel(text, self)
        newD.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        
        newD.setStyleSheet(self.Styles[sty])
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
        waitTime = self.Danmulist[self.currentDanMuID].start.total_seconds()
        while elps >= waitTime:
            self.sendOne(self.Danmulist[self.currentDanMuID])
            self.currentDanMuID += 1
            waitTime = self.Danmulist[self.currentDanMuID].start.total_seconds()
            # print(self.currentDanMuID, waitTime)


    def keyPressEvent(self, event):
        super(App, self).keyPressEvent(event)
        if event.text()== ',':
            self.currentDanMuID = max(self.currentDanMuID - 3, 0)
            self.shiftTime -= 1
        elif event.text() == '.':
            self.currentDanMuID = min(self.currentDanMuID + 3, 99999)
            self.shiftTime += 1


if __name__ == "__main__":
    app = QApplication([])
    ex = App()
    ex.show()
    app.exec_()