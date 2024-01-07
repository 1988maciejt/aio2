from libs.aio import *
from math import *
import re



class MusicTools:
  
  _K = 1.0594630943592953
  _FREQS = None

  @staticmethod
  def _getK() -> float:
    return MusicTools._K

  @staticmethod
  def _getFreqs() -> list:
    if  MusicTools._FREQS is None:
      f = 16.351598
      l = [f]
      k = MusicTools._K
      for i in range(12 * 11):
        f *= k
        l.append(round(f, 3))
      MusicTools._FREQS = l
    return MusicTools._FREQS.copy()
  
  @staticmethod
  def _findToneIdx(Freq : float) -> int:
    bestD = 1000000000
    bestI = 0
    Freqs = MusicTools._getFreqs()
    for i in range(len(Freqs)):
      D = abs(Freq - Freqs[i])
      if D < bestD:
        bestD, bestI = D, i
      if D > bestD:
        break
    return bestI
  
  @staticmethod
  def _idxToTone(Idx : int) -> tuple:
    return Idx//12, Idx%12
  
  @staticmethod
  def _toneToIdx(Octave : int, Note : int) -> int:
    return Octave * 12 + Note
  
  @staticmethod
  def _toneToStr(Octave : int, Note : int, Major : bool = True, IncludeOctave : bool = True) -> str:
    if Major:
      Notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'H']
    else:
      Notes = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'B', 'H']
    if IncludeOctave and Octave is not None:
      return f"{Notes[Note]}{Octave}"
    return Notes[Note]
  
  @staticmethod
  def _idxToStr(Idx : int, Major : bool = True, IncludeOctave : bool = True) -> str:
    return MusicTools._toneToStr(*MusicTools._idxToTone(Idx), Major=Major, IncludeOctave=IncludeOctave)
  
  @staticmethod
  def _strToTone(Txt : str) -> tuple:
    Octave = None
    Tone = None
    Major = True
    R = re.search(r'([a-hA-H]{1}[bB#]?)\s*([0-9]?[0-9]?)', Txt)
    if R:
      Tones = {
        'C':0, 'C#':1, 'D':2, 'D#':3, 'E':4, 'F':5, 'F#':6, 'G':7, 'G#':8, 'A':9, 'A#':10, 'H':11,
                'DB':1,       'EB':3,               'GB':6,        'AB':8,        'B':10, 'HB':10,
                                              'FH':5,                                             'H#':0,
        'CB':11,                      'FB':4
      }
      Note = str(R.group(1)).upper()
      if "B" in Note:
        Major = False
      Tone = Tones.get(Note, None)
      try:
        Octave = int(R.group(2))
      except: pass
    return Octave, Tone, Major
  
  @staticmethod
  def _toneToFreq(Octave : int, Note : int) -> float:
    Idx = MusicTools._toneToIdx(Octave, Note)
    try:
      return MusicTools._getFreqs()[Idx]
    except:
      return None
    
  @staticmethod
  def centsDiff(Freq1 : float, Freq2 : float) -> float:
    return 1200 * log2(Freq2 / Freq1)

class MusicTone:
  pass
class MusicTone:
  
  __slots__ = ('_octave', '_tone', '_major')
  
  def __init__(self, Octave : int, Tone : int, Major : bool = True) -> None:
    self._octave = Octave
    self._tone = Tone
    self._major = Major
  
  def __hash__(self) -> int:
    return hash(tuple([self._octave, self._tone]))
    
  def __repr__(self) -> str:
    return f"MusicTone({self._octave}, {self._tone}, {self._major})"
  
  def __str__(self) -> str:
    return MusicTools._toneToStr(self._octave, self._tone, self._major, self._octave > 0)
  
  def __sub__(self, other) -> int:
    if type(other) is MusicTone:
      return MusicTools._toneToIdx(self._octave, self._tone) - MusicTools._toneToIdx(other._octave, other._tone)
    try:
      N = int(other)
    except:
      Aio.printError("Second operand must be a number or MusicTone object")
      return None
    Idx = MusicTools._toneToIdx(self._octave, self._tone) - N
    return MusicTone(*MusicTools._idxToTone(Idx), self._major)
  
  def __add__(self, other) -> int:
    try:
      N = int(other)
    except:
      Aio.printError("Second operand must be a number")
      return None
    Idx = MusicTools._toneToIdx(self._octave, self._tone) + N
    return MusicTone(*MusicTools._idxToTone(Idx), self._major)
  
  def getFreq(self) -> float:
    return MusicTools._toneToFreq(self._octave, self._tone)
  
  def centsDiff(self, Freq : float) -> float:
    return MusicTools.centsDiff(self.getFreq(), Freq)
    
  @staticmethod
  def fromString(Txt : str) -> MusicTone:
    O, T, M = MusicTools._strToTone(Txt)
    if T is None:
      return None
    if O is None:
      O = 0
    return MusicTone(O, T, M)
  
  @staticmethod
  def fromFreq(Freq : float, Major : bool = True) -> MusicTone:
    return MusicTone(*MusicTools._idxToTone(MusicTools._findToneIdx(Freq)), Major=Major)
  
  
  