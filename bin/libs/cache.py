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
