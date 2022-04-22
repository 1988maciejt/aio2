from libs.files import *
import shelve

GLOBALCACHE = {}

class Cache:
  def store(key, value) -> None:
    global GLOBALCACHE
    GLOBALCACHE[key] = value
  def recall(key, default = None):
    global GLOBALCACHE
    if key in GLOBALCACHE.keys():
      return GLOBALCACHE[key]
    return default

class PersistentCache:
  def store(key, value) -> None:
    db = shelve.open(getAioPath() + "cache")
    db[str(key)] = value
    db.close()
  def recall(key, default = None):
    db = shelve.open(getAioPath() + "cache")
    sk = str(key)
    if sk in db:
      return db[sk]
    db.close()
    return default