# -*- coding: utf-8 -*-
import Ui
import sys, struct, serial, time, threading
from PyQt4 import QtCore, QtGui

reload(sys)
sys.setdefaultencoding('utf-8')
#全局变量
#数据位
SERIAL_DATABIT_ARRAY = (serial.EIGHTBITS, serial.SEVENBITS, serial.SIXBITS, serial.FIVEBITS)
#停止位
SERIAL_STOPBIT_ARRAY = (serial.STOPBITS_ONE, serial.STOPBITS_ONE_POINT_FIVE, serial.STOPBITS_TWO)
#校验位
SERIAL_CHECKBIT_ARRAY = (serial.PARITY_NONE, serial.PARITY_EVEN, serial.PARITY_ODD , serial.PARITY_MARK, serial.PARITY_SPACE)

class CKZS(Ui.Ui_Form):
    #初始化
    def __init__(self,Ui_Form):
        super(Ui.Ui_Form, self).__init__()
        self.setupUi(MainWindow) #显示主窗口
        self.portstatus_flag = False #端口使能标志
        self._serial = serial.Serial() #i初始化串口

        self.recstr = str #串口接收字符串
        self.recdatacnt = 0 #数据接收计数
        self.senddatacnt = 0 # 数据发送是计数

        self.qingchuneirong.connect(self.qingchuneirong, QtCore.SIGNAL('clicked()'), self.qingchuneirongProcess)
        self.chuankouopen.connect(self.chuankouopen, QtCore.SIGNAL('clicked()'), self.chuankouopen_Click) #打开串口操作
        self.lingchunwei.connect(self.lingchunwei, QtCore.SIGNAL('clicked()'), self.lingchunweiProcess)

        self.recievestate = 0 #数据开始处理
        self._data = ""
        #用定时器每个一定时间去扫描有没数据收到，只要在打开串口才开始
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.ReadData)


    def chuankouopen_Click(self):
        clickstatus = self.chuankouopen.isChecked() #串口开关状态检查
        if clickstatus: #如果开关为打开状态
            #获得串口参数
            comread = int(self.comport.text())-1 #端口号，计算机端口都是从0开始算的，所以减去1
            bandrate = int(self.botelv.currentText()) #波特率
            databit = SERIAL_DATABIT_ARRAY[self.shujuwei.currentIndex()] #数据位
            stopbit = SERIAL_STOPBIT_ARRAY[self.jiaoyanwei.currentIndex()] #校验位
            checkbit = SERIAL_CHECKBIT_ARRAY[self.tingzhiwei.currentIndex()] #停止位

            #打开串口
            try:
                self._serial = serial.Serial(comread)
                self._serial.baudrate = bandrate
                self._serial.bytesize = databit
                self._serial.parity = checkbit
                self._serial.stopbits = stopbit
            except (OSError, serial.SerialException): #错误信息
                QtGui.QMessageBox.warning(None, 'Error',"Invalid Serial Port", QtGui.QMessageBox.Ok)

            if self._serial.isOpen():
                self.timer.start(300)   #定时器30ms刷新一次界面
                self.botelv.setEnabled(False) #波特率
                self.jiaoyanwei.setEnabled(False) #校验位
                self.shujuwei.setEnabled(False) #数据位
                self.tingzhiwei.setEnabled(False) #停止位
                self.comport.setEnabled(False) #端口
                self.chuankouopen.setText("Close") #串口打开成功之后，按钮由“打开”变为“关闭”
                self.portstatus_flag = True
            else:
                self.chuankouopen.setChecked(False) #如果串口没有打开成果，按钮回复为未打开状态
        else:   #关闭串口、使能各个窗口
            self._serial.close()
            self.timer.stop()
            self.botelv.setEnabled(True) #波特率
            self.jiaoyanwei.setEnabled(True) #校验位
            self.shujuwei.setEnabled(True) #数据位
            self.tingzhiwei.setEnabled(True) #停止位
            self.comport.setEnabled(True) #端口
            self.chuankouopen.setText("Open")
            self.portstatus_flag = False

    def qingchuneirongProcess(self):#接收窗口清楚数据
        if self.distext.currentIndex() == 0:
            self.dishex.clear()
        elif self.distext.currentIndex() == 1:
            self.distring.clear()

    # def HexShow(self,strargv):#转换陈十六进制格式显示
    #     restr = ''
    #     slen = len(strargv)
    #     for i in range(slen):
    #         restr += int(strargv[i],)+' '
    #     return restr
    def HexShow(self,strargv):#转换陈十六进制格式显示
        result = ''
        hLen = len(strargv)
        for i in xrange(hLen):
            hvol = ord(strargv[i])
            hhex = '%02X'%hvol
            result += hhex+' '
        return result
    def intShow(self,strargv):#转换陈十六进制格式显示
        hvol = ord(strargv)
        hhex = '%d'%hvol
        return hhex
    def intShow1(self,strargv):#转换陈十六进制格式显示
        hvol = ord(strargv) / 10
        hhex = '%d'%hvol
        return hhex
    def intShow11(self,strargv):#转换陈十六进制格式显示
        hvol = ord(strargv) / 10
        hhex = '%02d'%hvol
        return hhex
    def intShow2(self,strargv):#转换陈十六进制格式显示
        hvol = ord(strargv) % 10
        hhex = '%d'%hvol
        return hhex
    def intShow3(self,strargv):#转换陈十六进制格式显示
        hvol = ord(strargv) / 100
        hhex = '%d'%hvol
        return hhex
    def intShow4(self,strargv):#转换陈十六进制格式显示
        hvol = ord(strargv) % 100
        hhex = '%02d'%hvol
        return hhex
    # def StrShow(self,strargv):
    #     result = ''
    #     hLen = len(strargv)
    #     for i in xrange(hLen):
    #         hvol = ord(strargv[i])
    #         hhex = '%c'%hvol
    #         result += hhex+' '
    #     return result
    def lingchunweiProcess(self): #保存数据
        filename = QtGui.QFileDialog.getSaveFileName(self.lingchunwei, 'Save File', '.',"Text file(*.txt);;All file(*.*)")
        fname = open(filename, 'w')
        if self.distext.currentIndex() == 0:
            fname.write(self.dishex.toPlainText())
        elif self.distext.currentIndex() == 1:
            fname.write(self.distring.toPlainText())
        fname.close()
    def Prossess_data(self,strargv):
        for i in range(len(strargv)):
            hvol = ord(self.recstr[i])
            hhex = '%02X'%hvol
        #    self.WinReFresh1(i)
            if(hvol== 0x0A):
                self.recievestate = 1
            if(self.recievestate ==1 and hvol== 0x55):
                self.recievestate = 2
                continue
            if(self.recievestate == 2):
                if(i < len(strargv)-1):
                    self.WinReFresh1(i)
                self.recievestate = 3
                continue
            if(self.recievestate == 3):
                self.recievestate = 4
                continue
            if(self.recievestate == 4):
                if(i < len(strargv)-1):
                    self.WinReFresh2(i)
                self.recievestate = 5
                continue
            if(self.recievestate == 5):
                self.recievestate = 6
                continue
            if(self.recievestate == 6):
                if(i < len(strargv)-1):
                    self.WinReFresh3(i)
                self.recievestate = 7
                continue
            if(self.recievestate == 7):
                self.recievestate = 8
                continue
            if(self.recievestate == 8):
                if(i < len(strargv)-1):
                    self.WinReFresh4(i)
                self.recievestate = 9
                continue
            if(self.recievestate == 9):
                self.recievestate = 10
                continue
            if(self.recievestate == 10):
                if(i < len(strargv)-1):
                    self.WinReFresh5(i)
                self.recievestate = 11
                continue
            if(self.recievestate == 11):
                self.recievestate == 0
                continue
            if(hvol==0x6B):
                self.recievestate = -1
            if(hvol==0x6B and self.recievestate== -1):
                self.recievestate = 0
    def ReadData(self):#deal sci data
        if self.portstatus_flag == True:
            try:
                bytesToRead = self._serial.inWaiting()#读取缓冲区有多少数据
            except:
                self.chuankouopen.setChecked(False)#出现异常，则关闭串口
                self.chuankouopen_Click()
                bytesToRead = 0

            if bytesToRead > 0:#大于0 ，则取出数据
                self.recstr = self._serial.read(bytesToRead)#读取串口数据
                self.recdatacnt += bytesToRead
                self.WinReFresh()#根据选择，来判断数据在那个窗口刷新
                self.Prossess_data(self.recstr)

    def WinReFresh(self):
        if self.distext.currentIndex() == 0:
            self.dishex.appendPlainText(self.HexShow(self.recstr))#把数据按十六进制显示
            if self.dishex.toPlainText().__len__() > 100000:
                self.dishex.clear()
        else:
            pass

    def WinReFresh1(self,num):
        if(self.intShow(self.recstr[num])=='0'):
            self.wendu.setPlainText(self.intShow1(self.recstr[num+1])+'.'+self.intShow2(self.recstr[num+1]))#把数据按十六进制显示
        else:
            self.wendu.setPlainText(self.intShow(self.recstr[num])+self.intShow1(self.recstr[num+1])+'.'+self.intShow2(self.recstr[num+1]))
    def WinReFresh2(self,num):
            self.PH.setPlainText(self.intShow(self.recstr[num])+'.'+self.intShow(self.recstr[num+1]))#把数据按十六进制显示
    def WinReFresh3(self,num):
        self.yanghuahuanyuan.setPlainText(self.intShow(self.recstr[num])+self.intShow11(self.recstr[num+1])+'.'+self.intShow2(self.recstr[num+1]))#把数据按十六进制显示
    def WinReFresh4(self,num):
        if(self.intShow(self.recstr[num])=='0'):
            self.diandaolv.setPlainText(self.intShow(self.recstr[num+1]))#把数据按十六进制显示
        else:
            self.diandaolv.setPlainText(self.intShow(self.recstr[num])+self.intShow(self.recstr[num+1]))#把数据按十六进制显示
    def WinReFresh5(self,num):
        if(self.intShow(self.recstr[num])=='0'):
            self.zuodu.setPlainText(self.intShow(self.recstr[num+1]))#把数据按十六进制显示
        else:
            self.zuodu.setPlainText(self.intShow(self.recstr[num])+self.intShow(self.recstr[num+1]))#把数据按十六进制显示

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QWidget()
    ui = CKZS(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
