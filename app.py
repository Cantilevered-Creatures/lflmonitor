from flask import Flask, request, render_template, redirect, url_for

from concurrent.futures import ThreadPoolExecutor, Future
executor = ThreadPoolExecutor(1)

import colorsys
import time
import datetime
import math
import threading

import RPi.GPIO as GPIO
import picamera

import blinkt

# Clear blinkt in case it was left on after a unexpected shutdown or crash
blinkt.clear()
blinkt.show()

bgThread = None

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

doorSwitch=2
doorSwitchSTS = GPIO.LOW

class Door(object):
  def __init__(self):
    self.lock = threading.Lock()
    self._isRunning = False
  def start(self):
      self.lock.acquire()
      self._isRunning = True
      self.lock.release()
  def stop(self):
      self.lock.acquire()
      self._isRunning = False
      self.lock.release()
  def canIRun(self):
    print("beforeLock")
    self.lock.acquire()
    print(self._isRunning)
    if (self._isRunning):
      self.lock.release()
      return False
    else:
      self._isRunning = True
      self.lock.release()
      return True  

door = Door()

GPIO.setup(doorSwitch, GPIO.IN, pull_up_down=GPIO.PUD_UP)

app = Flask(__name__)

def rainbow(runSeconds: int = 5, clear: bool = True):
  spacing = 360.0 / 16.0
  hue = 0

  blinkt.set_clear_on_exit()
  blinkt.set_brightness(1.0)

  start_time = datetime.datetime.now()

  tSeconds = (datetime.datetime.now() - start_time).total_seconds()

  while (tSeconds < runSeconds) :
    hue = int(time.time() * 100) % 360
    for x in range(blinkt.NUM_PIXELS):
      offset = x * spacing
      h = ((hue + offset) % 360) / 360.0
      r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(h, 1.0, 1.0)]
      blinkt.set_pixel(x, r, g, b)

    # Increment brightness over the run
    blinkt.set_brightness(math.ceil(tSeconds/runSeconds*10)/10)
    #print(math.ceil(tSeconds/runSeconds*10)/10)

    blinkt.show()
    time.sleep(0.01)
    tSeconds = (datetime.datetime.now() - start_time).total_seconds()
  
  if clear:
    blinkt.clear()
    blinkt.show()

def takepicture(imageName: str):
  with picamera.PiCamera() as camera:
    camera.resolution = (1920, 1080)
    time.sleep(1) # Camera warm-up time
    filename = 'images/%s.jpg' % imageName
    camera.capture(filename)

def doorSwitch_callback(channel):
  print("Callback")
  doorRoutine(door)

def doorRoutine(door: Door):
  print("knocking")
  if door.canIRun():

    rainbow(5, False)
    blinkt.set_all(255, 255, 255, 1.0)
    blinkt.show()

    start_time = datetime.datetime.now()

    tSeconds = (datetime.datetime.now() - start_time).total_seconds()

    while(GPIO.input(doorSwitch) == 0 and tSeconds < 300):
      takepicture('{:%Y-%m-%d%H:%M:%S}'.format(datetime.datetime.now()))
      time.sleep(2)
      tSeconds = (datetime.datetime.now() - start_time).total_seconds()

    time.sleep(2)

    takepicture('{:%Y-%m-%d%H:%M:%S}'.format(datetime.datetime.now()))

    brightness = 1.0

    while(brightness > 0):
      blinkt.set_brightness(brightness)
      blinkt.show()
      time.sleep(0.1)
      brightness = brightness - 0.1

    blinkt.clear()
    blinkt.show()

    door.stop()

@app.route('/', methods=['GET', 'POST'])
def index():
  
  if request.method == 'GET':
    doorSwitchSTS = GPIO.input(doorSwitch)
    now = datetime.datetime.now()
    timeString = now.strftime("%Y-%m-%d %H:%M")
    templateData = {
      'title' : 'HELLO!',
      'time': timeString,
      'door': doorSwitchSTS
    }
    return render_template('index.html', **templateData)
    
  if request.form['submit'] == 'Rainbow':
    executor.submit(rainbow, int(request.form['secRainbow']))
  elif request.form['submit'] == 'Take Picture':
    takepicture('images/test')
  
  return redirect(url_for('index'))

GPIO.add_event_detect(doorSwitch, GPIO.RISING, callback=doorSwitch_callback, bouncetime=1000)

if __name__ == '__main__':
  app.run(port=5000)