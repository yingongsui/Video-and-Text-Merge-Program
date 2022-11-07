#完全的多线程，计时和文件处理都是单独的线程
from PySide6.QtWidgets import QApplication, QMessageBox,QFileDialog,QMainWindow,QProgressBar,QTextEdit
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile,QTimer,QThread,Signal
import os
import cv2
import re
import subprocess
import sys
from MyOwnWidgets import MyTextViewer,MyTextEdit

import time

def wtxt(fname,outfile):                                #ffmpeg不支持数组传递，需要txt文件
    ftxt = open(outfile,'w')
    for line in fname:
        ftxt.write(line + '\n')
    ftxt.close()

def getvideoinfo(fname):                        #用cv2获取视频信息
    cap = cv2.VideoCapture(fname)
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    return (width,height,round(frames))             #返回总帧数

def isexist(allfilelist,merglist,ffmpegpath,Wid):
        if bool(allfilelist) == False:                   #没有文件的话，输出消息
            textadd(Wid,"Please select files")    #没有选择文件时
            return(False)
        elif ".txt" in allfilelist[0] :                 #文本文件的话直接返回列表
            return(True)
        elif os.path.exists(ffmpegpath) == False:                   #没有ffmpeg的话，输出消息
            QMessageBox.about(None,"Message","Can't find ffmpeg.exe")
            textadd(Wid,"Can't find ffmpeg.exe")    #没有选择文件时
            return(False)
        else:                                           #视频文件的话创建txt合并列表
            wtxt(allfilelist, merglist)                      #除了用wtxt创建永久文件之外，是否也能创建临时文件 
            return (True)

def typecheck(filelist):        #文件格式
    filetype = ['.mp4','.avi','.txt','.mp3','.aac']
    
    i = 0
    for t in filetype:
        if t in filelist:
                return(t)

    return(False)

def findpreframe(line):         #找到现在帧数
    if "frame=" in line:
        #line = line.strip(" ")              #去掉空格
        preframe = re.search(r'\d+',line)   #找到第一个数字，对应于帧数
        return(int(preframe[0]))
    else:
        pass

def textadd(Wid,nline):            #文本框中加入文件
    Wid.setText(str(Wid.toPlainText()) + nline + "\n")  #此处是加上已经存在于框内的文字

finicheck = False
outname = ""

#主窗体
class VideoMerge(QMainWindow):      #新建的类是从QDialog继承下来的，将ui布局中的元素全部传递进来，作为MainWindow函数的参数
    def __init__(self):
        QUiLoader().registerCustomWidget(MyTextViewer)                          #导入自定义模块
        QUiLoader().registerCustomWidget(MyTextEdit)                          #导入自定义模块

        ui_inf = QFile("E:\\Programming\\Python\\GUI\\video merge\\videomerge.ui")        #导入布局文件
        ui_inf.open(QFile.ReadOnly)
        self.ui = QUiLoader().load(ui_inf)
        ui_inf.close()
        #控件行为设置
        self.ui.File1Button.clicked.connect(self.find_file)     #self.ui.控件名.控件行为.连接函数
        self.ui.mergeButton.clicked.connect(self.merge_files)
        self.ui.clearButton.clicked.connect(self.clear_all)
        self.ui.ffmpegButton.clicked.connect(self.getffmpeg)
        self.ui.extractButton.clicked.connect(self.exa_file)
        self.ui.avmButton.clicked.connect(self.merge_AV)
        self.ui.testButton.clicked.connect(self.testhreads)
        #self.ui.textEdit.textChanged.connect(self.editchange)

        #各种参数，文件位置
        #self.i = 0              #按键次数记录变量
        self.openfilepath = os.path.abspath(os.path.dirname("__file__"))        #文件位置，初始位置定于程序所在目录
        self.ffmpegpath = "ffmpeg.exe"

        self.step = 0
        self.ui.progressBar.setValue(self.step)

        self.timethreadtest = Timecount()         #测试计时线程
        #self.timethread = Timecount()         #是否应该设置总计时线程，而不是在每个函数里设置分线程》》不能设置总进程，会有数据残留


    def getffmpeg(self):
        if self.ui.textEdit.toPlainText():      #优先文本框中文件地址
            if os.path.exists(self.ui.textEdit.toPlainText()):
                self.ffmpegpath = self.ui.textEdit.toPlainText()
            else:
                QMessageBox.about(None,"Message","Can't find ffmpeg.exe")
        elif os.path.exists('E:/Programming/Python/ffmpeg/bin/ffmpeg.exe'):      #其次本目录中文件地址
            self.ffmpegpath = "E:/Programming/Python/ffmpeg/bin/ffmpeg.exe"
            self.ui.textEdit.setText(self.ffmpegpath)
        else:
            QMessageBox.about(None,"Message","Can't find ffmpeg.exe")
            textadd(self.ui.MyTBrowser,"Can't find ffmpeg.exe")
            return
        textadd( self.ui.MyTBrowser , ">>>>ffmpeg path : " + self.ffmpegpath )

    def find_folder(self):
        rootpath = os.path.abspath(os.path.dirname("__file__"))     #返回当前文件目录
        textadd(self.ui.MyTBrowser ,rootpath)   #显示rootpath
        fname = QFileDialog.getExistingDirectory(None, "Please select a director", rootpath)    #打开选择的文件目录，并将值返回和fname    
        textadd(self.ui.MyTBrowser ,fname)      #显示文件路径

    def find_file(self):
        fname = QFileDialog.getOpenFileNames(None, "Please select files", self.openfilepath)        

        #打开选择的文件目录，并将值返回和fname，返回值为元组[文件路径，文件类型]
        if len(fname[0]) == 0 and self.ui.MyTBrowser.allfileslist == [] :   #文本框记录的列表为空
            textadd(self.ui.MyTBrowser , "Please select files" )    #没有选择文件时
        else:
            for fn in fname[0]:
                self.ui.MyTBrowser.filenum += 1
                textadd(self.ui.MyTBrowser,"File " + str(self.ui.MyTBrowser.filenum) + " : " + fn)
                prefilepath = os.path.split(fn)           #将所在文件位置进行分割，返回值为元组(文件目录，文件)
                self.ui.MyTBrowser.filepath = prefilepath[0]            #更新位置为当前文件位置
                self.openfilepath = prefilepath[0]             #设定下次打开文件路径
                if ".txt" in fn:
                    pass
                elif typecheck(fn) == ".mp4" :           #若是视频文件，获取视频信息，并将txt文件地址变为ffmpeg可识别的内容格式
                    (w,h,frames) = getvideoinfo(fn)       #获取长宽帧数
                    tem = "Resolution : " + str(w) + "x" + str(h) +"  Frames : " + str(frames)
                    textadd(self.ui.MyTBrowser ," "*(10+len(str(self.ui.MyTBrowser.filenum))) + "->" + tem)
                    self.ui.MyTBrowser.allframes += frames
                    fn = "file " + "\'" + fn + "\'"           #若是视频文件，获取视频信息，并将txt文件地址变为ffmpeg可识别的内容格式
                else:
                    QMessageBox.about(None,"Message","File type is wrong!!")
                self.ui.MyTBrowser.allfileslist.append(fn)                   #将新选择的文件添加进列表
    
    def merge_files(self):
        allfileslist = self.ui.MyTBrowser.allfileslist       #总的文件列表
        merglist = self.ui.MyTBrowser.filepath + "/mergelist.txt"       #输出txt列表地址
        exis = isexist(allfileslist,merglist,self.ffmpegpath,self.ui.MyTBrowser)       #判断是否输入文件并显示在文本框中 

        #输出文件名设定
        global outname       
        if exis and self.ui.typecomboBox.currentText():   #选择了文件类型
            outname = self.ui.MyTBrowser.filepath + "/newmergefile" + self.ui.typecomboBox.currentText()
            self.ui.progressBar.setRange(0,self.ui.MyTBrowser.allframes)
        elif exis and not self.ui.typecomboBox.currentText():   #没有选择文件类型
            if  typecheck(allfileslist[0]) == ".txt":
                outname = self.ui.MyTBrowser.filepath + "/newmergefile.txt"    #返回原格式
                self.ui.progressBar.setRange(0,self.ui.MyTBrowser.alllines)               
            else:
                outname = self.ui.MyTBrowser.filepath + "/newmergefile" +  str(typecheck(allfileslist[0]))     #返回原格式
                self.ui.progressBar.setRange(0,self.ui.MyTBrowser.allframes)
        else:
            return
        #####################################多线程不允许操作UI借用emit实现对UI的操作###############################################

        if(exis):
            self.timethread = Timecount()         #设置计时线程
            self.timethread.start()                                 #启动计时线程，会自动调用其中的run()
            self.timethread.trigger.connect(self.TimerandReset)             #将信号传给主程序，由主程序来改变UI界面

            self.mergethread = Merge(allfileslist,merglist,outname,self.ffmpegpath)          #设置合并进程
            self.mergethread.start()
            self.mergethread.trigger.connect(self.PGBState)
        else:
            return

    def exa_file(self):
        allfileslist = self.ui.MyTBrowser.allfileslist       #总的文件列表
        global outname
        if not allfileslist:
            textadd(self.ui.MyTBrowser , "Please select a file" )
            return
        elif os.path.exists(self.ffmpegpath) and self.ui.exacomboBox.currentText():   #有文件有类型
            inname = allfileslist[0].strip("file '")
            outname = self.ui.MyTBrowser.filepath + "/newexatractfile" + self.ui.exacomboBox.currentText()
            if self.ui.exacomboBox.currentText() == '.mp4':
                self.ui.progressBar.setRange(0,self.ui.MyTBrowser.allframes)
            else:
                self.ui.progressBar.setRange(0,self.ui.MyTBrowser.duration)
            
            self.timethread = Timecount()         #设置计时线程
            self.timethread.start()                                 #启动计时线程，会自动调用其中的run()
            self.timethread.trigger.connect(self.TimerandReset)        #将信号传给主程序，由主程序来改变UI界面

            self.exathread = VideoExa(allfileslist,inname,outname,self.ffmpegpath)          #设置合并进程
            self.exathread.start()
            self.exathread.trigger.connect(self.PGBState)
 
        else:
            QMessageBox.about(None,"Message","File type is unsupported!!")
            
    def merge_AV(self):      
        allfileslist = self.ui.MyTBrowser.allfileslist       #总的文件列表
        merglist = self.ui.MyTBrowser.filepath + "/mergelist.txt"       #输出txt列表地址
        if not (allfileslist == []):
            if ".aac" in allfileslist[0]:       #判断是否输入文件
                ina = allfileslist[0]
                inv = allfileslist[1].strip("file '")
            elif ".aac" in allfileslist[1]:
                ina = allfileslist[1]
                inv = allfileslist[0].strip("file '")
        else:
            textadd(self.ui.MyTBrowser ,"Please check the input files!!" )
            return
        
        global outname
        exis = isexist(allfileslist,merglist,self.ffmpegpath,self.ui.MyTBrowser)      #判断是否输入文件
        outname = self.ui.MyTBrowser.filepath + "/newmergefile.mp4"
        
        self.ui.progressBar.setRange(0,self.ui.MyTBrowser.allframes)
        
        if exis:                                #存在文件
            self.timethread = Timecount()         #设置计时线程
            self.timethread.start()                                 #启动计时线程，会自动调用其中的run()
            self.timethread.trigger.connect(self.TimerandReset)        #将信号传给主程序，由主程序来改变UI界面

            self.avmthread = AVMerge(ina,inv,outname,self.ffmpegpath)          #设置合并进程
            self.avmthread.start()
            self.avmthread.trigger.connect(self.PGBState)
            os.remove(merglist)             #删除临时列表       
        else:
            return

    def TimerandReset(self,state):
        global finicheck
        global outname
        if not state[1]:                #未完成      
            self.ui.lcdNumber.display(state[0])
        else:                           #完成后重置变量
            textadd(self.ui.MyTBrowser,"Output as " +  outname + " Succeffful!!") 
            self.ui.MyTBrowser.allframes = 0
            self.ui.MyTBrowser.alllines = 0
            self.ui.MyTBrowser.filepath = ""
            self.ui.MyTBrowser.allfileslist = []
            self.ui.MyTBrowser.filenum = 0
            self.ui.MyTBrowser.duration = 0
            finicheck = False
            outname = ""

    def MergeState(self,s):
        textadd(self.ui.MyTBrowser,s)

    def PGBState(self,s):
        self.ui.progressBar.setValue(s)

    def clear_all(self):
        self.ui.MyTBrowser.allframes = 0
        self.ui.MyTBrowser.alllines = 0
        self.ui.MyTBrowser.filepath = ""
        self.ui.MyTBrowser.allfileslist = []
        self.ui.MyTBrowser.filenum = 0
        self.ui.MyTBrowser.duration = 0
        self.ui.MyTBrowser.setText("")  #清空文本框
        self.ui.progressBar.setValue(0)
        self.ui.lcdNumber.display(0)
        global finicheck
        finicheck = False


#####################################测试部分################################################################
    def testhreads(self):
        global finicheck
        if not self.timethreadtest.isRunning():
            self.timethreadtest.start()
            self.timethreadtest.trigger.connect(self.testpart) 
            self.ui.testButton.setText("Stop")
        else:
            self.timethreadtest.terminate()
            self.ui.testButton.setText("Test")

    def testpart(self,state):
        global finicheck
        if not state[1]:                #未完成      
            self.ui.testlcdNumber.display(state[0])
        else:                           #完成后重置变量
            textadd(self.ui.MyTBrowser,"Test Complete") 
            finicheck = False

#定义合并多线程类
class Merge(QThread):            #合并线程
    trigger = Signal(int)        #实时传递帧率
    #对应参数为:列表格式的文件列表，路径，输出名，
    def __init__(self,allfilelist,mergelist,outname,ffmpegpath ):
        super(Merge,self).__init__()

        self.allfilelist = allfilelist      #文件列表
        self.mergelist = mergelist        #生成合并列表文件
        self.outname = outname
        self.ffmpegpath = ffmpegpath

    def run(self):
        if ".txt" in self.allfilelist[0]:                            #是文本文件
            f = open(self.outname,'w',encoding="utf8")           #建立新文件，编码不是utf8的话可能会出现转码错误
            nowline = 0
            for filename in self.allfilelist:         #遍历inname的list中文件名  
                for line in open(filename,encoding="utf8"):  
                    f.writelines(line)      #行写入
                    nowline += 1
                    self.trigger.emit(nowline)
                f.write('\n')  
            #关闭文件  
            f.close()  

        elif typecheck(self.allfilelist[0]):                 #非文本文件
            cmd =self.ffmpegpath + " -f concat -safe 0 -y -i \"" + self.mergelist + "\" -c copy -strict -2 \"" + self.outname + "\""
            #获取子程序进度
            process = subprocess.Popen(cmd, shell = True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,stdin = subprocess.PIPE,universal_newlines=True)
            for line in process.stdout:
                if "frame=" in line:
                    #line = line.strip(" ")              #去掉空格
                    preframe = re.search(r'\d+',line)   #找到第一个数字，对应于当前帧数
                    self.trigger.emit(int(preframe[0]))
            else:
                pass
            os.remove(self.mergelist)             #删除临时列表
        else:
            #QMessageBox.about(None,"Message","File type is unsupported!!")
            #self.trigger.emit("File type is unsupported!!")
            self.trigger.emit(0)

        global finicheck
        finicheck = True  

class VideoExa(QThread):
    trigger = Signal(float)        #实时传递帧率或时间
    #对应参数为:列表格式的文件列表，路径，输出名，
    def __init__(self,allfilelist,inname,outname,ffmpegpath ):
        super(VideoExa,self).__init__()

        self.allfilelist = allfilelist      #文件列表
        self.inname = inname        #生成合并列表文件
        self.outname = outname
        self.ffmpegpath = ffmpegpath

    def run(self):
        if ".mp4" in self.outname:              #提取视频
            cmd = self.ffmpegpath + " -i \"" + self.inname + "\" -vcodec copy -an \"" + self.outname + "\" -y"
            process = subprocess.Popen(cmd, shell = True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,stdin = subprocess.PIPE,universal_newlines=True)
            for line in process.stdout:
                if findpreframe(line):
                    self.trigger.emit(findpreframe(line))      #进度条设置
        else:                                   #提取音频
            cmd = self.ffmpegpath + " -i \"" + self.inname + "\" -vn -y -acodec copy \"" + self.outname + "\" -y"
            process = subprocess.Popen(cmd, shell = True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,stdin = subprocess.PIPE,universal_newlines=True)
            for line in process.stdout:
                if "size=" in line and "N/A" not in line:
                    pretime = re.search(r'\d+:\d+:\d+.\d+',line)   #找到第一个数字，对应于帧数
                    t = pretime[0]
                    h,m,s = t.strip().split(":")
                    self.trigger.emit(int(h)*3600+int(m)*60+float(s))
                else:
                    pass
        
        global finicheck
        finicheck = True  

class AVMerge(QThread):
    trigger = Signal(int)        #实时传递帧率或时间
    #对应参数为:列表格式的文件列表，路径，输出名，
    def __init__(self,ina,inv,outname,ffmpegpath ):
        super(AVMerge,self).__init__()
        self.ina = ina                     #音频
        self.inv = inv                      #视频
        self.outname = outname
        self.ffmpegpath = ffmpegpath

    def run(self):
        if self.ina and self.inv:
            cmd = self.ffmpegpath + " -i \"" + self.ina + "\" -i \"" + self.inv  + "\" -c:v copy -c:a aac -strict experimental \"" + self.outname + "\" -y"
        else:
            cmd = self.ffmpegpath + " -i \"" + self.ina + "\" -i \"" + self.inv  + "\" -c:v copy -c:a aac -strict experimental -map 0:v:0 -map 1:a:0 \"" + self.outname + "\" -y"
        
        process = subprocess.Popen(cmd, shell = True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,stdin = subprocess.PIPE,universal_newlines=True)
        for line in process.stdout:
            if findpreframe(line):
                self.trigger.emit(findpreframe(line))      #当前帧率
                #print(findpreframe(line))

        global finicheck
        finicheck = True 

#计时多线程
class Timecount(QThread):            #为LCD显示提供多线程
    trigger = Signal(list)           #该线程传输的信号是一个数字，即当前耗时

    def __init__(self):
        super(Timecount,self).__init__()
        # self.timer = QTimer()         #定时器无法在子进程中创建
        # self.costtime = 0
        # self.timer.timeout.connect(self.addtime)

    def run(self):
        #self.timer.start(1000)          #启动计时器
        i = 0.0
        global finicheck
        while not finicheck :
            time.sleep(0.1)
            i += 0.1
            self.trigger.emit([i,False])    #输出计时和状态

        self.trigger.emit([i,True])



if __name__ == "__main__":
    app = QApplication([])
    vm = VideoMerge()
    vm.ui.show()
    app.exec()

 

