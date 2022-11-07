from PySide6.QtWidgets import QTextBrowser,QMessageBox,QTextEdit
import cv2
import os

def getvideoinfo(fname):                        #用cv2获取视频信息
    cap = cv2.VideoCapture(fname)
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = frames / fps
    return (width,height,round(frames),round(duration))             #返回总帧数

def typecheck(filelist):
    filetype = ['.mp4','.avi','.txt','.mp3','.aac','.ml']
    
    i = 0
    for t in filetype:
        if t in filelist:
            i += 1
            if i:
                return(t)

    return(False)

class MyTextViewer(QTextBrowser):                        #创建自己的类，继承自QTextBrowser，已激活拖拽行为
        def __init__(self,parent):               #对于与自己建的控件的各种属性
            super(MyTextViewer, self).__init__(parent)         #这条命令意思是引用自身窗口，因此可以用下面的命令来调整尺寸
            self.setAcceptDrops(True)
            self.filenum = 0
            self.allfileslist = []
            self.allframes = 0
            self.filepath = ""
            self.alllines = 0
            self.duration = 0
        
        def textadd(self,nline):            #文本框中加入文件
            self.setText(str(self.toPlainText()) + nline + "\n")  #此处是加上已经存在于框内的文字，此处的self指的就是自己
        
        def dragEnterEvent(self, event):
            # print(event.mimeData().urls())
            # print(len(event.mimeData().urls()))
            self.allpaths = ""  # ==> 默认文本内容
            for i in range(len(event.mimeData().urls())):
                self.filenum +=1
                fn = event.mimeData().urls()[i].toLocalFile()   #获取文件路径
                prefilepath = os.path.split(fn)           #将所在文件位置进行分割，返回值为元组(文件目录，文件)
                self.filepath = prefilepath[0]            #更新位置为当前文件位置
                self.merglist = self.filepath + "/mergelist.txt"   #更新合并列表位置
                if fn not in self.allpaths:                     #allpaths是str格式
                    self.allpaths += fn +"\n"        #去重
                    if typecheck(fn) == ".txt":
                        self.alllines += len(open(fn,'r',encoding="utf8").readlines())  #读取文件行数
                        self.textadd( "File" + str(self.filenum) + " : " + fn)
                        self.allfileslist.append(fn)                   #将新选择的文件添加进列表
                    elif typecheck(fn) == ".aac" or typecheck(fn) == ".mp3":           #若是视频文件，获取视频信息，并将txt文件地址变为ffmpeg可识别的内容格式                       
                        self.textadd( "File" + str(self.filenum) + " : " + fn)
                        self.allfileslist.append(fn)                   #将新选择的文件添加进列表
                    elif typecheck(fn) == ".mp4" or typecheck(fn) == ".avi" or typecheck(fn) == ".ml" :           #若是视频文件，获取视频信息，并将txt文件地址变为ffmpeg可识别的内容格式
                        (w,h,frames,duration) = getvideoinfo(fn)       #获取长宽帧数
                        self.textadd( "File" + str(self.filenum) + " : " + fn)
                        tem = "Resolution : " + str(w) + "x" + str(h) +"  Frames : " + str(frames) + " Duration : " + str(duration) +"s"
                        self.textadd(" "*(10+len(str(self.filenum))) + "->" + tem)                        
                        self.allframes += frames
                        self.duration += duration
                        fn = "file " + "\'" + fn + "\'"           #若是视频文件，获取视频信息，并将txt文件地址变为ffmpeg可识别的内容格式
                        self.allfileslist.append(fn)                   #将新选择的文件添加进列表
                    else:
                        self.textadd( "File" + " : " + fn)
                        QMessageBox.about(None,"Message","Unsupportted file type")
                        self.filenum -= 1           #错误文件不计入文件数中
                    #event.accept()
            #print(self.allfileslist)
            #self.filenum += len(event.mimeData().urls())
            #print(self.toPlainText())                
            

class MyTextEdit(QTextEdit):                        #创建自己的类，继承自QTextBrowser，已激活拖拽行为
        def __init__(self,parent):               #对于与自己建的控件的各种属性
            super(MyTextEdit, self).__init__(parent)         #这条命令意思是引用自身窗口，因此可以用下面的命令来调整尺寸
            self.setAcceptDrops(True)

        def dragEnterEvent(self, event):
            self.setText("")        #发生拖拽时首先清空文本
            fn = event.mimeData().urls()[0].toLocalFile()
            # print(len(event.mimeData().urls()))
            self.allpaths = ""  # ==> 默认文本内容
            if fn not in self.allpaths:                     #allpaths是str格式
                self.allpaths += fn +"\n"        #去重
                self.setText(fn)
                #event.accept()                             #不要设置event.accept，会重复文本框输入行为，导致文件输入复数
