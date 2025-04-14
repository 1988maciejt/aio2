from libs.aio import *
from libs.pandas_table import AioTable
from libs.simple_threading import SimpleThreadInterval
import requests
import json
import time

class DessMonitorConfig:

  __slots__ = ('_querySPDeviceLastData', '_queryDeviceParsEs', "_setPrioritySolar", "_setPrioritySBU")

  def __init__(self, URL_querySPDeviceLastData : str, URL_queryDeviceParsEs : str, URL_SetPrioritySolar : str = None, URL_SetPrioritySBU : str = None):
    self._querySPDeviceLastData = URL_querySPDeviceLastData
    self._queryDeviceParsEs = URL_queryDeviceParsEs
    self._setPrioritySolar = URL_SetPrioritySolar
    self._setPrioritySBU = URL_SetPrioritySBU
  
  def getLastDataUrl(self) -> str:
    return self._querySPDeviceLastData
  
  def getRestDataUrl(self) -> str:
    return self._queryDeviceParsEs
  
  def getSetPrioritySolarUrl(self) -> str:
    return self._setPrioritySolar
  
  def getSetPrioritySBUUrl(self) -> str:
    return self._setPrioritySBU

  

class DessInverter:

  __slots__ = (
    'AcInputFrequency', 'AcInputVoltage', 'AcInputPower', 'AcInputCurrent',
    'AcOutputFrequncy', 'AcOutputVoltage', 'AcOutputPower', 'AcOutputCurrent', 'AcOutputApparentPower', 'AcOutputLoad',
    'PvInputPower', 'PvInputVoltage', 'PvInputCurrent',
    'BatteryVoltage', 'BatteryInputCurrent', 'BatteryInputPower', 'BatteryCapacity',
    'OutputSourcePriority', 'ChargerSourcePriority',
    'TimeOfData', 'WorkingMode',
    '_my_config', 'InverterPowerConsumption', '_updater', 'LastUpdateTimeStamp',
    'DcAcConversionEfficiency', '_priority_automator', '_pv_enough_history', '_priority_automator_last_timestamp',
  )

  def __init__(self, Config : DessMonitorConfig, AutoUpdate : bool = True):
    self._my_config = Config
    self.AcInputFrequency = 0
    self.AcInputVoltage = 0
    self.AcInputPower = 0
    self.AcInputCurrent = 0
    self.AcOutputFrequncy = 0
    self.AcOutputVoltage = 0
    self.AcOutputPower = 0
    self.AcOutputCurrent = 0
    self.AcOutputApparentPower = 0
    self.AcOutputLoad = 0
    self.PvInputPower = 0
    self.PvInputVoltage = 0
    self.PvInputCurrent = 0
    self.BatteryVoltage = 0
    self.BatteryInputCurrent = 0
    self.BatteryInputPower = 0
    self.BatteryCapacity = 0
    self.OutputSourcePriority = ''
    self.ChargerSourcePriority = ''
    self.WorkingMode = ''
    self._priority_automator_last_timestamp = ''
    self.InverterPowerConsumption = 25
    self.DcAcConversionEfficiency = 0.9
    self._updater = SimpleThreadInterval(60, self.update)
    self._priority_automator = SimpleThreadInterval(180, self.priorityAutomatorPoll)
    self.LastUpdateTimeStamp = 0
    self.TimeOfData = None
    self._pv_enough_history = None
    if AutoUpdate:
      self._updater.start()

  def __del__(self):
    self._updater.stop()
    time.sleep(2)
    del self._updater

  def __str__(self):
    Table = AioTable(['Parameter', 'AC Input', 'Pv Input', 'Battery', 'Ac Output', '[Unit]'])
    Table.addRow(['Frequency', self.AcInputFrequency, '', '', self.AcOutputFrequncy, 'Hz'])
    Table.addRow(['Voltage', self.AcInputVoltage, self.PvInputVoltage, self.BatteryVoltage, self.AcOutputVoltage, 'V'])
    Table.addRow(['Current', self.AcInputCurrent, self.PvInputCurrent, self.BatteryInputCurrent, self.AcOutputCurrent, 'A'])
    Table.addRow(['Power', self.AcInputPower, self.PvInputPower, self.BatteryInputPower, self.AcOutputPower, 'W'])
    Table.addRow(['Apparent Power', '', '', '', self.AcOutputApparentPower, 'VA'])
    Table.addRow(['Capacity', '', '', int(self.BatteryCapacity*100), int(self.AcOutputLoad*100), '%'])
    Table.addRow(['Priority', '', '', self.ChargerSourcePriority, self.OutputSourcePriority, ''])
    return f'''Time of data: {self.TimeOfData}, {self.WorkingMode}, PV power is {'NOT ' if not self.isPvEnough() else ''}enough.
{Table.toString()}'''

  def _getJson(self, url):
    try:
      response = requests.get(url)
      if response.status_code == 200:
        data = json.loads(response.text)
        return data
      else:
        return None
    except:
      return None
    
  def setPrioritySolar(self) -> bool:
    Url = self._my_config.getSetPrioritySolarUrl()
    if Url is None:
      Aio.printError('Set Priority Solar URL is not set')
      return False
    try:
      j = self._getJson(Url)
      if j is None:
        return False
      if j["err"] == 0:
        return True
    except:
      return False
    return True
    
  def setPrioritySBU(self) -> bool:
    Url = self._my_config.getSetPrioritySBUUrl()
    if Url is None:
      Aio.printError('Set Priority SBU URL is not set')
      return False
    try:
      j = self._getJson(Url)
      if j is None:
        return False
      if j["err"] == 0:
        return True
    except:
      return False
    return True
  
  def priorityAutomatorPoll(self):
    if self.TimeOfData is None:
      return
    if self._priority_automator_last_timestamp == self.TimeOfData:
      return
    if self._pv_enough_history is None:
      self._pv_enough_history = self.isPvEnough()
    else:
      IsEnough = self.isPvEnough()
      if IsEnough and self._pv_enough_history:
        # should be solar
        if self.OutputSourcePriority != 'Solar':
          if self.setPrioritySolar():
            self.OutputSourcePriority = 'Solar'
      elif not IsEnough and not self._pv_enough_history:
        # should be SBU
        if self.OutputSourcePriority != 'SBU':
          if self.setPrioritySBU():
            self.OutputSourcePriority = 'SBU'
    self._priority_automator_last_timestamp = self.TimeOfData
    
  def update(self) -> bool:
    Json = self._getJson(self._my_config.getLastDataUrl())
    if Json is None:
      return False
    def get_par_val(pars, id, idname = 'id', Round = 1):
      for par in pars:
        if par[idname] == id:
          Res = par['val']
          try:
            Res = int(Res)
          except:
            try:
              Res = float(Res)
              if Round:
                Res = round(Res, 1)
            except:
              pass
          return Res
      return 0
    TimeOfData = Json['dat']['gts']
    if TimeOfData == self.TimeOfData:
      return True
    gdPars = Json['dat']['pars']['gd_']
    syPars = Json['dat']['pars']['sy_']
    pvPars = Json['dat']['pars']['pv_']
    btPars = Json['dat']['pars']['bt_']
    bcPars = Json['dat']['pars']['bc_']
    Json = self._getJson(self._my_config.getRestDataUrl())
    if Json is None:
      return False
    restPars = Json['dat']['parameter']
    self.WorkingMode = get_par_val(syPars, 'sy_status')
    self.AcInputFrequency = get_par_val(gdPars, 'gd_ac_input_frequency')
    self.AcInputVoltage = get_par_val(gdPars, 'gd_ac_input_voltage')
    self.AcOutputFrequncy = get_par_val(bcPars, 'bc_output_frequency')
    self.AcOutputVoltage = get_par_val(bcPars, 'bc_output_voltage')
    self.AcOutputPower = int(get_par_val(restPars, 'output_power', 'par', 0)*1000)
    self.AcOutputCurrent = round(self.AcOutputPower / self.AcOutputVoltage,1) if self.AcOutputVoltage != 0 else 0
    self.AcOutputApparentPower = get_par_val(bcPars, 'bc_output_apparent_power')
    self.AcOutputLoad = get_par_val(bcPars, 'bc_battery_capacity') / 100.0
    self.PvInputPower = get_par_val(pvPars, 'pv_output_power')
    self.PvInputVoltage = get_par_val(pvPars, 'pv_input_voltage')
    self.PvInputCurrent = round(self.PvInputPower / self.PvInputVoltage,1) if self.PvInputVoltage != 0 else 0
    self.BatteryVoltage = get_par_val(btPars, 'bt_battery_voltage')
    Char = get_par_val(btPars, 'bt_battery_charging_current')
    Dis = get_par_val(btPars, 'bt_battery_discharge_current')
    self.BatteryInputCurrent = Dis - Char
    self.BatteryInputPower = round(self.BatteryVoltage * self.BatteryInputCurrent, 1)
    self.BatteryCapacity = get_par_val(btPars, 'bt_battery_capacity') / 100
    self.OutputSourcePriority = get_par_val(bcPars, 'bc_output_source_priority')
    self.ChargerSourcePriority = get_par_val(btPars, 'bt_charger_source_priority')
    if self.BatteryInputPower < 0:
      BattPower = self.BatteryInputPower / self.DcAcConversionEfficiency
    else:
      BattPower = self.BatteryInputPower * self.DcAcConversionEfficiency
    if "Invert" in self.WorkingMode:
      self.AcInputCurrent = 0
    else:
      self.AcInputPower = int(self.AcOutputPower - BattPower - self.PvInputPower + self.InverterPowerConsumption)
    self.AcInputCurrent = round(self.AcInputPower / self.AcInputVoltage,1) if self.AcInputVoltage != 0 else 0
    self.TimeOfData = TimeOfData
    self.LastUpdateTimeStamp = time.time()
    return True

  def AutoUpdate(self, Enable : bool):
    if Enable:
      self._updater.start()
    else:
      self._updater.stop()

  def automateOutputSourcePriority(self, Enable : bool):
    if Enable:
      self._priority_automator.start()
    else:
      self._priority_automator.stop()

  def isPvEnough(self) -> bool:
    if self.BatteryInputPower > 0:
      return False
    if self.PvInputPower >= (self.AcOutputPower - self.BatteryInputPower) / self.DcAcConversionEfficiency:
      return True
    return False
  
  def isModeInverter(self) -> bool:
    return 'Invert' in self.WorkingMode

  def isModeLine(self) -> bool:
    return 'Line' in self.WorkingMode