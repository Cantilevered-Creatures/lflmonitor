import json
import os
from Song import Song

class MusicInfo():

  MUSIC_EXTENSIONS = {'mp3'}

  def __init__(self, musicPath):
    self.musicPath = musicPath
    self.musicFiles = []
    self.playList = []
    self.currentSong = None
    self.loadMusic()
    self.playListFile = "{}/playlist.cfg".format(self.musicPath)
    self.loadPlayList()

  def loadMusic(self):
    it = os.scandir(self.musicPath)
    for entry in it:
      if not entry.name.startswith('.') and entry.is_file() and entry.name.rsplit('.',1)[1].lower() in self.MUSIC_EXTENSIONS:
        self.musicFiles.append(Song(entry.path))

  def loadPlayList(self):
    if os.path.exists(self.playListFile):
      if os.path.getsize(self.playListFile) > 0:
        with open(self.playListFile, 'r') as filePlaylist:
          playListNames = json.load(filePlaylist)

          for playListName in playListNames:
            tmpSong = self.getSong(playListName, True)
            if tmpSong:
              self.playList.append(tmpSong)

          self.updatePlayListOrder(playListNames)

  def addPlayList(self,name):
    tmpSong = self.getSong(name, True)
    if tmpSong:
      self.playList.append(tmpSong)

  def updatePlayList(self, songNames):
    for songName in songNames:
      if songName not in self.listPlayList():
        self.addPlayList(songName)

    for songName in self.listPlayList():
      if songName not in songNames:
        self.musicFiles.append(self.getPlayListItem(songName, True))
    
    with open(self.playListFile, 'w') as filePlaylist:
      json.dump(self.listPlayList(), filePlaylist, indent=2, separators=(',', ': '))

    self.updatePlayListOrder(songNames)

  def updatePlayListOrder(self, songNames):
    for i, songName in enumerate(songNames):
      if i == len(songNames)-1:
        self.getPlayListItem(songName).setNext(i, self.getPlayListItem(songNames[0]))
      else:
        self.getPlayListItem(songName).setNext(i, self.getPlayListItem(songNames[i+1]))

    self.playList.sort(key=lambda x: x.order)

  def listMusic(self):
    tmpList = []
    for song in self.musicFiles:
        tmpList.append(song.name)
    return tmpList

  def listPlayList(self):
    tmpList = []
    for song in self.playList:
        tmpList.append(song.name)
    return tmpList

  def getSong(self, name, pop=False):
    for i, x in enumerate(self.musicFiles):
        if x.name == name:
          if pop:
            return self.musicFiles.pop(i)
          else:
            return x
    return None
  
  def getPlayListItem(self, name, pop=False):
    for i, x in enumerate(self.playList):
        if x.name == name:
          if pop:
            return self.playList.pop(i)
          else:
            return x
    return None

  def setCurrentSong(self, name):
    tmpSong = self.getSong(name)
    if not tmpSong:
      tmpSong = self.getPlayListItem(name)
    self.currentSong = tmpSong

  