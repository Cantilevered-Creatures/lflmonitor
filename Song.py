import eyed3


class Song():

  def __init__(self, filePath):
    self.filePath = filePath
    self.next = None
    self.importMetadata()

  def importMetadata(self):
    idtag = eyed3.load(self.filePath)
    self.name = idtag.tag.title
    self.artist = idtag.tag.artist
    self.album = idtag.tag.album

  def setNext(self, listOrder, song):
    self.order = listOrder
    self.next = song

  def getNext(self):
    return self.next

  def removeNext(self):
    self.order = None
    self.next = None
