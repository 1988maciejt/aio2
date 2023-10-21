import atexit
import shutil

_DIRS_TO_CLEAN = []
_DIRS_FILE_NAME = "/tmp/aio_dirs_to_clean"

class AioAuto:
  
  @staticmethod
  def _removeDirs(lst : list) -> list:
    Failed = []
    for d in lst:
      try:
        shutil.rmtree(d)
      except: 
        Failed.append(d)
    return Failed
      
  @staticmethod
  def _updateDirsFile():
    from libs.files import File
    global _DIRS_FILE_NAME, _DIRS_TO_CLEAN
    try:
      File.writeObject(_DIRS_FILE_NAME, _DIRS_TO_CLEAN)
    except:
      pass
  
  @staticmethod
  def atStart():
    from libs.files import File
    global _DIRS_FILE_NAME
    try:
      Dirs = File.readObject(_DIRS_FILE_NAME)
      AioAuto._removeDirs(Dirs)
    except:
      pass
    File.remove(_DIRS_FILE_NAME)
    
  @staticmethod
  def atExit():
    global _DIRS_TO_CLEAN
    Failed = AioAuto._removeDirs(_DIRS_TO_CLEAN)
    _DIRS_TO_CLEAN = Failed
    AioAuto._updateDirsFile()
    
  def registerDirToClean(Dir : str):
    global _DIRS_TO_CLEAN
    if Dir not in _DIRS_TO_CLEAN:
      _DIRS_TO_CLEAN.append(Dir)
      AioAuto._updateDirsFile()
  
  def unregisterDirToClean(Dir : str):
    global _DIRS_TO_CLEAN
    if Dir in _DIRS_TO_CLEAN:
      _DIRS_TO_CLEAN.remove(Dir)
      AioAuto._updateDirsFile()