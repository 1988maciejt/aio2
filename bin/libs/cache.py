from libs.files import *

GLOBALCACHE = {}


class Cache:
  
  @staticmethod
  def store(key, value) -> None:
    global GLOBALCACHE
    GLOBALCACHE[key] = value
    
  @staticmethod
  def recall(key, default = None):
    global GLOBALCACHE
    if key in GLOBALCACHE.keys():
      return GLOBALCACHE[key]
    return default
