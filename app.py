import RPi.GPIO as GPIO
import socketio
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
import math
from collections import Counter
import pandas as pd
import requests
import time

df = pd.read_csv('dataset.txt', header=None)
df = df.values

def convert(lst):
 return ' '.join(lst).split()
split = []

for i in range(len(df)):
 df_to_list = df[i].tolist()
 df_to_list = convert(df_to_list)
 split.append(df_to_list)

def build_vector(iterable1,iterable2):
 counter1 = Counter(iterable1)
 counter2 = Counter(iterable2)
 all_items = set(counter1.keys()).union(set(counter2.keys()))
 vector1 = [counter1[k] for k in all_items]
 vector2 = [counter2[k] for k in all_items]
 return vector1, vector2

def cosim(v1,v2):
 dot_product = sum(n1 * n2 for n1, n2 in zip(v1,v2))
 magnitude1 = math.sqrt(sum(n ** 2 for n in v1))
 magnitude2 = math.sqrt(sum(n ** 2 for n in v2))
 return dot_product / (magnitude1 * magnitude2)

relay1 = 32
relay2 = 36
relay3 = 38
relay4 = 40
GPIO.setmode(GPIO.BOARD)
GPIO.setup(relay1, GPIO.OUT)
GPIO.setup(relay2, GPIO.OUT)
GPIO.setup(relay3, GPIO.OUT)
GPIO.setup(relay4, GPIO.OUT)
GPIO.output(relay1, GPIO.LOW)
GPIO.output(relay2, GPIO.LOW)
GPIO.output(relay3, GPIO.LOW)
GPIO.output(relay4, GPIO.HIGH)

sio = socketio.Client()
sio.connect('http://192.168.100.5:3000')

@sio.on('to_raspi')
def to_raspi(data):
 print('perintah dari user :' ,data)
 factory = StemmerFactory()
 factory2 = StopWordRemoverFactory()
 stemmer = factory.create_stemmer()
 stopword = factory2.create_stop_word_remover()
 output = stemmer.stem(data)
 stop = stopword.remove(output)
 print('hasil text pre processing : ' ,stop)
 print('')

 nilai_max = 0.0
 index = 0

 for i in range(len(df)):
  l1 = stop.split()
  l2 = split[i]
  v1, v2 = build_vector(l1,l2)
  result = cosim(v1,v2)
  print("target cosine : " ,l2)
  print("skor cosine : " ,result)
  if(result >= nilai_max and result != 0):
   nilai_max = result
   hasil = df[i]
  print("skor max sementara : ", nilai_max)
  print("")
 print("command terpilih : " ,hasil)

 if hasil  == "nyala lampu garasi" or hasil == "hidup lampu garasi" :
  millis = int(round(time.time() * 1000))
  GPIO.output(relay1, GPIO.LOW)
  print(millis)
  print("Lampu Garasi Berhasil Dinyalakan")
  sio.emit("lg_raspi", "lg_on")
  r = requests.put("http://192.168.100.5:5000/api/v1/devices/5efaf8303691e4d53c695ac8", json = {'status':'true'})

 elif hasil == "nyala lampu utama" or hasil == "hidup lampu utama" :
  millis = int(round(time.time() * 1000)) 
  GPIO.output(relay2, GPIO.LOW)
  print(millis)
  print("Lampu Utama Berhasil Dinyalakan")
  sio.emit("lu_raspi", "lu_on")
  r = requests.put("http://192.168.100.5:5000/api/v1/devices/5efaf8303691e4d53c695ac7", json = {'status':'true'})

 elif hasil == "mati lampu utama" or hasil == "padam lampu utama" :
  millis = int(round(time.time() * 1000))
  GPIO.output(relay2, GPIO.HIGH)
  sio.emit("lu_raspi", "lu_off")
  print(millis)
  print("Lampu Utama Berhasil Dimatikan")
  r = requests.put("http://192.168.100.5:5000/api/v1/devices/5efaf8303691e4d53c695ac7", json = {'status':'false'})

 elif hasil == "mati lampu garasi" or hasil == "padam lampu garasi" :
  millis = int(round(time.time() * 1000))
  GPIO.output(relay1, GPIO.HIGH)
  print(millis)
  print("Lampu Garasi Berhasil Dimatikan")
  sio.emit("lg_raspi", "lg_off")
  r = requests.put("http://192.168.100.5:5000/api/v1/devices/5efaf8303691e4d53c695ac8", json = {'status':'false'})

 elif hasil == "buka kunci pintu" :
  millis = int(round(time.time() * 1000))
  GPIO.output(relay4, GPIO.LOW)
  print(millis)
  print("Pintu Berhasil Dibuka Kuncinya")
  sio.emit("kr_raspi", "kr_off")
  r = requests.put("http://192.168.100.5:5000/api/v1/devices/5efaf8303691e4d53c695ac9", json = {'status':'false'})

 elif hasil == "tutup kunci pintu" :
  millis = int(round(time.time() * 1000))
  GPIO.output(relay4, GPIO.HIGH)
  print(millis)
  print("Pintu Berhasil Dikunci")
  sio.emit("kr_raspi", "kr_on")
  r = requests.put("http://192.168.100.5:5000/api/v1/devices/5efaf8303691e4d53c695ac9", json = {'status':'true'})

 elif hasil == "mati kipas angin" or hasil == "padam kipas angin" :
  millis = int(round(time.time() * 1000))
  GPIO.output(relay3, GPIO.HIGH)
  print(millis)
  print("Kipas Berhasil Dimatikan")
  sio.emit("ka_raspi", "ka_off")
  r = requests.put("http://192.168.100.5:5000/api/v1/devices/5efaf8303691e4d53c695aca", json = {'status':'false'})

 elif hasil == "nyala kipas angin" or hasil == "hidup kipas angin" :
  millis = int(round(time.time() * 1000))
  GPIO.output(relay3, GPIO.LOW)
  print(millis)
  print("Kipas Berhasil Dinyalakan")
  sio.emit("ka_raspi", "ka_on")
  r = requests.put("http://192.168.100.5:5000/api/v1/devices/5efaf8303691e4d53c695aca", json = {'status':'true'})

 else:
  print("Kirim perintah yang benar")

@sio.event
def disconnect():
 print("I'm disconnected!")
