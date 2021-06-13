import speech_recognition as sr
import pyaudio
import wave
import http.client
import hashlib
import json
import urllib
import random
import time
CHUNK = 1024 
FORMAT = pyaudio.paInt16  # paInt8
CHANNELS = 2 
RATE = 44100              # 採樣率 -sample rate
RECORD_SECONDS = 4
WAVE_OUTPUT_FILENAME = "output10.wav"



def googletranslatevoice(filename):      #  使用谷歌api将语音转文字函数，输入：文件名str,  输出：文字str
    voice=sr.AudioFile(filename)
    r=sr.Recognizer()
    with voice as source:
        audio=r.record(source)
    return r.recognize_google(audio)
    
def luyin():     #调动麦克风进行录音函数   无输入
    p = pyaudio.PyAudio()
    
    stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK) # buffer

    print("* recording")

    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)    # 2 bytes(16 bits) per channel

    print("* done recording")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open("output10.wav", 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
def tochinse(content):         #将英文转换为中文的函数，输入：str，输出：str
    appid = '20210330000753240'
    secretKey = '0VpYTX13l1sqIrAgc9js'
    httpClient = None
    myurl = '/api/trans/vip/translate'
    q = content
    fromLang='en'
    toLang='zh'
    salt = random.randint(32768, 65536)
    sign = appid + q + str(salt) + secretKey
    sign = hashlib.md5(sign.encode()).hexdigest()
    myurl = myurl + '?appid=' + appid + '&q=' + urllib.parse.quote(
        q) + '&from=' + fromLang + '&to=' + toLang + '&salt=' + str(
        salt) + '&sign=' + sign
    try:
        httpClient = http.client.HTTPConnection('api.fanyi.baidu.com')
        httpClient.request('GET', myurl)
        # responseˇHTTPResponseהг
        response = httpClient.getresponse()
        jsonResponse = response.read().decode("utf-8")
        js = json.loads(jsonResponse)  
        dst = str(js["trans_result"][0]["dst"])  
        print(dst) # ղӡޡڻ
        httpClient.close() 
        return dst
    except Exception as e:
        print('err:'+e)
    finally:
        if httpClient:
            httpClient.close()  
if __name__=="__main__":    
    luyin()
    text=googletranslatevoice(WAVE_OUTPUT_FILENAME)
    print(text)
