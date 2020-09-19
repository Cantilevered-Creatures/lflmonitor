import eyed3

class Song():

  def __init__(self, filePath):
    self.filePath = filePath
    self.importMetadata()

  def importMetadata(self):
    idtag = eyed3.load(self.filePath)
    self.name = idtag.tag.title

