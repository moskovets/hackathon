#! /usr/bin/env python
# coding: utf-8
from collections import deque
import serial
import time
import struct
import datetime
import Tkinter as Tk
import pybrain
from pybrain.tools.shortcuts import buildNetwork
from pybrain import SigmoidLayer
from pybrain import LinearLayer
from pybrain.structure import FeedForwardNetwork
from pybrain.structure import FullConnection
from pybrain.datasets import SupervisedDataSet
from pybrain.supervised.trainers import BackpropTrainer
import random
from threading import Thread

#TODO
from pybrain.tools.customxml.networkwriter import NetworkWriter
from pybrain.tools.customxml.networkreader import NetworkReader

# глобальные переменные
root = Tk.Tk()
datafile = "eeg.dat"
buf = [] 
ref = 0; 
FSM_state = 0 #[0 - "education", 1 - "work"]
CMD = 0 #[0 - "left", 1 - "right"]
run_state = False # run/stop state
# массив FiFo
valuechannel1 = deque([])
valuechannel2 = deque([])
valuechannel3 = deque([])
learnData = []
education = []

trained_net = 0
medium = -0.42
res_array = []


#Нейронная сеть
net = buildNetwork(64*3, 20, 6, 2, bias=True, hiddenclass=SigmoidLayer)




#режим работы
#state = 1 	#Данные поступают из электроэнцефалографа
state = 0 	#Данные поступают из файла datafile

if state == 1:
	ser = serial.Serial("/dev/ttyUSB0")


# преобразование данных
def changebyte(needbyte):
  return  struct.unpack('b', needbyte)
def change2byteCRC(need2byteCRC):
  return  struct.unpack('h', need2byteCRC)
def change2byte(need2byte):
  return  struct.unpack('>h', need2byte)
def change3byte(need3byte):
  return  struct.unpack('BBB', need3byte)
def change4byte(need4byte):
  return  struct.unpack('>i', need4byte)
# проверка CRC
def calc(data):
        crc_table=[
	0x0000,0xC0C1,0xC181,0x0140,0xC301,0x03C0,0x0280,0xC241,0xC601,0x06C0,0x0780,0xC741,0x0500,0xC5C1,0xC481,0x0440,
	0xCC01,0x0CC0,0x0D80,0xCD41,0x0F00,0xCFC1,0xCE81,0x0E40,0x0A00,0xCAC1,0xCB81,0x0B40,0xC901,0x09C0,0x0880,0xC841,
	0xD801,0x18C0,0x1980,0xD941,0x1B00,0xDBC1,0xDA81,0x1A40,0x1E00,0xDEC1,0xDF81,0x1F40,0xDD01,0x1DC0,0x1C80,0xDC41,
	0x1400,0xD4C1,0xD581,0x1540,0xD701,0x17C0,0x1680,0xD641,0xD201,0x12C0,0x1380,0xD341,0x1100,0xD1C1,0xD081,0x1040,
	0xF001,0x30C0,0x3180,0xF141,0x3300,0xF3C1,0xF281,0x3240,0x3600,0xF6C1,0xF781,0x3740,0xF501,0x35C0,0x3480,0xF441,
	0x3C00,0xFCC1,0xFD81,0x3D40,0xFF01,0x3FC0,0x3E80,0xFE41,0xFA01,0x3AC0,0x3B80,0xFB41,0x3900,0xF9C1,0xF881,0x3840,
	0x2800,0xE8C1,0xE981,0x2940,0xEB01,0x2BC0,0x2A80,0xEA41,0xEE01,0x2EC0,0x2F80,0xEF41,0x2D00,0xEDC1,0xEC81,0x2C40,
	0xE401,0x24C0,0x2580,0xE541,0x2700,0xE7C1,0xE681,0x2640,0x2200,0xE2C1,0xE381,0x2340,0xE101,0x21C0,0x2080,0xE041,
	0xA001,0x60C0,0x6180,0xA141,0x6300,0xA3C1,0xA281,0x6240,0x6600,0xA6C1,0xA781,0x6740,0xA501,0x65C0,0x6480,0xA441,
	0x6C00,0xACC1,0xAD81,0x6D40,0xAF01,0x6FC0,0x6E80,0xAE41,0xAA01,0x6AC0,0x6B80,0xAB41,0x6900,0xA9C1,0xA881,0x6840,
	0x7800,0xB8C1,0xB981,0x7940,0xBB01,0x7BC0,0x7A80,0xBA41,0xBE01,0x7EC0,0x7F80,0xBF41,0x7D00,0xBDC1,0xBC81,0x7C40,
	0xB401,0x74C0,0x7580,0xB541,0x7700,0xB7C1,0xB681,0x7640,0x7200,0xB2C1,0xB381,0x7340,0xB101,0x71C0,0x7080,0xB041,
	0x5000,0x90C1,0x9181,0x5140,0x9301,0x53C0,0x5280,0x9241,0x9601,0x56C0,0x5780,0x9741,0x5500,0x95C1,0x9481,0x5440,
	0x9C01,0x5CC0,0x5D80,0x9D41,0x5F00,0x9FC1,0x9E81,0x5E40,0x5A00,0x9AC1,0x9B81,0x5B40,0x9901,0x59C0,0x5880,0x9841,
	0x8801,0x48C0,0x4980,0x8941,0x4B00,0x8BC1,0x8A81,0x4A40,0x4E00,0x8EC1,0x8F81,0x4F40,0x8D01,0x4DC0,0x4C80,0x8C41,
	0x4400,0x84C1,0x8581,0x4540,0x8701,0x47C0,0x4680,0x8641,0x8201,0x42C0,0x4380,0x8341,0x4100,0x81C1,0x8081,0x4040
	]
        crc_hi=0xFF
        crc_lo=0xFF

        for w in data:
                index=crc_lo ^ ord(w)
                crc_val=crc_table[index]
                crc_temp=crc_val/256
                crc_val_low=crc_val-(crc_temp*256)
                crc_lo=crc_val_low ^ crc_hi
                crc_hi=crc_temp

        crc=crc_hi*256 +crc_lo
        return crc

#посылка команды прибору
def send_cmd(cmd):
	ser.write(cmd.encode())
	time.sleep(0.5)
	
#инициализация
def ser_init():
	#Open serial
	ser.baudrate = 460800
	if ser.isOpen():
		ser.close()
	ser.open()
	#Check serial is openned
	ser.isOpen()
	#Send init commands
	print ("Start device initialization!")
	send_cmd("/put/memory?address=39&value=214&\r")
	send_cmd("/put/memory?address=40&value=194&\r")
	send_cmd("/put/memory?address=41&value=96&\r")
	send_cmd("/put/memory?address=42&value=0&\r")
	send_cmd("/put/memory?address=43&value=0&\r")
	send_cmd("/put/memory?address=44&value=0&\r")
	send_cmd("/put/memory?address=45&value=0&\r")
	send_cmd("/put/memory?address=46&value=0&\r")
	send_cmd("/put/memory?address=47&value=0&\r")
	send_cmd("/put/memory?address=48&value=112&\r")
	send_cmd("/put/memory?address=49&value=0&\r")
	send_cmd("/put/memory?address=50&value=0&\r")
	send_cmd("/put/memory?address=51&value=0&\r")
	send_cmd("/put/memory?address=87&value=0x76543210&\r")
	send_cmd("/put/memory?address=88&value=0x40&\r")
	send_cmd("/put/memory?address=89&value=0x40&\r")
	send_cmd("/put/memory?address=90&value=0x40&\r")
	send_cmd("/put/memory?address=91&value=0x40&\r")
	send_cmd("/put/memory?address=92&value=0x40&\r")
	send_cmd("/put/memory?address=93&value=0x40&\r")
	send_cmd("/put/memory?address=94&value=0x40&\r")
	send_cmd("/put/memory?address=95&value=0x40&\r")
	send_cmd("/put/memory?address=39&value=214&\r")
	send_cmd("/put/memory?address=40&value=194&\r")
	send_cmd("/put/memory?address=41&value=96&\r")
	send_cmd("/put/memory?address=42&value=0&\r")
	send_cmd("/put/memory?address=43&value=0&\r")
	send_cmd("/put/memory?address=44&value=0&\r")
	send_cmd("/put/memory?address=45&value=0&\r")
	send_cmd("/put/memory?address=46&value=0&\r")
	send_cmd("/put/memory?address=47&value=0&\r")
	send_cmd("/put/memory?address=48&value=112&\r")
	send_cmd("/put/memory?address=49&value=0&\r")
	send_cmd("/put/memory?address=50&value=0&\r")
	send_cmd("/put/memory?address=51&value=0&\r")
	send_cmd("/put/memory?address=87&value=0x76543210&\r")
	send_cmd("/put/memory?address=88&value=0x40&\r")
	send_cmd("/put/memory?address=89&value=0x40&\r")
	send_cmd("/put/memory?address=90&value=0x40&\r")
	send_cmd("/put/memory?address=91&value=0x40&\r")
	send_cmd("/put/memory?address=92&value=0x40&\r")
	send_cmd("/put/memory?address=93&value=0x40&\r")
	send_cmd("/put/memory?address=94&value=0x40&\r")
	send_cmd("/put/memory?address=95&value=0x40&\r")
	send_cmd("/put/memory?address=52&value=1&\r")
	print ("Device initialization done! Wait for 3 sec!")
	time.sleep(3)
	#Clear all buffers
	ser.flushInput()
	ser.flushOutput()    

#Чтение файла в буфер
def file_init():
	global buf
	f = open(datafile)
	b = f.read(1)
	while b:
		buf += b
		b = f.read(1)
	f.close()


#Чтение количества байт из циклического буфера
def buf_read(count):
	global ref
	res = ""
	for i in range(count):
		res+=buf[ref];		
		ref = (ref+1)%len(buf)
		time.sleep(0.000001)
	return res


def get(count):
  if state:
  	return ser.read(count)
  else:
        return buf_read(count)


def receive_data_from_eeg():

	
	# массив FiFo
	global valuechannel1
	global valuechannel2
	global valuechannel3
	global learnData
	global education

	valuechannel1.clear()
	valuechannel2.clear()
	valuechannel3.clear()

	#wait 100 ms
	time.sleep(0.1)

	#Clear all buffers
	if state:
                ser.flushInput()
                ser.flushOutput()
                
	begin_time = time.time()
	buffer_lst = []       
	learnData=[]
	counter = 0
	break_flag = False
	
	while not(break_flag) : # Цикл 
	  	data_of_byte = get(3)
	  	header = change3byte(data_of_byte)
	  	headerfirstbyte = int(header[0])
	  	headersecondbyte = int(header[1])
	  	headerthirtbyte = int(header[2])
		# Проверка заголок пакета
		
		while headerfirstbyte != 1 and headersecondbyte != 28 and headerthirtbyte != 32:
			data_of_byte = data_of_byte[1:]
			data_of_byte += get(1)
			header_nextbyte = changebyte(data_of_byte[2])
			headerfirstbyte = headersecondbyte
			headersecondbyte = headerthirtbyte
			headerthirtbyte = int(header_nextbyte[0])
	   	if headerfirstbyte == 1 and headersecondbyte == 28 and headerthirtbyte == 32:
	    		data_of_byte = data_of_byte + get(520) 
	    		size = change2byte(data_of_byte[7:9]) #Информация об объеме данных
	    		if int(size[0]) == 512: #Проверка размеров данных
	     			x = 9
	     			data_for_matrix = data_of_byte[0:521] #Данные от 16 сэмплов
	     			crc = data_of_byte[521:523] #CRC
	     			matrix_of_value = [[0] * 16 for i in range(8)]
	     			for i in range(16):
	      				for j in range(8):
						value = change4byte(data_for_matrix[x:x+4])
						x += 4 #Шаг по 4 байта
						buffer_lst.append(int(value[0]))
						matrix_of_value[j][i] = buffer_lst[:] #Ввод данных в массив
						del buffer_lst[:]
	     			crc_check = calc(data_for_matrix)
	     			crc = ''.join([ crc[x:x+2][::-1] for x in range(0, len(crc), 2) ])
	     			crc = change2byteCRC(crc)
	    			if int(crc[0]) == crc_check: #Сравнения CRC
	       				end_time = time.time()
	       				my_time = end_time - begin_time 
	       				if counter < 4 : #Пока не получим 4 пакета (но не менее 500 мс от начала предъявления)
						valuechannel1.append(matrix_of_value[0:15][0])
						valuechannel2.append(matrix_of_value[1:15][0])
						valuechannel3.append(matrix_of_value[2:15][0])
						counter += 1
	       				else: #Иначе отправка данных в Bluemix + очистка FiFo
						# 
						for i in range(4):
							for j in range (16):
								learnData+=valuechannel1[i][j]
								learnData+=valuechannel2[i][j]
								learnData+=valuechannel3[i][j]
						print "__________________"
						print learnData
						print "__________________"
						counter = 0
						background_image=Tk.PhotoImage(file="right.png")
						time.sleep(0.5) #Задержка 500 мс
						begin_time = time.time()
						break_flag = True



def constructPerceptron (name, numNeurons):
    """Возвращает необученную сеть

    Аргументы:
    name -- имя сети, строка
    numNeurons -- число нейронов в каждом слое, список из целых чисел

    """
    # Создаём сеть
    net = FeedForwardNetwork(name)
    # Создаём слои и добавляем их в сеть
    prevLayer = None
    newLayer = None
    for i, val in enumerate(numNeurons):
        # Если слой входной, он линейный
        if (i == 0): 
            newLayer = LinearLayer(val, 'input')
            net.addInputModule(newLayer)
            prevLayer = newLayer
        # Если слой выходной, он линейный    
        elif (i == len(numNeurons) - 1):
            newLayer = LinearLayer(val, 'output')
            net.addOutputModule(newLayer)
        # Иначе - слой сигмоидный   
        else:
            newLayer = SigmoidLayer(val, 'hidden_' + str(i))
            net.addModule(newLayer)    
        # Если слой не входной, создаём связь между новым и предыдущим слоями
        if (i > 0):
            conn = FullConnection(prevLayer, newLayer, 'conn_' + str(i))
            net.addConnection(conn)
            prevLayer = newLayer
    # Готовим сеть к активации, упорядочивая её внутреннюю структуру        
    net.sortModules()
    # Готово
    return net	


def constructDataset (name, learnData):
    """Возвращает обучающую выборку в формате PyBrain

    Аргументы:
    name -- имя набора данных, строка
    learnData -- данные для обучения: список кортежей типа "входные признаки - выходной вектор"

    """
    # Вычисляем размерность входных данных
    dimIn = len(learnData[0][0])
    dimOut = len (learnData[0][1])
    ds = SupervisedDataSet(dimIn, dimOut)
    for d in learnData:
        ds.addSample(d[0], d[1])
    return ds

def trainNetwork (net, trainData):
    """Возвращает сеть, прошедшую 1 эпоху обучения, и оценку ошибки

    Аргументы:
    net - нейронная сеть, PyBrain network
    trainData -- обучающий набор данных, PyBrain dataset

    """
      # Трейнер для обучения с учителем
    trainer = BackpropTrainer(net, trainData)
      # Запускаем трейнер на 1 эпоху и запоминаем оценку ошибки 
    coef = trainer.train()
    return (net, coef)

def saveNetwork (net, name):
    """Экспорт нейронной сети в файл

    Аргументы:
    net - нейронная сеть, PyBrain network
    name -- имя файла, строка

    """
    NetworkWriter.writeToFile(net, name)

def importNetwork (name):
    """Возвращает импортированную из файла нейронную сеть

    Аргументы:
    name - имя файла, строка

    """
    return NetworkReader.readFrom(name)



# Обработка после кноки start
def lets_start(): 
	global FSM_state
	global CMD
	global root
	global education	
 
	#Ждем старта
	while not run_state: 
		time.sleep(0.1)

	# Работа с последовательном портом и файлом
	if state:
		print "Working with serial"
	  	ser_init()
	else:
		print "Working with file"
		file_init()

	# Инициализация сети
	n = constructPerceptron('perc', [64*3, 10, 3, 1]) # Создаём перцептрон

	def medium_update():
                global medium
                global res_array
                sum01 = [0,0]
                count01 = [0,0]
                for i in res_array:
                        sum01[i[1]] += i[0]
                        count01[i[1]] += 1
                if count01[0] * count01[1] == 0:
                        return #ex by zero... 
                medium = (sum01[1] / count01[1] + sum01[0] / count01[0]) / 2
                print medium

	
	def main_main(): 
                max1 = 0 #max(recog_array)
                min1 = 0 #min(recog_array)
                #global medium
                #global res_array
                #medium =0 #(max1 + min1) / 2
                s = 0
                col = 0
                def on_check():
                        global trained_net
                        global medium
                        receive_data_from_eeg()
                        # Активизируем сеть! На вход подаем список из 64*3 чисел - вектор входных признаков
                        recognition = trained_net.activate(learnData)
                        print recognition
                        res = recognition[0]
                        if res < medium:
                                print "not concentrate"
                        else:
                                print "concentrate"
                ### доп эксперимент
                def on_concentrateN():
                        global trained_net
                        global res_array
                        receive_data_from_eeg()
                        recognition = trained_net.activate(learnData)
                        print recognition
                        res_array.append([recognition[0], 0])
                        medium_update()
                def on_not_concentrateN():
                        global trained_net
                        global res_array
                        receive_data_from_eeg()
                        recognition = trained_net.activate(learnData)
                        print recognition
                        res_array.append([recognition[0], 1])
                        medium_update()

                def change_state_net():
                        global trained_net
                        # Импортировать сеть
                        trained_net = importNetwork('net.xml')

			FSM_state = 1 #Work, cmd = left	
			#time.sleep(3)
                        checkButton = Tk.Button(root, text = "check", command = on_check)
                        checkButton.pack()

                        concentrateNButton = Tk.Button(root, text = "concentrateNorm", command = on_concentrateN)
                        concentrateNButton.pack()

                        notconcentrateNButton = Tk.Button(root, text = "NOTconcentrateNorm", command = on_not_concentrateN)
                        notconcentrateNButton.pack()
                       
                def change_state():
                        global trained_net
			# Формирование обучающей выборки
			#print education			
			# Данные для обучения data поступают от ЭЭГ в описанном выше формате - списке обучающих пар
			ds = constructDataset('data', education)
			# Запуск 1 полной эпохи обучения
			(trained_net, err) = trainNetwork (n, ds)

                        # TODO
			# Сохранить сеть
                        saveNetwork(trained_net, 'net.xml')
                        # Импортировать сеть
                        #new_n = importNetwork('net.xml')

			FSM_state = 1 #Work, cmd = left	
			#time.sleep(3)
                        checkButton = Tk.Button(root, text = "check", command = on_check)
                        checkButton.pack()

                        concentrateNButton = Tk.Button(root, text = "concentrateNorm", command = on_concentrateN)
                        concentrateNButton.pack()

                        notconcentrateNButton = Tk.Button(root, text = "NOTconcentrateNorm", command = on_not_concentrateN)
                        notconcentrateNButton.pack()
			
                def on_concentrate():
                        receive_data_from_eeg()
			education.append((learnData,[0]))
		def on_not_concentrate():
			receive_data_from_eeg()
			education.append((learnData,[1]))

                concentrateButton = Tk.Button(root, text = "concentrate", command = on_concentrate)
                concentrateButton.pack()

                notconcentrateButton = Tk.Button(root, text = "NOTconcentrate", command = on_not_concentrate)
                notconcentrateButton.pack()

                workButton = Tk.Button(root, text = "startwork", command = change_state)
                workButton.pack()

                workNetButton = Tk.Button(root, text = "work with ready net", command = change_state_net)
                workNetButton.pack()
                

        main_main()

#Изменение состояния
def go():	
	global run_state
	run_state = True



#Стартуем приложение
m = Thread(target=lets_start)
m.start()

#Интерфейс 
background_image=Tk.PhotoImage(file="start.png")
background_label = Tk.Label(root, image=background_image)
background_label.place(x=0, y=0, relwidth=1, relheight=1)
root.wm_geometry("1000x650+20+40")
root.title('Go read your brain')
startButton = Tk.Button(root, text = "start", command = go)
startButton.pack()
root.mainloop()
