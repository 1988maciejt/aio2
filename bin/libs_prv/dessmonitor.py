from libs.aio import *
from libs.pandas_table import AioTable
from libs.simple_threading import SimpleThreadInterval
import requests
import json
import time
import hashlib

class DessMonitorConfig:

  __slots__ = (
    'UserName', 'PasswordHash', 'Source', 'Language',
    'SN', 'Protocol', 'DeviceAddress', 'PN',
    '_secret', '_token', '_company_key', '_authenticated',
    '_AuthThread', 'NextloginTime'
  )

  def __init__(self, UserName : str, Password : str, SN : str = None):
    self.UserName = UserName
    self.PasswordHash = self.getSha1(Password)
    self.Source = "1"
    self.SN = SN
    self.Protocol = ""
    self.DeviceAddress = ""
    self.PN = ""
    self.Language = "en_US"
    self._secret = None
    self._token = None
    self._company_key = "bnrl_frRFjEz8Mkn"
    self._authenticated = False
    self.NextloginTime = 0
    self._AuthThread = SimpleThreadInterval(10, self._autoLogin)
    self._AuthThread.start()

  def __bool__(self) -> bool:
    return self._authenticated
  
  def isAuthenticated(self) -> bool:
    return self._authenticated

  def getJson(self, url):
    try:
      response = requests.get(url)
      if response.status_code == 200:
        data = json.loads(response.text)
        return data
      else:
        return None
    except:
      return None
  
  def getSalt(self) -> str:
    return str(int(time.time() * 1000))
  
  def getSha1(self, Text : str) -> str:
    return hashlib.sha1(Text.encode('utf-8')).hexdigest()
  
  def _getDevices(self):
    Url = self.getQueryDevicesUrl()
    Json = self.getJson(Url)
    if Json is not None:
      try:
        Devices = Json["dat"]["device"]
        return Devices
      except:
        pass
    return None

  def _autoSetDevice(self) -> bool:
    for _ in range(3):
      Devices = self._getDevices()
      if Devices is not None:
        if self.SN is None:
          if len(Devices) == 1:
            self.SN = Devices[0]["sn"]
            self.PN = Devices[0]["pn"]
            self.Protocol = str(Devices[0]["devcode"])
            self.DeviceAddress = str(Devices[0]["devaddr"])
            return True
          else:
            Aio.printError("More than one device. Please set the SN in constructor call.")
            return False
        else:
          SNs = []
          for Device in Devices:
            SNs.append(Device["sn"])
            if Device["sn"] == self.SN:
              self.PN = Device["pn"]
              self.Protocol = Device["devcode"]
              self.DeviceAddress = Device["devaddr"]
              return True
          Aio.printError(f"There is no device having SN = {self.SN}. Available devices: {','.join(SNs)}.")
          return False
    return False      

  def _autoLogin(self):
    if self._authenticated:
      if time.time() < self.NextloginTime:
        return
    for _ in range(3):
      Url = self.getLoginUrl()
      Json = self.getJson(Url)
      if Json is not None:
        try:
          Secret = Json["dat"]["secret"]
          Token = Json["dat"]["token"]
          Expire = int(Json["dat"]["expire"])
          self._secret = Secret
          self._token = Token
          self.NextloginTime = time.time() + (Expire // 2)
          if self._autoSetDevice():
            self._authenticated = True
          else:
            Aio.printError("Failed to set device. AutoLogin disabled. Set the correct SN.")
            self._authenticated = False
            self._AuthThread.stop()
          return
        except:
          pass
    if time.time() > self.NextloginTime:
      self._authenticated = False

  def getLoginUrl(self):
    Salt = self.getSalt()
    HashingString = Salt + self.PasswordHash + "&action=authSource&usr=" + self.UserName + "&source=" + self.Source + "&company-key=" + self._company_key
    Sign = self.getSha1(HashingString)
    Url = "https://web.dessmonitor.com/public/?sign=" + Sign + "&salt=" + Salt + "&action=authSource&usr=" + self.UserName + "&source=" + self.Source + "&company-key=" + self._company_key
    return Url
  
  def getQueryUrl(self, Params : dict, Force : bool = False) -> str:
    if not self._authenticated and not Force:
      return None
    Salt = self.getSalt()
    HashingString = Salt + self._secret + self._token
    Query = ""
    for key, val in Params.items():
      Query +=  "&" + key + "=" + val  
    HashingString += Query
    Sign = self.getSha1(HashingString)
    Url = "https://web.dessmonitor.com/public/?sign=" + Sign + "&salt=" + Salt + "&token=" + self._token + Query
    return Url 
  
  def getQueryDevicesUrl(self) -> str:
    Params = {
      'action': 'webQueryDeviceEs',
      'source': self.Source,
      'devtype': "2304",
      'page': "0",
      'pagesize': "15"
    }
    return self.getQueryUrl(Params, Force=1)
  
  def getLastDataUrl(self) -> str:
    Params = {
      'action': 'querySPDeviceLastData',
      'source': self.Source,
      'devcode': self.Protocol,
      'pn': self.PN,
      'devaddr': self.DeviceAddress,
      'sn': self.SN,
      'i18n': self.Language
    }
    return self.getQueryUrl(Params)
  
  def getRestDataUrl(self) -> str:
    Params = {
      'action': 'queryDeviceParsEs',
      'source': self.Source,
      'devcode': self.Protocol,
      'pn': self.PN,
      'devaddr': self.DeviceAddress,
      'sn': self.SN,
      'i18n': self.Language
    }
    return self.getQueryUrl(Params)
  
  def getSetParamUrl(self, ParamId : str, ParamValue : str) -> str:
    Params = {
      'action': 'ctrlDevice',
      'source': self.Source,
      'pn': self.PN,
      'sn': self.SN,
      'devcode': self.Protocol,
      'devaddr': self.DeviceAddress,
      'id': ParamId,
      'val': ParamValue,
      'i18n': self.Language
    }
    return self.getQueryUrl(Params)
  
  def getSetPrioritySolarUrl(self) -> str:
    return self.getSetParamUrl("los_output_source_priority", "1")
  
  def getSetPrioritySBUUrl(self) -> str:
    return self.getSetParamUrl("los_output_source_priority", "2")

  

class DessInverter:

  __slots__ = (
    'AcInputFrequency', 'AcInputVoltage', 'AcInputPower', 'AcInputCurrent',
    'AcOutputFrequncy', 'AcOutputVoltage', 'AcOutputPower', 'AcOutputCurrent', 'AcOutputApparentPower', 'AcOutputLoad',
    'PvInputPower', 'PvInputVoltage', 'PvInputCurrent',
    'BatteryVoltage', 'BatteryInputCurrent', 'BatteryInputPower', 'BatteryCapacity',
    'OutputSourcePriority', 'ChargerSourcePriority',
    'TimeOfData', 'WorkingMode',
    '_my_config', 'InverterPowerConsumption', '_updater', 'LastUpdateTimeStamp',
    'DcAcConversionEfficiency', '_priority_automator', '_priority_automator_last_timestamp',
    'BatteryBulkChargingVoltage', 'BatteryFloatingChargingVoltage', 'BatteryTotalChargingCurrent', 'BatteryStatus' 
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
    self.BatteryBulkChargingVoltage = 0
    self.BatteryFloatingChargingVoltage = 0
    self.BatteryTotalChargingCurrent = 0
    self.BatteryStatus = ''
    self._priority_automator_last_timestamp = ''
    self.InverterPowerConsumption = 25
    self.DcAcConversionEfficiency = 0.9
    self._updater = SimpleThreadInterval(20, self.update)
    self._priority_automator = SimpleThreadInterval(10, self.priorityAutomatorPoll)
    self.LastUpdateTimeStamp = 0
    self.TimeOfData = None
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
    Table.addRow(['Bulk/Float Char. Volt.', '', '', f'{self.BatteryBulkChargingVoltage} / {self.BatteryFloatingChargingVoltage}', '', 'V'])
    Table.addRow(['Total Char. Curr.', '', '', self.BatteryTotalChargingCurrent, '', 'A'])
    Table.addRow(['Priority', '', '', self.ChargerSourcePriority, self.OutputSourcePriority, ''])
    return f'''Time of data: {self.TimeOfData}, {self.WorkingMode}, {self.BatteryStatus}, PV power is {'NOT ' if not self.isPvEnough() else ''}enough.
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
    if not self._my_config or self.TimeOfData is None:
      return
    if self._priority_automator_last_timestamp == self.TimeOfData:
      return
    else:
      IsEnough = self.isPvEnough()
      if IsEnough:
        # should be solar
        if self.OutputSourcePriority != 'Solar':
          print("Trying to set solar priority")
          if self.setPrioritySolar():
            print("Set solar priority")
            self.OutputSourcePriority = 'Solar'
      else:
        # should be SBU
        if self.OutputSourcePriority != 'SBU':
          print("Trying to set SBU priority")
          if self.setPrioritySBU():
            print("Set SBU priority")
            self.OutputSourcePriority = 'SBU'
    self._priority_automator_last_timestamp = self.TimeOfData
    
  def update(self) -> bool:
    if not self._my_config:
      return False
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
    try:
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
      self.BatteryBulkChargingVoltage = get_par_val(btPars, 'bt_vulk_charging_voltage')
      self.BatteryFloatingChargingVoltage = get_par_val(btPars, 'bt_floating_charging_voltage')
      self.BatteryTotalChargingCurrent = get_par_val(btPars, 'bt_total_charge_current')
      self.BatteryStatus = get_par_val(btPars, 'bt_battery_status')
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
        self.AcInputPower = 0
      else:
        self.AcInputPower = int(self.AcOutputPower - BattPower - self.PvInputPower + self.InverterPowerConsumption)
      self.AcInputCurrent = round(self.AcInputPower / self.AcInputVoltage,1) if self.AcInputVoltage != 0 else 0
      self.TimeOfData = TimeOfData
      self.LastUpdateTimeStamp = time.time()
      return True
    except:
      return False

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
    if self.isModeInverter():
      if self.BatteryBulkChargingVoltage <= self.BatteryVoltage:
        return True
      if self.BatteryFloatingChargingVoltage == self.BatteryVoltage and self.BatteryInputCurrent == 0:
        if self.PvInputPower >= (self.AcOutputPower) / self.DcAcConversionEfficiency:
          return True      
      else:
        MPPVoltage = (self.BatteryBulkChargingVoltage + self.BatteryFloatingChargingVoltage) / 2
        EstimatedChargingPowerMax = self.BatteryTotalChargingCurrent * MPPVoltage
        if self.PvInputPower >= (self.AcOutputPower + EstimatedChargingPowerMax) / self.DcAcConversionEfficiency:
          return True
    else:
      if self.PvInputPower >= (self.AcOutputPower - self.BatteryInputPower) / self.DcAcConversionEfficiency:
        return True
    return False
  
  def isModeInverter(self) -> bool:
    return 'Invert' in self.WorkingMode

  def isModeLine(self) -> bool:
    return 'Line' in self.WorkingMode