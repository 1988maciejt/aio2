from libs.nlfsr import *
import keras
from tqdm import tqdm
import p_tqdm
import functools


class NlfsrAi:
  
  __slots__ = ("_nlfsrs", "MaxTapsCount", "MaxAndInputs")
  
  def __init__(self, nlfsrs = None, MaxTapsCount=30, MaxAndInputs=8) -> None:
    self.MaxTapsCount = MaxTapsCount
    self.MaxAndInputs = MaxAndInputs
    self._nlfsrs = []
    if nlfsrs is not None:
      self.addNlfsrs(nlfsrs)
    
  def addNlfsrs(self, nlfsrs : list | Nlfsr):
    if type(nlfsrs) is Nlfsr:
      if not (nlfsrs.isSemiLfsr()):
        self._nlfsrs.append(nlfsrs)
    else:
      if len(nlfsrs) > 100:
        cntr = 0
        for i in p_imap(Nlfsr.isSemiLfsr, nlfsrs, desc="Adding NLFSRs"):
          if not i:
            self._nlfsrs.append(nlfsrs[cntr])
          cntr += 1
      else:
        for n in nlfsrs:
          if type(n) is Nlfsr:
            if not n.isSemiLfsr():
              self._nlfsrs.append(n)
          
  def createAISet(self) -> tuple:
    NlfsrList.checkMaximum(self._nlfsrs)
    x = []
    y = []
    cntr = 0
    for xi in p_imap(functools.partial(Nlfsr.toAIArray, MaxTapsCount=self.MaxTapsCount, MaxAndInputs=self.MaxAndInputs), self._nlfsrs, desc="Creating train set"):
      n = self._nlfsrs[cntr]
      x.append(xi)
      y.append([1 if n.isMaximum() else 0])
      cntr += 1
#    for n in tqdm(self._nlfsrs, desc="Creating train set"):
#      x.append(n.toAIArray(self.MaxTapsCount, self.MaxAndInputs))
#      y.append([1 if n.isMaximum() else 0])
    return x, y
  
  def getInputVectorSize(self) -> tuple:
    return self.MaxAndInputs * self.MaxTapsCount + 2
  
  def createAIModel(self) -> keras.Model:
    x, y = self.createAISet()
    model = keras.models.Sequential()
    model.add(keras.layers.Dense(1024, activation="relu", input_shape=(self.getInputVectorSize(),)))
    model.add(keras.layers.Dense(1024, activation="relu"))
    model.add(keras.layers.Dense(128, activation="relu"))
    model.add(keras.layers.Dense(1, activation="sigmoid"))
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    model.fit(x, y, epochs=10, batch_size=128)
    return model