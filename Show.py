from threading import Lock, Thread

import os
import sys

sys.path.insert(0, "./lightshowpi/py")
os.environ["SYNCHRONIZED_LIGHTS_HOME"] = "{}/lightshowpi".format(os.curdir)

from lightshowpi.py.synchronized_lights import Lightshow


class Show(object):

  def __init__(self):
    self.lock = Lock()
    self.isRunning = False
    self._thread = None
    self.ls = Lightshow()

  def canIRun(self):
    self.lock.acquire()
    if (self.isRunning):
      self.lock.release()
      return False
    else:
      self.isRunning = True
      self.lock.release()
      return True

  def setConfig(self, configName):
    self.ls.configPath = "{}.cfg".format(configName)
    self.ls.loadHC()

  def startShow(self, songPath, callback=None):
    if (self.canIRun()):
      self.ls.filepath = songPath

      self._thread = Thread(target=self.showWatcher, args=[callback])
      self._thread.start()
      return True
    else:
      return False

  def showWatcher(self, callback):
    self.ls.play_song()

    self.lock.acquire()
    self.isRunning = False
    self.lock.release()

    if callback:
      callback()