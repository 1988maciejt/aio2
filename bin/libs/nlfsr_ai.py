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
import time
from libs.stats import *

class NlfsrAi:
  
  __slots__ = ("_x_train", "_y_train", "_x_ver", "_y_ver", "MaxTapsCount", "MaxAndInputs", "SequenceBased", "model", "_filename", "_empty", "_base_on_period")
  
  def __init__(self, nlfsrs = None, MaxTapsCount=30, MaxAndInputs=8, SequenceBased=False, FileName : str = None, BaseOnPeriod = False) -> None:
    self.MaxTapsCount = MaxTapsCount
    self.MaxAndInputs = MaxAndInputs
    self.SequenceBased = SequenceBased
    self._filename = FileName
    self._x_train = []
    self._y_train = []
    self._x_ver = []
    self._y_ver = []
    self._empty = True
    self._base_on_period = BaseOnPeriod
    if self._filename is not None:
      if not self.load(self._filename, Silent=False):
        self._createModel()
    else:
      self._createModel()
    if nlfsrs is not None:
      self.addNlfsrs(nlfsrs)
    
    
  def _createModel(self):
    self.model = keras.models.Sequential()
    if self._base_on_period:
      self.model.add(keras.layers.Dense(2048, activation="sigmoid", input_shape=(self.getInputVectorSize(),)))
      self.model.add(keras.layers.Dense(2048, activation="sigmoid"))
      self.model.add(keras.layers.Dense(1024, activation="sigmoid"))
      self.model.add(keras.layers.Dense(1, activation="sigmoid"))
      self.model.compile(loss=keras.losses.MeanAbsoluteError(), optimizer=keras.optimizers.RMSprop(), metrics=['accuracy'])
    else:
      self.model.add(keras.layers.Dense(2048, activation="relu", input_shape=(self.getInputVectorSize(),)))
      self.model.add(keras.layers.Dense(2048, activation="relu"))
      self.model.add(keras.layers.Dense(1024, activation="relu"))
      self.model.add(keras.layers.Dense(1, activation=keras.activations.sigmoid))
      self.model.compile(loss=keras.losses.BinaryCrossentropy(), optimizer=keras.optimizers.Nadam(), metrics=['accuracy'])
    
  def addNlfsrs(self, nlfsrs : list | Nlfsr):
    if type(nlfsrs) is Nlfsr:
      self._x_train.append(nlfsrs.toAIArray(self.MaxTapsCount, self.MaxAndInputs, self.SequenceBased))
      self._y_train.append([nlfsrs.getPeriod() / ((1 << nlfsrs.getSize()) -1)])        
    else:
      for xi in p_uimap(functools.partial(NlfsrList.toAIArray, MaxTapsCount=self.MaxTapsCount, MaxAndInputs=self.MaxAndInputs, SequenceBased=self.SequenceBased, ReturnAlsoAccepted=1, BaseOnPeriod=self._base_on_period), List.splitIntoSublists(nlfsrs, 128), desc="Adding to train set (x 128)"):
        self._x_train += xi[0]
        self._y_train += xi[1]
    
  def addNlfsrsToVerify(self, nlfsrs : list | Nlfsr):
    if type(nlfsrs) is Nlfsr:
      self._x_ver.append(nlfsrs.toAIArray(self.MaxTapsCount, self.MaxAndInputs, self.SequenceBased))
      self._y_ver.append([nlfsrs.getPeriod() / ((1 << nlfsrs.getSize()) -1)])        
    else:
      for xi in p_uimap(functools.partial(NlfsrList.toAIArray, MaxTapsCount=self.MaxTapsCount, MaxAndInputs=self.MaxAndInputs, SequenceBased=self.SequenceBased, ReturnAlsoAccepted=1, BaseOnPeriod=self._base_on_period), List.splitIntoSublists(nlfsrs, 128), desc="Adding to train set (x 128)"):
        self._x_ver += xi[0]
        self._y_ver += xi[1]
  
  def getInputVectorSize(self) -> tuple:
    return self.MaxAndInputs * self.MaxTapsCount + 2
  
  def fit(self, Epochs=10):
    if len(self._x_ver) > 0:
      self.model.fit(self._x_train, self._y_train, epochs=Epochs, batch_size=128, use_multiprocessing=1, validation_data=(self._x_ver, self._y_ver))
    else:
      self.model.fit(self._x_train, self._y_train, epochs=Epochs, batch_size=128, use_multiprocessing=1)
    self._empty = False
    
  def save(self, FileName : str = None):
    if FileName is None:
      FileName = self._filename
    if FileName is None:
      Aio.printError("Filename cannot be 'None'")
    self.model.save(f"{FileName}.keras")
    mlist = [self._x_train, self._y_train, self._x_ver, self._y_ver, self.MaxTapsCount, self.MaxAndInputs, self.SequenceBased, self._empty, self._base_on_period]
    File.writeObject(f"{FileName}.nlfsrai", mlist, True)
    
  def load(self, FileName : str, Silent = False) -> bool:
    try:
      model = keras.models.load_model(f"{FileName}.keras")
    except:
      if not Silent:
        Aio.printError(f"'{FileName}.keras' does not exist.")
      return False
    try:
      mlist = File.readObject(f"{FileName}.nlfsrai", True)
    except:
      if not Silent:
        Aio.printError(f"'{FileName}.nlfsrai' does not exist.")
      return False
    if len(mlist) < 8:
      if not Silent:
        Aio.printError(f"'{FileName}.nlfsrai' is incorrect.")
      return False
    self._x_train = mlist[0]
    self._y_train = mlist[1]
    self._x_ver = mlist[2]
    self._y_ver = mlist[3]
    self.MaxTapsCount = mlist[4]
    self.MaxAndInputs = mlist[5]
    self.SequenceBased = mlist[6]
    self._empty = mlist[7]
    if len(mlist) > 8:
      self._base_on_period = mlist[8]
    else:
      self._base_on_period = False
    self.model = model
    return True

  def analyse(self, Size : int, MinTapsCount = 3, MaxTapsCount = 10, MinAndInputsCount = 2, MaxAndInputCount = 3, MinNonlinearTapsRatio = 0.3, MaxNonlinearTapsRatio = 0.6, HybridAllowed = False, UniformTapsDistribution = False, HardcodedInverters = False, OnlyMaximumPeriod = False, OnlyPrimeNonMaximumPeriods = True, AllowMaximumPeriods = True, MinimumPeriodRatio = 0.95) -> list:
    CandidateSet = 8192
    for _ in range(Size-18):
      CandidateSet //= 2
    if CandidateSet < 128:
      CandidateSet = 128
    ChunkSize = CandidateSet // 8
    Candidates = Nlfsr.listRandomNlrgCandidates(Size, CandidateSet, True, MinTapsCount, MaxTapsCount, MinAndInputsCount, MaxAndInputCount, MinNonlinearTapsRatio, MaxNonlinearTapsRatio, HybridAllowed, UniformTapsDistribution, HardcodedInverters)
    x_data = []
    for xi in p_uimap(functools.partial(NlfsrList.toAIArray, MaxTapsCount=self.MaxTapsCount, MaxAndInputs=self.MaxAndInputs, SequenceBased=self.SequenceBased, ReturnAlsoAccepted=False), List.splitIntoSublists(Candidates, 128), desc="Creating data for AI (x 128)"):
      x_data += xi
    y_data = self.model.predict(x_data)
    for i in range(len(Candidates)):
      Candidates[i]._prediction = y_data[i][0]
    Candidates.sort(key=lambda x: x._prediction, reverse=1)
    Candidates = NlfsrList.filterPeriod(NlfsrList.checkPeriod(Candidates), OnlyMaximumPeriod, AllowMaximumPeriods, OnlyPrimeNonMaximumPeriods, MinimumPeriodRatio=MinimumPeriodRatio, ReturnAll=1)
    PlotData = []
    for subl in Generators().subLists(Candidates, ChunkSize):
      Sum = 0
      for nlfsr in subl:
        if nlfsr.Accepted:
          Sum += 1
      PlotData.append(Sum)
    Plot(PlotData, PlotTypes.Bar, Height=12, Width=100).print()
    
  def searchAndAdd(self, Size : int, n : int, MaxSearchingTimeMin = 300, MinTapsCount = 3, MaxTapsCount = 10, MinAndInputsCount = 2, MaxAndInputCount = 3, MinNonlinearTapsRatio = 0.3, MaxNonlinearTapsRatio = 0.6, HybridAllowed = False, UniformTapsDistribution = False, HardcodedInverters = False, OnlyMaximumPeriod = False, OnlyPrimeNonMaximumPeriods = True, AllowMaximumPeriods = True, MinimumPeriodRatio = 0.95, AutoFit = False, GenerateUsingAI = True, ShowPredictionHistograms = False) -> list:
    if self._empty or (not GenerateUsingAI):
      All = Nlfsr.listRandomNlrgs(Size, MinTapsCount, MaxTapsCount, MinAndInputsCount, MaxAndInputCount, MinNonlinearTapsRatio, MaxNonlinearTapsRatio, HybridAllowed, UniformTapsDistribution, HardcodedInverters, OnlyMaximumPeriod, OnlyPrimeNonMaximumPeriods, AllowMaximumPeriods, MinimumPeriodRatio, n, 0, MaxSearchingTimeMin, 1)
      Result = []
      for nlfsr in All:
        if nlfsr.Accepted:
          Result.append(nlfsr.copy())
      self.addNlfsrs(All)
    else:
      ChunkSize = 1024
      for _ in range(Size-14):
        ChunkSize //= 2
      if ChunkSize < 32:
        ChunkSize = 32
      CandidateSet = ChunkSize * 4
      Result = []
      T0 = time.time()
      FitCntr = 0
      while 1:
        Candidates = Nlfsr.listRandomNlrgCandidates(Size, CandidateSet, True, MinTapsCount, MaxTapsCount, MinAndInputsCount, MaxAndInputCount, MinNonlinearTapsRatio, MaxNonlinearTapsRatio, HybridAllowed, UniformTapsDistribution, HardcodedInverters)
        x_data = []
        for xi in p_uimap(functools.partial(NlfsrList.toAIArray, MaxTapsCount=self.MaxTapsCount, MaxAndInputs=self.MaxAndInputs, SequenceBased=self.SequenceBased, ReturnAlsoAccepted=False), List.splitIntoSublists(Candidates, 128), desc="Creating data for AI (x 128)"):
          x_data += xi
        y_data = self.model.predict(x_data)
        if ShowPredictionHistograms:
          H = Histogram(y_data, BarCount=10)
          Plot(H.getPlotData(), PlotTypes.Bar, Width=120, Height=15).print()
        for i in range(len(Candidates)):
          Candidates[i]._prediction = y_data[i][0]
        Candidates.sort(key=lambda x: x._prediction, reverse=1)
        Candidates = Candidates[:ChunkSize]
        Candidates = NlfsrList.filterPeriod(NlfsrList.checkPeriod(Candidates), OnlyMaximumPeriod, AllowMaximumPeriods, OnlyPrimeNonMaximumPeriods, MinimumPeriodRatio=MinimumPeriodRatio, ReturnAll=1)
        for nlfsr in Candidates:
          if nlfsr.Accepted:
            Result.append(nlfsr.copy())
        self.addNlfsrs(Candidates)
        STime = round((time.time() - T0) / 60, 2)
        print(f"// Found so far: {len(Result)}, searching time: {STime} min")
        if len(Result) >= n > 0:
          break      
        if STime >= MaxSearchingTimeMin > 0:
          break
        if AutoFit:
          FitCntr += 1
          if FitCntr == 10:
            self.fit(1)
            FitCntr = 0
    if AutoFit:
      self.fit(10)
    if len(Result) > n > 0:
      Result = Result[:n]  
    return Result
        