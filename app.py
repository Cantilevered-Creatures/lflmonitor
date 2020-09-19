from flask import Flask, flash, request, render_template, redirect, url_for, send_from_directory, current_app
from flask_paginate import Pagination, get_page_args
from flask_security import Security, login_required, SQLAlchemySessionUserDatastore, logout_user
from flask_restful import Resource, Api
from database import dbconfig
from models import User, Role
from MusicInfo import MusicInfo

from werkzeug.utils import secure_filename

from itertools import zip_longest
from functools import total_ordering

from pydub import AudioSegment
import simpleaudio as sa

import colorsys
import datetime
import json
import math
import os
import re
import rrdtool
import subprocess
import sys
import threading
import time
import urllib

sys.path.insert(0, "./lightshowpi/py")
os.environ["SYNCHRONIZED_LIGHTS_HOME"] = "{}/lightshowpi".format(os.curdir)

from lightshowpi.py.synchronized_lights import Lightshow

app = Flask(__name__)
api = Api(app)

import RPi.GPIO as GPIO

from bibliopixel.layout.strip import *
from bibliopixel.drivers.driver_base import *
from bibliopixel.drivers.SPI import SPI
import bibliopixel.colors as colors

ls = Lightshow()

shortDateOrder = {
  's': 1,
  'm': 2,
  'h': 3,
  'd': 4,
  'w': 5,
  'M': 6,
  'y': 7
}

secRainbow = 5

intVolume = 0
configName = 'defaults'
MUSIC_FOLDER = 'music'

musicInfo = MusicInfo(MUSIC_FOLDER)

curSong = ''

songPlaying = False
# showProcess = None
showThread = threading.Thread()

rePath = re.compile("[^0-9]*([0-9]*)([smhdwMy]).*")

@total_ordering
class XMLFile(object):
  def __init__(self, path):
    self.path = path
    self.quotepath = urllib.parse.quote(path)
    match = rePath.search(path)
    self.shortDate = match.group(2)
    self.dateCount = int(match.group(1))
  @staticmethod
  def _is_valid_operand(other):
    return (hasattr(other, "shortDate") and hasattr(other, "dateCount"))
  def __eq__(self, other):
    if not self._is_valid_operand(other):
      return NotImplemented
    return ((shortDateOrder[self.shortDate], self.dateCount) == (shortDateOrder[other.shortDate], other.dateCount))
  def __ge__(self, other):
    if not self._is_valid_operand(other):
      return NotImplemented
    return (shortDateOrder[self.shortDate] >= shortDateOrder[other.shortDate] and self.dateCount >= other.dateCount)
  def __gt__(self, other):
    if not self._is_valid_operand(other):
      return NotImplemented
    return (shortDateOrder[self.shortDate] > shortDateOrder[other.shortDate] or (shortDateOrder[self.shortDate] == shortDateOrder[other.shortDate] and self.dateCount > other.dateCount))
  def __le__(self, other):
    if not self._is_valid_operand(other):
      return NotImplemented
    return (shortDateOrder[self.shortDate] <= shortDateOrder[other.shortDate] and self.dateCount <= other.dateCount)
  def __lt__(self, other):
    if not self._is_valid_operand(other):
      return NotImplemented
    return (shortDateOrder[self.shortDate] < shortDateOrder[other.shortDate] or (shortDateOrder[self.shortDate] == shortDateOrder[other.shortDate] and self.dateCount < other.dateCount))

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

# if __name__ == '__main__':
#   app.run(host='0.0.0.0',port=5000)

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

def voltageLogger():
  while(True):
    if(app.config['BATTERY_PIN'] > -1):
      vBattery = round(chanBattery.voltage * 5, 3)
    else:
      vBattery = 0

    if(app.config['PANEL_PIN'] > -1):
      vPanel = round(chanPanel.voltage * 5, 3)
    else:
      vPanel = 0

    rrdtool.update(app.config['RRD_PATH'], "N:{}:{}".format(vBattery, vPanel))
    time.sleep(app.config['RRD_INTERVAL'])

def led_setbrightness(brightness: int):
  if(brightness<0):
    brightness = 0
  elif(brightness>255):
    brightness = 255
  
  ledStrip.brightness = brightness
  ledStrip.push_to_driver()

def led_clear():
  ledStrip.all_off()
  ledStrip.push_to_driver()
  

def rainbow(runSeconds: int = 5, clear: bool = True, decreaseBrightness: bool = False):
  spacing = 360.0 / 16.0
  hue = 0

  start_time = datetime.datetime.now()

  tSeconds = (datetime.datetime.now() - start_time).total_seconds()

  while (tSeconds < runSeconds) :
    hue = int(time.time() * 100) % 360

    for x in range(app.config['LED_COUNT']):
      offset = x * spacing
      h = int((hue + offset) % 360)
      ledStrip.setHSV(x, (h,255,255))

    brightness = math.ceil((tSeconds/runSeconds)*10)/10

    if(decreaseBrightness):
      brightness = 1 - brightness

    ledStrip.set_brightness(int(brightness *255))

    ledStrip.push_to_driver()

    time.sleep(0.01)
    tSeconds = (datetime.datetime.now() - start_time).total_seconds()

  if clear:
    led_clear()

def colorrotate(runSeconds: int = 5, clear: bool = True, decreaseBrightness: bool = False):
  hue = 0

  start_time = datetime.datetime.now()

  tSeconds = (datetime.datetime.now() - start_time).total_seconds()

  while (tSeconds < runSeconds) :
    brightness = math.ceil((tSeconds/runSeconds)*10)/10

    if(decreaseBrightness):
      brightness = 1 - brightness

    hue = int(time.time() * 100) % 360
    h = int(hue % 360)
    
    led_setbrightness(int(brightness * 255))

    ledStrip.fillHSV((h,255,255))

    ledStrip.push_to_driver()

    time.sleep(0.005)
    tSeconds = (datetime.datetime.now() - start_time).total_seconds()

  if clear:
    led_clear()

def takepicture(imageName: str):
  if(app.config['ENABLE_CAMERA']):
    with picamera.PiCamera() as camera:
      camera.resolution = (1920, 1080)
      time.sleep(1) # Camera warm-up time
      filename = 'images/%s.jpg' % imageName
      camera.capture(filename)

def doorSwitch_callback(channel):
  t = threading.Thread(target=doorRoutine, args=[door])
  t.start()

def doorRoutine(door: Door):
  global showThread,configName
  if door.canIRun():
    showRunning = True

    if not showThread.is_alive():
      configName = "defaults"
      startShow('01_-_Reading_Rainbow_Theme_Song.mp3', doorLightsOn)

    #colorrotate(4, False)

    start_time = datetime.datetime.now()

    tSeconds = (datetime.datetime.now() - start_time).total_seconds()

    while(GPIO.input(doorSwitch) == 0 and tSeconds < 300):
      takepicture('{:%Y-%m-%d%H:%M:%S}'.format(datetime.datetime.now()))
      time.sleep(2)
      tSeconds = (datetime.datetime.now() - start_time).total_seconds()

    time.sleep(2)

    takepicture('{:%Y-%m-%d%H:%M:%S}'.format(datetime.datetime.now()))

    colorrotate(2,True,True)

    door.stop()

def doorLightsOn():
  if GPIO.input(doorSwitch) == 0:
    ledStrip.brightness = 255
    ledStrip.fillRGB(255, 255, 255)
    ledStrip.push_to_driver()

def startShow(songName, callback = None):
  global showThread, configName, musicInfo
  
  musicInfo.setCurrentSong(songName)

  if showThread.is_alive():
    showThread._stop()

  ls.filepath = musicInfo.currentSong.filePath
  ls.configPath = "{}.cfg".format(configName)
  ls.loadHC()

  showThread = threading.Thread(target=showWatcher, args=[callback])
  showThread.start()

def showWatcher(callback):
  ls.play_song()
  if callback:
    callback()

def stopShow():
  global showThread, currentSong
  showThread._stop()
  curSong.name = ""

def setVolume():
  global intVolume
  command = ["amixer", "sset", "PCM", "{}%".format(intVolume)]
  subprocess.Popen(command)

def allowed_musicfile(fileName):
  return '.' in fileName and fileName.rsplit('.', 1)[1].lower() in MUSIC_EXTENSIONS

class currentSong(Resource):
  def get(self):
    global musicInfo, showThread
    tmpSongName = ""
    if musicInfo.currentSong and showThread.is_alive():
      tmpSongName = musicInfo.currentSong.name

    return { 'name': tmpSongName }

api.add_resource(currentSong, '/currentsong')

@app.route('/logout')
def logout():
  logout_user()
  return redirect(url_for('index'))

@app.route('/musicPlayer', methods=['GET', 'POST'])
@login_required
def musicPlayer():
  global intVolume, configName, playList
  global musicInfo

  if request.method == 'POST':
    if 'submit' in request.form:
      if request.form['submit'] == 'SetVolume':
        intVolume = int(request.form['intVolume'])
        setVolume()
      elif request.form['submit'] == 'UploadMusic':
        # check if the post request has the file part
        if 'fileMusic' not in request.files:
          flash('No file included')
          return redirect(request.url)
        fileMusic = request.files['fileMusic']
        # if user does not select file, browser also
        # submit an empty part without filename
        if fileMusic.filename == '':
          flash('No file selected')
          return redirect(request.url)
        if fileMusic and allowed_musicfile(fileMusic.filename):
          filename = secure_filename(fileMusic.filename)
          fileMusic.save(os.path.join(MUSIC_FOLDER, filename))
      elif request.form['submit'] == 'stopMusic':
        stopShow()
    elif 'updatePlayList' in request.form:
      playList = request.form['playList'].split(',')
      musicInfo.updatePlayList(playList)
    elif 'playMusic' in request.form:
      configName = request.form['configName']
      startShow(request.form['playMusic'])

  templateData = {
    'intVolume' : intVolume,
    'musicFiles' : musicInfo.listMusic(),
    'playList' : musicInfo.listPlayList(),
    'configName' : configName
  }

  return render_template('musicPlayer.html', **templateData)

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

@app.route('/voltage')
@login_required
def voltage():

  xmlFiles = []

  it = os.scandir("{}/".format(app.config['XML_PATH']))
  for entry in it:
    if not entry.name.startswith('.') and entry.name.endswith('.xml') and entry.is_file():
      xmlFiles.append(XMLFile(entry.path))

  xmlFiles.sort()

  templateData = {
    'xmlpaths' : xmlFiles
  }

  return render_template('voltagegraph.html', **templateData)

@app.route('/images/<path:path>')
@app.route('/images/350/<path:path>')
@login_required
def send_image(path):
    return send_from_directory('images', path)

@app.route('/xml/<path:path>')
@login_required
def send_xml(path):
    return send_from_directory(app.config['XML_PATH'], path)

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():

  doorSwitchSTS = GPIO.input(doorSwitch)
  now = datetime.datetime.now()
  timeString = now.strftime("%Y-%m-%d %H:%M")
  global secRainbow
  global songPlaying

  if request.method == 'POST':
    secRainbow = int(request.form['secRainbow'])
    if request.form['submit'] == 'Rainbow':
      t = threading.Thread(target=rainbow, args=(secRainbow,))
      t.start()
    elif request.form['submit'] == 'ColorRotate':
      t = threading.Thread(target=colorrotate, args=(secRainbow,))
      t.start()
    elif request.form['submit'] == 'Take Picture':
      ledStrip.brightness = 255
      ledStrip.fillRGB(255, 255, 255)
      ledStrip.push_to_driver()
      time.sleep(1)
      takepicture('test')
      led_clear()
    elif request.form['submit'] == 'StartSong':
      songPlaying = True
      t = threading.Thread(target=song, args=())
      t.start()
    elif request.form['submit'] == 'StopSong':
      songPlaying = False
    elif request.form['submit'] == 'setColor':
      ledStrip.brightness = 255
      ledStrip.fillRGB(*colors.name_to_color(request.form['colorList']))
      ledStrip.push_to_driver()
    elif request.form['submit'] == 'clearColor':
      led_clear()
    

  templateData = {
    'title' : 'HELLO!',
    'time': timeString,
    'door': doorSwitchSTS,
    'secRainbow': secRainbow,
    'colors': colors.tables.CANONICAL_DICT
  }

  try:
    templateData['batteryVoltage'] = round(chanBattery.voltage * 5, 2)
    templateData['panelVoltage'] = round(chanPanel.voltage * 5, 2)
  except NameError:
    print("Ignoring name error")

  return render_template('index.html', **templateData)

# picamera can only import on a pi
if(app.config['ENV']!='development'):
  import picamera
  import board
  import busio
  import adafruit_ads1x15.ads1115 as ADS
  from adafruit_ads1x15.analog_in import AnalogIn

  try:
    app.config.from_pyfile('/etc/lflmonitor/app.cfg')
  except FileNotFoundError:
    app.config.from_pyfile('app.cfg')

  # Create the I2C bus
  i2c = busio.I2C(board.SCL, board.SDA)

  # Create the ADC object using the I2C bus
  try:
    ads = ADS.ADS1115(i2c)

    if(app.config['BATTERY_PIN'] > -1 or app.config['PANEL_PIN'] > -1):
      # Create single-ended input on channel 0
      chanBattery = AnalogIn(ads, app.config['BATTERY_PIN'])
      chanPanel = AnalogIn(ads, app.config['PANEL_PIN'])

      t = threading.Thread(target=voltageLogger)
      t.start()
  except:
    print("Error loading ADC module, voltage will not be logged.")

else:
  app.config.from_pyfile('app.cfg.example')

ledDriver = SPI(ledtype=app.config['LED_TYPE'], num=app.config['LED_COUNT'], spi_interface='PYDEV', c_order=app.config['CHANNEL_ORDER'])
ledStrip = Strip(ledDriver)

intVolume=app.config['STARTING_VOLUME']

setVolume()

db = dbconfig(app.config['DB_PATH'])

app.secret_key = app.config['SECRET_KEY']

user_datastore = SQLAlchemySessionUserDatastore(db.db_session, User, Role)
security = Security(app, user_datastore)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

doorSwitch = app.config['DOOR_SWITCH']
doorSwitchSTS = GPIO.LOW

GPIO.setup(doorSwitch, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.add_event_detect(doorSwitch, GPIO.FALLING, callback=doorSwitch_callback, bouncetime=1000)