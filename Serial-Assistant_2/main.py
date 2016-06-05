# -*- coding: utf-8 -*-
import Ui
import sys, struct, serial, time, threading, binascii
from PyQt4 import QtCore, QtGui
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import *


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
        self.settemple.connect(self.settemple, QtCore.SIGNAL('clicked()'), self.settempleProcess) #设置温度
        self.start.connect(self.start, QtCore.SIGNAL('clicked()'), self.startProcess) #开始
        self.stop.connect(self.stop, QtCore.SIGNAL('clicked()'), self.stopProcess) #停止

        self.recievestate = 0 #数据开始处理
        self._data = ""
        #用定时器每个一定时间去扫描有没数据收到，只要在打开串口才开始
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.ReadData)

        #用来实现波形的显示，画图
        self.matplot = MplCanvas()
        self.plot.addWidget(self.matplot)


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
    def StrShow(self,strargv):
        result = ''
        hLen = len(strargv)
        for i in xrange(hLen):
            hvol = ord(strargv[i])
            hhex = '%c'%hvol
            result += hhex+' '
        return result
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
            self.wendu.setPlainText(self.recstr)

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
            self.HexMatplotDisplay(self.recstr)
        else:
            pass

    def WinReFresh1(self,num):
        self.wendu.setPlainText(self.StrShow(self.recstr[num]))


    def SerialSend(self,sdata):  #发送相关
        try:
            self.senddatacnt += self._serial.write(sdata)
        except:
             QtGui.QMessageBox.warning(None, 'Error',"数据格式错误", QtGui.QMessageBox.Ok)

    def settempleProcess(self):
        if self.portstatus_flag == True:
			str_ = self.temple.text()
			str_=str(str_)
 			hex_ = binascii.b2a_hex(str_) 
 			strhex = hex_.decode("hex") 
			self.SerialSend(strhex)

    def HexMatplotDisplay(self,p_str):
    	num2 = ""
        for num in p_str:
        	#print num
        	if num != "/n":
        		num2 += num
        num2.strip()
        self.matplot.matplot_updatabuf(float(num2))
        self.Multiplot_Refresh()

    def Multiplot_Refresh(self):
        if len(self.matplot.plotdatabuf) < self.matplot.databuflimit:
            self.matplot.line1.set_xdata(np.arange(len(self.matplot.plotdatabuf)))
            self.matplot.line1.set_ydata(self.matplot.plotdatabuf)
        else:
            self.matplot.line1.set_xdata(np.arange(self.matplot.databuflimit))
            self.matplot.line1.set_ydata(self.matplot.plotdatabuf[:self.matplot.databuflimit])
        #更新数据后去刷新matplot界面
        self.matplot.ax.relim()
        self.matplot.ax.autoscale_view()
        self.matplot.draw()
   
    def startProcess(self):
    	if self.portstatus_flag == True:
    		str_ = "a"
    		hex_ = binascii.b2a_hex(str_) 
    		strhex = hex_.decode("hex") 
    		self.SerialSend(strhex)
    def stopProcess(self):
    	if self.portstatus_flag == True:
    		str_ = "b"
    		hex_ = binascii.b2a_hex(str_) 
    		strhex = hex_.decode("hex") 
    		self.SerialSend(strhex)

class MplCanvas(FigureCanvas):  #画图
    def __init__(self):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.ax.axis([0,100, 0, 250])
        #self.fig.subplots_adjust(left=0.06, right=0.99, top=0.9, bottom=0.1)
        FigureCanvas.__init__(self, self.fig)
        FigureCanvas.setSizePolicy(self, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.databuflimit = 100
        self.line1, = self.ax.plot([],[],color = 'blue')
        self.plotdatabuf =[]
        self.ax.grid()
        self.ax.hold(False)

    def matplot_updatabuf(self, newdata):
        if len(self.plotdatabuf) >= self.databuflimit:
            del self.plotdatabuf[0]
            try:
                self.plotdatabuf[0] = newdata
            except:
                self.plotdatabuf.append(newdata)
        else:
            self.plotdatabuf.append(newdata)



if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QWidget()
    ui = CKZS(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
