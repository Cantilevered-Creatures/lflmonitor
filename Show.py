from threading import Thread
from flask_caching import Cache

import os
import sys

sys.path.insert(0, "./lightshowpi/py")
os.environ["SYNCHRONIZED_LIGHTS_HOME"] = "{}/lightshowpi".format(os.curdir)

from lightshowpi.py.synchronized_lights import Lightshow


class Show(object):

  def __init__(self, cache: Cache):
    self.cache = cache
    if not self.cache.get("showRunning"):
      self.cache.set("showRunning", False)
    self._thread = None
    self.ls = Lightshow()

  def canIRun(self):
    if (self.cache.get("showRunning")):
      return False
    else:
      self.cache.set("showRunning", True)
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

    self.cache.set("showRunning", False)

    if callback:
      callback()

  def isRunning(self):
    return self.cache.get("showRunning")