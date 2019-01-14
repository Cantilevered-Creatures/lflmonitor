from flask import Flask, request, render_template, redirect, url_for, send_from_directory, current_app
from flask_paginate import Pagination, get_page_args
from flask_security import Security, login_required, SQLAlchemySessionUserDatastore, logout_user
from database import dbconfig
from models import User, Role

from itertools import zip_longest

import colorsys
import time
import datetime
import math
import threading
import os

import RPi.GPIO as GPIO

import blinkt

app = Flask(__name__)

try:
  app.config.from_pyfile('/etc/lflmonitor/app.cfg')
except FileNotFoundError:
  if(app.config['ENV']!='development'):
    app.config.from_pyfile('app.cfg')
  else:
    app.config.from_pyfile('app.cfg.example')

app.secret_key = app.config['SECRET_KEY']

# picamera can only import on a pi
if(app.config['ENV']!='development'):
  import picamera
  db = dbconfig('/tmp/test.db')
else:
  db = dbconfig(app.config['DB_PATH'])

user_datastore = SQLAlchemySessionUserDatastore(db.db_session, User, Role)
security = Security(app, user_datastore)

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
    self.lock.acquire()
    if (self._isRunning):
      self.lock.release()
      return False
    else:
      self._isRunning = True
      self.lock.release()
      return True  

door = Door()

GPIO.setup(doorSwitch, GPIO.IN, pull_up_down=GPIO.PUD_UP)

@app.before_first_request
def create_user():
    #init_db()
    admin_role = [user_datastore.find_role('Admin')]
    if(admin_role[0]==None):
      user_datastore.create_role(name='Admin', description='Admin group')
      db.db_session.commit()
      admin_role = [user_datastore.find_role('Admin')]

    if(not user_datastore.find_user(email=app.config['ADMIN_USER'])):
      user_datastore.create_user(email=app.config['ADMIN_USER'], password=app.config['ADMIN_PASS'], roles=admin_role)
      db.db_session.commit()

def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

def rainbow(runSeconds: int = 5, clear: bool = True, decreaseBrightness: bool = False):
  spacing = 360.0 / 16.0
  hue = 0

  blinkt.set_clear_on_exit()

  start_time = datetime.datetime.now()

  tSeconds = (datetime.datetime.now() - start_time).total_seconds()

  while (tSeconds < runSeconds) :
    hue = int(time.time() * 100) % 360

    for x in range(blinkt.NUM_PIXELS):
      offset = x * spacing
      h = ((hue + offset) % 360) / 360.0
      r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(h, 1.0, 1.0)]
      blinkt.set_pixel(x, r, g, b)

    brightness = math.ceil((tSeconds/runSeconds)*10)/10

    if(decreaseBrightness):
      brightness = 1 - brightness
    
    blinkt.set_brightness(brightness)

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
  t = threading.Thread(target=doorRoutine, args=(door,))
  t.start()

def doorRoutine(door: Door):
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

    rainbow(2,True,True)

    door.stop()

@app.route('/logout')
def logout():
  logout_user()
  return redirect(url_for('index'))

@app.route('/imagelist')
@login_required
def imagelist():

  search = False
  q = request.args.get('q')
  if q:
      search = True

  images = []

  it = os.scandir('./images/')
  for entry in it:
      if not entry.name.startswith('.') and entry.name.endswith('.jpg') and entry.is_file():
          images.append(entry.name)

  images.sort()

  page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
  print(per_page)
  pagination = Pagination(
    page=page, 
    total=len(images), 
    search=search, 
    record_name='images',
    per_page=per_page,
    format_total=True,
    format_number=True,
    css_framework=current_app.config.get('CSS_FRAMEWORK', 'sm'),
    link_size=current_app.config.get('LINK_SIZE', 'sm'),
    alignment=current_app.config.get('LINK_ALIGNMENT', ''),
    show_single_page=current_app.config.get('SHOW_SINGLE_PAGE', 'sm')
    )
  
  pageimages = grouper(images[offset:offset+per_page], 3)
  
  templateData = {
    'pagination' : pagination,
    'images': pageimages,
    'page' : page,
    'per_page' : per_page
  }

  return render_template('imagelist.html', **templateData)

@app.route('/images/<path:path>')
@login_required
def send_image(path):
    return send_from_directory('images', path)

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():

  doorSwitchSTS = GPIO.input(doorSwitch)
  now = datetime.datetime.now()
  timeString = now.strftime("%Y-%m-%d %H:%M")
  templateData = {
    'title' : 'HELLO!',
    'time': timeString,
    'door': doorSwitchSTS
  }
  
  if request.method == 'POST':
    if request.form['submit'] == 'Rainbow':
      t = threading.Thread(target=doorRoutine, args=(door,))
      t.start()
    elif request.form['submit'] == 'Take Picture':
      takepicture('images/test')
    elif request.form['submit'] == 'Exec Python':
      templateData['execcmd'] = request.form['exec']
      templateData['execoutput'] = exec(templateData['execcmd'])
  
  return render_template('index.html', **templateData)

GPIO.add_event_detect(doorSwitch, GPIO.FALLING, callback=doorSwitch_callback, bouncetime=1000)

if __name__ == '__main__':
  app.run(port=5000)