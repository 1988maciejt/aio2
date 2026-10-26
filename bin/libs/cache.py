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



import functools
import multiprocess

class SafeProcessCache:
    def __init__(self):
        # Używamy surowego Locka z managera, ale dane trzymamy w bezpieczniejszej strukturze 
        # lub korzystamy z zabezpieczonego dostępu do współdzielonego słownika
        self._manager = multiprocess.Manager()
        self._lock = self._manager.Lock()
        # Zamiast manager.dict() używamy synchronizowanego słownika przez Lock
        self._cache = {} 
        self._hits = 0
        self._misses = 0

    def lru_cache(self, maxsize=1024):
        # Lokalne referencje
        cache_dict = self._cache
        lock = self._lock

        def decorator(func):
            func_name = func.__name__

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                nonlocal self # Dostęp do liczników
                cache_key = (func_name, args, tuple(sorted(kwargs.items())) if kwargs else ())

                # Bezpieczny odczyt/zapis przez blokadę
                with lock:
                    if cache_key in cache_dict:
                        self._hits += 1
                        return cache_dict[cache_key]
                    self._misses += 1

                result = func(*args, **kwargs)

                with lock:
                    if cache_key not in cache_dict:
                        if len(cache_dict) >= maxsize:
                            try:
                                # Proste wyrzucenie pierwszego elementu (FIFO/LRU przybliżone)
                                first_key = next(iter(cache_dict))
                                del cache_dict[first_key]
                            except (RuntimeError, StopIteration):
                                pass
                        cache_dict[cache_key] = result

                return result

            def cache_info():
                with lock:
                    return f"CacheInfo(hits={self._hits}, misses={self._misses}, maxsize={maxsize}, currsize={len(cache_dict)})"

            def cache_clear():
                with lock:
                    cache_dict.clear()
                    self._hits = 0
                    self._misses = 0

            wrapper.cache_info = cache_info
            wrapper.cache_clear = cache_clear
            return wrapper
        return decorator


multiprocess_cache = SafeProcessCache()