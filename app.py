from flask import Flask, request, render_template, redirect, url_for

from concurrent.futures import ThreadPoolExecutor, Future
executor = ThreadPoolExecutor(1)

import colorsys
import time
import datetime
import math

import RPi.GPIO as GPIO

import blinkt

bgThread = None

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

doorSwitch=2
doorSwitchSTS = GPIO.LOW

GPIO.setup(doorSwitch, GPIO.IN, pull_up_down=GPIO.PUD_UP)

app = Flask(__name__)

def rainbow(runSeconds: int = 5):
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
    print(math.ceil(tSeconds/runSeconds*10)/10)

    blinkt.show()
    time.sleep(0.001)
    tSeconds = (datetime.datetime.now() - start_time).total_seconds()

  blinkt.clear()
  blinkt.show()

def doorSwitch_callback(channel):
  executor.submit(rainbow)

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
    executor.submit(rainbow, request.form['secRainbow'])
  
  return redirect(url_for('index'))
  

GPIO.add_event_detect(2, GPIO.FALLING, callback=doorSwitch_callback, bouncetime=300)

if __name__ == '__main__':
  app.run(port=5000)