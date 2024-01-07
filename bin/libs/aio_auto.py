import atexit
import shutil

_DIRS_TO_CLEAN = []
_FILES_TO_CLEAN = []
_LOCAL_DIRS_TO_CLEAN = []
_LOCAL_FILES_TO_CLEAN = []
_DIRS_FILE_NAME = "/tmp/aio_dirs_to_clean"
_FILES_FILE_NAME = "/tmp/aio_files_to_clean"

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
  def _removeFiles(lst : list) -> list:
    from libs.files import File
    Failed = []
    for f in lst:
      if not File.remove(f):
        Failed.append(f)
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
  def _updateFilesFile():
    from libs.files import File
    global _FILES_FILE_NAME, _FILES_TO_CLEAN
    try:
      File.writeObject(_FILES_FILE_NAME, _FILES_TO_CLEAN)
    except:
      pass
  
  @staticmethod
  def atStart():
    from libs.files import File
    global _DIRS_FILE_NAME, _FILES_FILE_NAME, _DIRS_TO_CLEAN, _FILES_TO_CLEAN
    try:
      _DIRS_TO_CLEAN = File.readObject(_DIRS_FILE_NAME)
    except:
      pass
    try:
      _FILES_TO_CLEAN = File.readObject(_FILES_FILE_NAME)
    except:
      pass
    
  @staticmethod
  def atExit():
    from libs.files import File
    global _DIRS_FILE_NAME, _FILES_FILE_NAME, _LOCAL_DIRS_TO_CLEAN, _LOCAL_FILES_TO_CLEAN
    AioAuto._removeDirs(_LOCAL_DIRS_TO_CLEAN)
    AioAuto._removeDirs(_LOCAL_FILES_TO_CLEAN)
    
    
  @staticmethod
  def cleanOldTempDIrsAndFiles():
    global _LOCAL_DIRS_TO_CLEAN, _LOCAL_FILES_TO_CLEAN, _DIRS_TO_CLEAN, _FILES_TO_CLEAN
    Failed = []
    for D in _DIRS_TO_CLEAN:
      if D not in _LOCAL_DIRS_TO_CLEAN:
        try:
          shutil.rmtree(D)
        except:
          Failed.append(D)
    _DIRS_TO_CLEAN = Failed
    AioAuto._updateDirsFile()
    Failed = []
    for D in _FILES_TO_CLEAN:
      if D not in _LOCAL_FILES_TO_CLEAN:
        try:
          shutil.rmtree(D)
        except:
          Failed.append(D)
    _FILES_TO_CLEAN = Failed
    AioAuto._updateFilesFile()
    
  @staticmethod
  def cleanAllTempDIrsAndFiles():
    global _LOCAL_DIRS_TO_CLEAN, _LOCAL_FILES_TO_CLEAN, _DIRS_TO_CLEAN, _FILES_TO_CLEAN
    Failed = []
    for D in _DIRS_TO_CLEAN:
      try:
        shutil.rmtree(D)
      except:
        Failed.append(D)
    _DIRS_TO_CLEAN = Failed
    _LOCAL_DIRS_TO_CLEAN = []
    AioAuto._updateDirsFile()
    Failed = []
    for D in _FILES_TO_CLEAN:
      try:
        shutil.rmtree(D)
      except:
        Failed.append(D)
    _FILES_TO_CLEAN = Failed
    _LOCAL_FILES_TO_CLEAN = []
    AioAuto._updateFilesFile()
    
  def registerDirToClean(Dir : str):
    global _DIRS_TO_CLEAN, _LOCAL_DIRS_TO_CLEAN
    if Dir not in _LOCAL_DIRS_TO_CLEAN:
      _LOCAL_DIRS_TO_CLEAN.append(Dir)
    if Dir not in _DIRS_TO_CLEAN:
      _DIRS_TO_CLEAN.append(Dir)
      AioAuto._updateDirsFile()
  
  def unregisterDirToClean(Dir : str):
    global _DIRS_TO_CLEAN, _LOCAL_DIRS_TO_CLEAN
    if Dir in _LOCAL_DIRS_TO_CLEAN:
      _LOCAL_DIRS_TO_CLEAN.remove(Dir)
    if Dir in _DIRS_TO_CLEAN:
      _DIRS_TO_CLEAN.remove(Dir)
      AioAuto._updateDirsFile()
    
  def registerFileToClean(File : str):
    global _FILES_TO_CLEAN, _LOCAL_FILES_TO_CLEAN
    if File not in _LOCAL_FILES_TO_CLEAN:
      _LOCAL_FILES_TO_CLEAN.append(File)
    if File not in _FILES_TO_CLEAN:
      _FILES_TO_CLEAN.append(File)
      AioAuto._updateFilesFile()
  
  def unregisterFileToClean(File : str):
    global _FILES_TO_CLEAN, _LOCAL_FILES_TO_CLEAN
    if File in _LOCAL_FILES_TO_CLEAN:
      _LOCAL_FILES_TO_CLEAN.remove(File)
    if File in _FILES_TO_CLEAN:
      _FILES_TO_CLEAN.remove(File)
      AioAuto._updateFilesFile()
      
  