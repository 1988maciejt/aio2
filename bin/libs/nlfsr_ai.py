try:
  x = __import__("keras")
except:      
  print(f"INSTALLING MISSING 'tensorflow' MODULE:")
  os.system(f"python3 -m pip install --upgrade tensorflow")

from libs.nlfsr import *
import keras
from tqdm import tqdm
import p_tqdm
import functools
from libs.files import *

class NlfsrAi:
  
  __slots__ = ("_x_train", "_y_train", "_x_ver", "_y_ver", "MaxTapsCount", "MaxAndInputs", "SequenceBased", "model")
  
  def __init__(self, nlfsrs = None, MaxTapsCount=30, MaxAndInputs=8, SequenceBased=False) -> None:
    self.MaxTapsCount = MaxTapsCount
    self.MaxAndInputs = MaxAndInputs
    self.SequenceBased = SequenceBased
    self._x_train = []
    self._y_train = []
    self._x_ver = []
    self._y_ver = []
    if nlfsrs is not None:
      self.addNlfsrs(nlfsrs)
    self.model = keras.models.Sequential()
    self.model.add(keras.layers.Dense(2048, activation="relu", input_shape=(self.getInputVectorSize(),)))
    self.model.add(keras.layers.Dense(2048, activation="relu"))
    self.model.add(keras.layers.Dense(1024, activation="relu"))
    self.model.add(keras.layers.Dense(1, activation="sigmoid"))
    self.model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    
  def addNlfsrs(self, nlfsrs : list | Nlfsr):
    if type(nlfsrs) is Nlfsr:
      self._x_train.append(nlfsrs.toAIArray(self.MaxTapsCount, self.MaxAndInputs, self.SequenceBased))
      self._y_train.append([nlfsrs.Accepted])        
    else:
      cntr = 0
      for xi in p_imap(functools.partial(Nlfsr.toAIArray, MaxTapsCount=self.MaxTapsCount, MaxAndInputs=self.MaxAndInputs, SequenceBased=self.SequenceBased), nlfsrs, desc="Adding to train set"):
        n = self._nlfsrs[cntr]
        self._x_train.append(xi)
        self._y_train.append([n.Accepted])
        cntr += 1
    
  def addNlfsrsToVerify(self, nlfsrs : list | Nlfsr):
    if type(nlfsrs) is Nlfsr:
      self._x_ver.append(nlfsrs.toAIArray(self.MaxTapsCount, self.MaxAndInputs, self.SequenceBased))
      self._y_ver.append([nlfsrs.Accepted])        
    else:
      cntr = 0
      for xi in p_imap(functools.partial(Nlfsr.toAIArray, MaxTapsCount=self.MaxTapsCount, MaxAndInputs=self.MaxAndInputs, SequenceBased=self.SequenceBased), nlfsrs, desc="Adding to train set"):
        n = self._nlfsrs[cntr]
        self._x_ver.append(xi)
        self._y_ver.append([n.Accepted])
        cntr += 1
  
  def getInputVectorSize(self) -> tuple:
    return self.MaxAndInputs * self.MaxTapsCount + 2
  
  def fit(self, Epochs=10):
    if len(self._x_ver) > 0:
      self.model.fit(self._x_train, self._y_train, epochs=Epochs, batch_size=128, use_multiprocessing=1, validation_data=(self._x_ver, self._y_ver))
    else:
      self.model.fit(self._x_train, self._y_train, epochs=Epochs, batch_size=128, use_multiprocessing=1)
      
  def save(self, FileName : str):
    self.model.save(f"{FileName}.keras")
    mlist = [self._x_train, self._y_train, self._x_ver, self._y_ver, self.MaxTapsCount, self.MaxAndInputs, self.SequenceBased]
    File.writeObject(f"{FileName}.nlfsrai", mlist, True)
    
  def load(self, FileName : str, SIlent = False) -> bool:
    try:
      model = keras.models.load_model(f"{FileName}.keras")
    except:
      Aio.printError(f"'{FileName}.keras' does not exist.")
      return False
    try:
      mlist = File.readObject(f"{FileName}.nlfsrai", True)
    except:
      Aio.printError(f"'{FileName}.nlfsrai' does not exist.")
      return False
    if len(mlist) != 7:
      Aio.printError(f"'{FileName}.nlfsrai' is incorrect.")
      return False
    self._x_train = mlist[0]
    self._y_train = mlist[1]
    self._x_ver = mlist[2]
    self._y_ver = mlist[3]
    self.MaxTapsCount = mlist[4]
    self.MaxAndInputs = mlist[5]
    self.SequenceBased = mlist[6]
    self.model = model
    return True