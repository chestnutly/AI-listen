# -*- coding:utf-8 -*-
import os
import sys
import random
import math
import numpy as np
import tkinter as tk
from tkinter import filedialog
from PIL import ImageTk, Image
import tkinter.messagebox
from numpy import *
import translate
import PythonFile.extract_data
import shutil
halfvoice=0.05
filename=""
h12,f0,f0_time=[],[],[]
voicetime=[]
voicespeed=0
score=0
upertime=0
h12_mean=0
f0_mean=0
politescore=0
h12_cha=0

word_score,tense_score,tense_score=0,0,0
       
"""
找到f0向量中最后一个上升趋势点
输入：f0列表
返回值：最后一个上升趋势点的坐标起点与终点
"""
def finduper(f0):
    n=len(f0)
    loss,up,losscount=0,0,0
    end=[]
    if n<=0:return [0,0]
    for i in range(n-1,n-20,-1):
        if f0[i]-f0[i-1]>0.1 :  #上升
            if f0[i]-f0[i-1]<=89.6+8.7:
                up+=f0[i]-f0[i-1]
                end.append(i)
                if i==n-18:
                    return [i,end[0]]
                
            
        elif f0[i-1]-f0[i]>0.1:#下降
            if f0[i-1]-f0[i]<=100.04+5.8:
                loss=f0[i-1]-f0[i]
                
                if len(end)>3:
                    print("losscount")
                    print(losscount)
                    if f0[i-1]-f0[i]>0.3 or losscount>=3:
                        
                        return [i,end[0]]
                    elif f0[i-1]-f0[i]<0.3 and f0[i-1]-f0[i]>0:
                        losscount+=1
                else:
                    if i==n-18 and len(end)>0:
                        return [i,end[0]]
                    elif i==n-18 and len(end)==0:
                        return [i,i]
                    end=[]
            
            
def getlist(filename):
    """
    #获取文件中的h12特征向量与f0,与时间特征向量
    h12[float,float ,....]
    f0[float,float ,....]
    """
    h12,f0,f0_time,f0_mean=[],[],[],[]
    voicetime=[]
    h12txtfile = open("Final/"+filename+'.bid','r', encoding="utf-8")
    lines = h12txtfile.readlines()
    for line in lines:    #temp_list中[1]代表h1-h2，[2]代表h1*-h2*，
        temp_list=line.split()
        if temp_list[1]!="h1-h2" :
            h12.append(float(temp_list[1]))
    h12_mean=mean(h12)
    h12_cha=max(h12)-min(h12)
    f0txtfile = open("Final/"+filename+'.actutimesemitonef0','r', encoding="utf-8")
    lines = f0txtfile.readlines()
    for line in lines:    #temp_list中[2]代表f0，
        temp_list=line.split()
        if temp_list[2]!="F0":
            f0.append(float(temp_list[2]))
        if temp_list[1]!="ActualTime":
            f0_time.append(float(temp_list[1]))
    uper= finduper(f0)
    
    f0_mean=mean(f0)
    if uper==None:
        upertime=0
    else:
        upertime=int(f0[uper[1]])-float(f0[uper[0]])
    """
    平均语速
    保存在voicespeed中
    """
    voicetimetext=open("Final/"+'duration.txt','r', encoding="utf-8")
    lines=voicetimetext.readlines()
    for line in lines:
        templine=line.split()
        if templine[0]=="_"+filename:
            for i in range(1,len(templine)):
                voicetime.append(float(templine[i]))
    voicespeed=mean(voicetime)/1000
    return upertime,voicespeed,h12_mean, h12_cha,f0_mean
"""
voicecomputepolite函数通过参数计算礼貌度
输入：upertime(最后升调时常),voicespeed（语速）,h12_mean（谐波差均值）,halfvoice（半音）
返回值：礼貌度分数
"""
def voicecomputepolite(upertime,voicespeed,h12_mean,halfvoice,f0_mean):
    politescore=0
    print("upertime",upertime)
    print("voicespeed",voicespeed)
    print("h12_mean",h12_mean)
    print("f0_mean",f0_mean)
    if upertime>=15:    #升调的礼貌分数评判
        politescore+=40
    elif upertime>=10 and upertime<15:    
        politescore+=25+(upertime-10)*3
    elif upertime>=7 and upertime<10:    
        politescore+=20+(upertime-7)*1.6
    elif upertime>=5 and upertime<7:    
        politescore+=14+(upertime-5)*3
    elif upertime<5 and upertime>=3:
        politescore+=7+(upertime-3)*3.5
    elif upertime<3 and upertime>=1:
        politescore+=3+(upertime-1)*2
    elif upertime<1 and upertime>=0:
        politescore+=upertime*3
        
    if voicespeed>0 and voicespeed<=0.25:#语速的礼貌分数评判
        politescore+=voicespeed*24
    elif voicespeed>0.25 and voicespeed<=0.325:
        politescore+=6+(voicespeed-0.25)*53
    elif voicespeed>0.325 and voicespeed<=0.35:
        politescore+=10+(voicespeed-0.325)*200
    elif voicespeed>=0.35: 
        politescore+=20
        
    if h12_mean>0 and h12_mean<=2.5:#谐波差均值的礼貌分数评判
        politescore+=(h12_mean)*1.2
    elif h12_mean>2.5 and h12_mean<=7.5:
        politescore+=3+(h12_mean-2.5)*0.4
    elif h12_mean>7.5 and h12_mean<=10:
        politescore+=5+(h12_mean-7.5)*2
    elif h12_mean>=10: 
        politescore+=10
       
    if f0_mean>0 and f0_mean<=87.5:   #基频均值的分数评判
        politescore+=3
    elif f0_mean>87.5 and f0_mean<=90:
        politescore+=3+(f0_mean-87.5)*0.8
    elif f0_mean>90 and f0_mean<=93:
        politescore+=3+(f0_mean-90)*1.6
    elif f0_mean>93:
        politescore+=15
        
    return int(politescore)


def textcomputepolite(text):
    politescore=0
    politeword=["please","thank","could"]
    tense_begin=["was","were"]
    sentence_type=["if"]
    #礼貌词评分
    word_list=text.split()
    word_score=0
    for i in range(len(word_list)):
        if word_list[i] in politeword:
            word_score+=5
    word_score=min(word_score,20) 
    
    #时态评分
    tense_score=0
    for i in range(len(word_list)):
        if word_list[i] in tense_begin:
            print(str(word_list[i+1]))
            if "ing"in str(word_list[i+1]):     #"could you please let me out if you was working"
                tense_score+=5
  
    #句型评分
    sentence_score=0
    for i in range(len(word_list)):
        if word_list[i] in sentence_type:
            sentence_score+=5
    sentence_score=min(sentence_score,20)
    return  word_score,tense_score,sentence_score      
"""
tkinter界面部分
"""

root = tk.Tk()
#背景  upertime,voicespeed,h12_mean,halfvoice
root.geometry('500x300+300+200')
root.title('礼貌度计算平台')
lable0 = tk.Label(root, text="软件介绍：该软件是计算礼貌度",fg="green")
"""
lable1 = tk.Label(root,text = ' ')
lable2 = tk.Label(root,text = ' ')
lable3 = tk.Label(root,text = ' ')
lable4 = tk.Label(root,text = ' ')
lable5 = tk.Label(root,text = ' ')
"""
def show():
    voicespeed=0 
    upertime=0
    h12_mean=0
    h12_cha=0
    #fpath = filedialog.askopenfilename()
    #filename=fpath.split(".")[0].split("/")[-1]
    filename="output10"
    upertime,voicespeed,h12_mean,h12_cha,f0_mean=getlist(filename)
    score=voicecomputepolite(upertime,voicespeed,h12_mean,halfvoice,f0_mean)
    temp_text=open('Praat/data/voice/output10.txt','r', encoding="utf-8")
    en_text=str(temp_text.readlines()[0])
    word_score,tense_score,sentence_score=textcomputepolite(en_text)
    lable1txt.set("最后升调持续时间："+str(upertime))
    lable2txt.set("语速："+str(voicespeed))
    lable3txt.set("谐波差均值："+str(h12_mean))
    lable4txt.set('基频均值：'+str(f0_mean))
    lable5txt.set('礼貌度分数：'+str(score))
    lable6txt.set('谐波差区间：'+str(h12_cha))
    lable1 = tk.Label(root,textvariable=lable1txt)
    lable2 = tk.Label(root,textvariable= lable2txt)
    lable3 = tk.Label(root,textvariable= lable3txt)
    lable4 = tk.Label(root,textvariable= lable4txt)
    lable5 = tk.Label(root,textvariable= lable5txt)
    lable6 = tk.Label(root,textvariable= lable6txt)
    lable1.place(x=100,y=80)     
    lable2.place(x=100,y=100)
    lable3.place(x=100,y=120)
    lable4.place(x=100,y=140)
    lable5.place(x=100,y=160) 
    lable6.place(x=100,y=180) 
    #lable7.place(x=100,y=200) 
    print(score)
def luyin():        #调用麦克风进行录音并转换为英文
    print("ok")
    translate.luyin()
    shutil.copyfile("output10.wav","Praat/data/voice/output10.wav")
    entext=translate.googletranslatevoice("Praat/data/voice/output10.wav")
    with open("Praat/data/voice/output10.txt","w",encoding="utf-8") as t:
        t.write(str(entext))
    t.close()
    print("voice to word sucessfully")
    PythonFile.extract_data.data_extractor()
    chtext=translate.tochinse(entext)
    lable7txt.set("语句："+str(entext))
    lable7 = tk.Label(root,textvariable= lable7txt)
    lable7.place(x=100,y=200)
    return [entext,chtext]
    print(text)
    


lable1txt,lable2txt,lable3txt,lable4txt,lable5txt,lable6txt,lable7txt=tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar()    
button1 = tk.Button(root, text="计算分数", font=("Monospaced", 10),height=3,width=10,command=show,bg="Ivory")
button2 = tk.Button(root, text="录音", font=("Monospaced", 10),height=3,width=10,command=luyin,bg="Ivory")


lable0.place(x=10,y=20)     #软件介绍文本所在位置
button1.place(x=80,y=220)   #执行运算按键所在位置
button2.place(x=180,y=220)
root.mainloop()

            
                
            
        
        