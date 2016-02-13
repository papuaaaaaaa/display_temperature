import time
import math
import RPi.GPIO as GPIO
import threading

class ShiftRegister:
    def __init__(self, rclk, srclk, ser):
        self.rclk = rclk
        self.srclk = srclk
	self.ser = ser
	GPIO.setup(self.rclk, GPIO.OUT)
	GPIO.setup(self.srclk, GPIO.OUT)
	GPIO.setup(self.ser, GPIO.OUT)
    def __shift(self,pin):
        GPIO.output(pin, True)
        GPIO.output(pin, False)
    def output(self, num_ary):
	for n in num_ary:
            GPIO.output(self.ser, bool(n))
	    self.__shift(self.srclk)
	self.__shift(self.rclk)

rlock = threading.RLock()

class AnodeCommonLeidThread(threading.Thread):
    def __init__(self, digits, outputor):
        threading.Thread.__init__(self)
        self.digits = digits
	self.running = True
	self.data_str = '000'
	self.outputor = outputor
	for d in digits:
	    GPIO.setup(d, GPIO.OUT)		
    def __serialize(self, num, isDot):
        dt = int(not isDot)
        data = ((dt,1,0,0,0,0,0,0),#0
            (dt,1,1,1,1,0,0,1),  #1
            (dt,0,1,0,0,1,0,0),  #2
            (dt,0,1,1,0,0,0,0),  #3
            (dt,0,0,1,1,0,0,1),  #4
            (dt,0,0,1,0,0,1,0),  #5
            (dt,0,0,0,0,0,1,0),  #6
            (dt,1,1,1,1,0,0,0),  #7
            (dt,0,0,0,0,0,0,0),  #8
            (dt,0,0,1,1,0,0,0))  #9
	return data[num]
    def set(self, data_str):
        rlock.acquire()
	self.data_str = data_str.replace('.', '')
	rlock.release()
    def run(self):
        while self.running:
            rlock.acquire()
            for d in range(3):
		for dd in range(3):
		    pin = self.digits[dd]
		    GPIO.output(pin, d == dd)
		self.outputor.output(self.__serialize(int(self.data_str[d]), d == 1))
	        time.sleep(0.005)
	    rlock.release()
    def stop(self):
        self.running = False
	
RCLK = 14
SRCLK = 15
SER = 18
DIGIT = [17,27,22]  

GPIO.setmode(GPIO.BCM) 

reg = ShiftRegister(RCLK,SRCLK,SER)
led = AnodeCommonLeidThread(DIGIT, reg)
led.start();
try:
    while True:
        tfile = open("/sys/bus/w1/devices/28-00000647df2c/w1_slave")
        text = tfile.read()
	tfile.close()
        secondline = text.split("\n")[1]
 	temperaturedata = secondline.split(" ")[9]
 	temperature = round(float(temperaturedata[2:]) / 1000, 1)
 	print temperature
        led.set(str(temperature))
        time.sleep(5)
except KeyboardInterrupt:
    print '\nbreak'
led.stop()
led.join()
GPIO.cleanup()
