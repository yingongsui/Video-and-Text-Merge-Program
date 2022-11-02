from PySide6.QtWidgets import QApplication, QMessageBox,QFileDialog,QMainWindow,QProgressBar,QTextEdit
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile,QTimer
import os
import cv2
import re
import subprocess
import sys
from MyOwnWidgets import MyTextViewer,MyTextEdit


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

def isexist(allfilelist,merglist,ffmpegpath,addtext):
        if bool(allfilelist) == False:                   #没有文件的话，输出消息
            addtext("Please select files")    #没有选择文件时
            return(False)
        elif ".txt" in allfilelist[0] :
            return(True)
        elif os.path.exists(ffmpegpath) == False:                   #没有ffmpeg的话，输出消息
            QMessageBox.about(None,"Message","Can't find ffmpeg.exe")
            addtext("Can't find ffmpeg.exe")    #没有选择文件时
            return(False)
        else:
            wtxt(allfilelist, merglist)                      #除了用wtxt创建永久文件之外，是否也能创建临时文件 
            return (True)

def typecheck(filelist):
    filetype = ['.mp4','.avi','.txt','.mp3','.aac']
    
    i = 0
    for t in filetype:
        if t in filelist:
            i += 1
            if i:
                return(t)

    return(False)

def findpreframe(line):
    if "frame=" in line:
        #line = line.strip(" ")              #去掉空格
        preframe = re.search(r'\d+',line)   #找到第一个数字，对应于帧数
        return(int(preframe[0]))
    else:
        pass

def txtmerge(inname,outname,progbar):       #inname是文件list的txt文件
    f = open(outname,'w',encoding="utf8")           #建立新文件，编码不是utf8的话可能会出现转码错误
    #统计总行数
    count = 0
    for filename in inname:         #遍历inname的list中文件名
        count += len(open(filename,'r',encoding="utf8").readlines())  
    #进度条设置
    progbar.setRange(0,count)
    nowline = 0
    for filename in inname:         #遍历inname的list中文件名  
        for line in open(filename,encoding="utf8"):  
            f.writelines(line)      #行写入
            nowline += 1
            progbar.setValue(nowline)
        f.write('\n')  
    #关闭文件  
    f.close()

def videomerge(inname,outname,progbar,allframes,ffmpegpath):
    progbar.setRange(0,allframes)
    cmd = ffmpegpath + " -f concat -safe 0 -y -i \"" + inname + "\" -c copy -strict -2 \"" + outname + "\""
    process = subprocess.Popen(cmd, shell = True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,stdin = subprocess.PIPE,universal_newlines=True)
    for line in process.stdout:
        if "frame=" in line:
            #line = line.strip(" ")              #去掉空格
            preframe = re.search(r'\d+',line)   #找到第一个数字，对应于帧数
            progbar.setValue(int(preframe[0]))
        else:
            pass

def videoexa(inname,outname,progbar,allframes,ffmpegpath):
    if ".mp4" in outname:
        progbar.setRange(0,allframes)
        cmd = ffmpegpath + " -i \"" + inname + "\" -vcodec copy -an \"" + outname + "\" -y"
        process = subprocess.Popen(cmd, shell = True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,stdin = subprocess.PIPE,universal_newlines=True)
        for line in process.stdout:
            if findpreframe(line):
                progbar.setValue(findpreframe(line))      #进度条设置
    else:
        cmd = ffmpegpath + " -i \"" + inname + "\" -vn -y -acodec copy \"" + outname + "\" -y"
        process = subprocess.Popen(cmd, shell = True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,stdin = subprocess.PIPE,universal_newlines=True)
        for line in process.stdout:
            if "Duration:" in line:
                duration = re.search(r'\d+:\d+:\d+.\d+',line)   #找到第一个数字，对应于帧数
                t = duration[0]
                h,m,s = t.strip().split(":")
                progbar.setRange(0,int(h)*3600+int(m)*60+float(s))
            else:
                pass

            if "size=" in line and "N/A" not in line:
                pretime = re.search(r'\d+:\d+:\d+.\d+',line)   #找到第一个数字，对应于帧数
                t = pretime[0]
                h,m,s = t.strip().split(":")
                progbar.setValue(int(h)*3600+int(m)*60+float(s))
            else:
                pass


def AVmerge(ina,inv,outname,progbar,allframes,ffmpegpath):
    progbar.setRange(0,allframes)
    if 1:
        cmd = ffmpegpath + " -i \"" + ina + "\" -i \"" + inv  + "\" -c:v copy -c:a aac -strict experimental \"" + outname + "\" -y"
    else:
        cmd = ffmpegpath + " -i \"" + ina + "\" -i \"" + inv  + "\" -c:v copy -c:a aac -strict experimental -map 0:v:0 -map 1:a:0 \"" + outname + "\" -y"
    process = subprocess.Popen(cmd, shell = True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,stdin = subprocess.PIPE,universal_newlines=True)
    for line in process.stdout:
        if findpreframe(line):
            progbar.setValue(findpreframe(line))      #进度条设置
    




class VideoMerge(QMainWindow):      #新建的类是从QDialog继承下来的，将ui布局中的元素全部传递进来，作为MainWindow函数的参数
    def __init__(self):
        QUiLoader().registerCustomWidget(MyTextViewer)                          #导入自定义模块
        QUiLoader().registerCustomWidget(MyTextEdit)                          #导入自定义模块

        ui_inf = QFile("E:/Programming/Python/GUI/ui/videomerge ver5.ui")        #导入布局文件
        ui_inf.open(QFile.ReadOnly)
        self.ui = QUiLoader().load(ui_inf)
        ui_inf.close()
        #控件行为设置
        self.ui.File1Button.clicked.connect(self.find_file)     #self.ui.控件名.控件行为.连接函数
        self.ui.mergeButton.clicked.connect(self.merge_files)
        self.ui.clearButton.clicked.connect(self.clear_all)
        self.ui.ffmpegButton.clicked.connect(self.getffmpeg)
        self.ui.extractButton.clicked.connect(self.ext_file)
        self.ui.avmButton.clicked.connect(self.merge_AV)
        #self.ui.textEdit.textChanged.connect(self.editchange)

        #各种参数，文件位置
        #self.i = 0              #按键次数记录变量
        self.openfilepath = os.path.abspath(os.path.dirname("__file__"))        #文件位置，初始位置定于程序所在目录
        self.ffmpegpath = "ffmpeg.exe"

        self.step = 0
        self.ui.progressBar.setValue(self.step)

        self.timer = QTimer()
   
    def getffmpeg(self):
        if self.ui.textEdit.toPlainText():      #优先文本框中文件地址
            if os.path.exists(self.ui.textEdit.toPlainText()):
                self.ffmpegpath = self.ui.textEdit.toPlainText()
            else:
                QMessageBox.about(None,"Message","Can't find ffmpeg.exe")
        elif os.path.exists("ffmpeg.exe"):      #其次本目录中文件地址
            self.ffmpegpath = "ffmpeg.exe"
        else:
            QMessageBox.about(None,"Message","Can't find ffmpeg.exe")
            self.textadd("Can't find ffmpeg.exe")
            return
        self.textadd(">>>>ffmpeg path : " + self.ffmpegpath)
    
    def textadd(self,nline):            #文本框中加入文件
        self.ui.MyTBrowser.setText(str(self.ui.MyTBrowser.toPlainText()) + nline + "\n")  #此处是加上已经存在于框内的文字

    def find_folder(self):
        rootpath = os.path.abspath(os.path.dirname("__file__"))     #返回当前文件目录
        self.textadd(rootpath)   #显示rootpath
        fname = QFileDialog.getExistingDirectory(None, "Please select a director", rootpath)    #打开选择的文件目录，并将值返回和fname    
        self.textadd(fname)      #显示文件路径

    def find_file(self):
        fname = QFileDialog.getOpenFileNames(None, "Please select files", self.openfilepath)        

        #打开选择的文件目录，并将值返回和fname，返回值为元组[文件路径，文件类型]
        if len(fname[0]) == 0 and self.ui.MyTBrowser.allfileslist == [] :   #文本框记录的列表为空
            self.textadd( "Please select a file" )    #没有选择文件时
        else:
            for fn in fname[0]:
                self.ui.MyTBrowser.filenum += 1
                self.textadd( "File" + str(self.ui.MyTBrowser.filenum) + " : " + fn)
                prefilepath = os.path.split(fn)           #将所在文件位置进行分割，返回值为元组(文件目录，文件)
                self.ui.MyTBrowser.filepath = prefilepath[0]            #更新位置为当前文件位置
                self.openfilepath = prefilepath[0]             #设定下次打开文件路径
                if ".txt" in fn:
                    pass
                elif ".mp4" in fn:           #若是视频文件，获取视频信息，并将txt文件地址变为ffmpeg可识别的内容格式
                    (w,h,frames) = getvideoinfo(fn)       #获取长宽帧数
                    tem = "Resolution : " + str(w) + "x" + str(h) +"  Frames : " + str(frames)
                    self.textadd(" "*(10+len(str(self.ui.MyTBrowser.filenum))) + "->" + tem)
                    self.ui.MyTBrowser.allframes += frames
                    fn = "file " + "\'" + fn + "\'"           #若是视频文件，获取视频信息，并将txt文件地址变为ffmpeg可识别的内容格式
                else:
                    QMessageBox.about(None,"Message","File type is wrong!!")
                self.ui.MyTBrowser.allfileslist.append(fn)                   #将新选择的文件添加进列表
    
    def merge_files(self):      
        allfilelist = self.ui.MyTBrowser.allfileslist       #总的文件列表
        merglist = self.ui.MyTBrowser.filepath + "/mergelist.txt"       #输出txt列表地址

        exis = isexist(allfilelist,merglist,self.ffmpegpath,self.textadd)       #判断是否输入文件
        
        if exis and self.ui.typecomboBox.currentText():   #有文件有类型
            outname = self.ui.MyTBrowser.filepath + "/new" + self.ui.typecomboBox.currentText()
        elif exis and not self.ui.typecomboBox.currentText():   #没有文件没类型
            outname = self.ui.MyTBrowser.filepath + "/new" +  str(typecheck(allfilelist[0]))     #返回原格式
        else:
            return
        
        if exis:                                #存在文件
            if ".txt" in allfilelist[0]:
                txtmerge(allfilelist,outname,self.ui.progressBar)
                self.textadd("Output as " +  outname + " Succeffful!!")
            elif typecheck(allfilelist[0]):
                videomerge(merglist,outname,self.ui.progressBar,self.ui.MyTBrowser.allframes,self.ffmpegpath)
                self.textadd("Output as " + outname + " Successful!!" )
                os.remove(merglist)             #删除临时列表       
            else:
                QMessageBox.about(None,"Message","File type is unsupported!!")
        else:
            return

        #重置所有变量
        self.ui.MyTBrowser.allframes = 0
        self.ui.MyTBrowser.filepath = ""
        self.ui.MyTBrowser.allfileslist = []
        self.ui.MyTBrowser.filenum = 0

    def ext_file(self):
        allfilelist = self.ui.MyTBrowser.allfileslist       #总的文件列表
        
        if not allfilelist:
            self.textadd( "Please select a file" )
        elif os.path.exists(self.ffmpegpath) and self.ui.exacomboBox.currentText():   #有文件有类型
            inname = allfilelist[0].strip("file '")
            outname = self.ui.MyTBrowser.filepath + "/new" + self.ui.exacomboBox.currentText()
            videoexa(inname,outname,self.ui.progressBar,self.ui.MyTBrowser.allframes,self.ffmpegpath)
            self.textadd("Output as " + outname +  " Succeffful!!")
        else:
            QMessageBox.about(None,"Message","File type is unsupported!!")
            

        self.ui.MyTBrowser.allframes = 0
        self.ui.MyTBrowser.filepath = ""
        self.ui.MyTBrowser.allfileslist = []
        self.ui.MyTBrowser.filenum = 0

    def merge_AV(self):      
        allfilelist = self.ui.MyTBrowser.allfileslist       #总的文件列表
        merglist = self.ui.MyTBrowser.filepath + "/mergelist.txt"       #输出txt列表地址
        print(allfilelist)
        if ".aac" in allfilelist[0]:       #判断是否输入文件
            ina = allfilelist[0]
            inv = allfilelist[1].strip("file '")
        elif ".aac" in allfilelist[1]:
            ina = allfilelist[1]
            inv = allfilelist[0].strip("file '")
        else:
            self.textadd("Please check the input files!!" )
        
        print(ina)
        exis = isexist(allfilelist,merglist,self.ffmpegpath,self.textadd)       #判断是否输入文件
        outname = self.ui.MyTBrowser.filepath + "/new.mp4"
        
        if exis:                                #存在文件
            AVmerge(ina,inv,outname,self.ui.progressBar,self.ui.MyTBrowser.allframes,self.ffmpegpath)
            self.textadd("Output as " + outname + " Successful!!" )
            os.remove(merglist)             #删除临时列表       
        else:
            return

        self.ui.MyTBrowser.allframes = 0
        self.ui.MyTBrowser.filepath = ""
        self.ui.MyTBrowser.allfileslist = []
        self.ui.MyTBrowser.filenum = 0
 

    def clear_all(self):
        self.ui.MyTBrowser.allframes = 0
        self.ui.MyTBrowser.filepath = ""
        self.ui.MyTBrowser.allfileslist = []
        self.ui.MyTBrowser.filenum = 0
        self.ui.MyTBrowser.setText("")  #清空文本框
        self.ui.progressBar.setValue(0)
        self.ui.textEdit.setText("")

if __name__ == "__main__":
    app = QApplication([])
    vm = VideoMerge()
    vm.ui.show()
    app.exec()

 

