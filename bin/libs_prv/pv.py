from libs.aio import *
from math import log, exp
from libs.stats import *
from tqdm import *
from p_tqdm import *
from pvlib import pvsystem
import suncalc

# azymut liczony od południa zgodnie z ruchem wskazowek zegara

class SolarSun:
    
    @staticmethod
    def getAzimuthAndAltitudeDegrees(Year : int, Month : int, Day : int, Hour : float, Lat : float, Long : float) -> tuple:
        H = int(Hour)
        M = int((Hour - H) * 60)
        S = 0
        from datetime import datetime
        from math import degrees
        Res = suncalc.get_position(datetime(Year, Month, Day, H, M, S), Long, Lat)
        return (degrees(Res['azimuth']), degrees(Res['altitude']))

    @staticmethod
    def getPVEfficiencyFactor(PanelTiltDegrees : float, PanelAzimuthDegrees : float, SunAzimuth : float, SunAltitude : float) -> float:
        from math import sin, cos, radians
        SunFactor = (sin((radians(SunAltitude))) * 0.5) + 0.5
        TiltEfficiency = cos(radians(90-SunAltitude-PanelTiltDegrees))
        AzimuthEfficiency = cos(radians(SunAzimuth-PanelAzimuthDegrees))
        if TiltEfficiency < 0:
            TiltEfficiency = 0.001
        if AzimuthEfficiency < 0:
            AzimuthEfficiency = 0.001
        return TiltEfficiency * AzimuthEfficiency * SunFactor
    
    @staticmethod
    def getPVEfficiencyFactorMorningShadow(AzimuthLimit : float, SunAzimuth : float, SunAltitude : float, ShadowFactor = 0.9, NonShadowAltitudeLimit : float = 90) -> float:
        if SunAltitude >= NonShadowAltitudeLimit:
            return 1.0
        return (1-ShadowFactor) if SunAzimuth<AzimuthLimit else 1.0
    
    @staticmethod
    def getPVEfficiencyFactorEveningShadow(AzimuthLimit : float, SunAzimuth : float, SunAltitude : float, ShadowFactor = 0.9, NonShadowAltitudeLimit : float = 90) -> float:
        if SunAltitude >= NonShadowAltitudeLimit:
            return 1.0
        return (1-ShadowFactor) if SunAzimuth>AzimuthLimit else 1.0
    
    @staticmethod
    def getPVEfficiencyFactorDaytimeShadow(MorningAzimuthLimit : float, EveningAzimuthLimit : float, SunAzimuth : float, SunAltitude : float, ShadowFactor = 0.5, NonShadowAltitudeLimit : float = 90) -> float:
        if SunAltitude >= NonShadowAltitudeLimit:
            return 1.0
        return (1-ShadowFactor) if EveningAzimuthLimit>SunAzimuth>MorningAzimuthLimit else 1.0
    

class SolarPanel:
    pass
class SolarPanel:
    
    __slots__ = ("parameters", "_vscale", "_iscale", "_cache")
    
    def copy(self) -> SolarPanel:
        return SolarPanel(self.parameters['V_mp_ref'], self.parameters['I_mp_ref'], self.parameters['V_oc_ref'], self.parameters['I_sc_ref'])
    
    def __init__(self, VMax : float, IMax : float, VOpen : float, IShort : float) -> None:
        self.parameters = {
            'I_sc_ref': IShort,
            'V_oc_ref': VOpen,
            'I_mp_ref': IMax,
            'V_mp_ref': VMax,
            'alpha_sc': 0.004539,
            'a_ref': 2.6373,
            'I_L_ref': 5.114,
            'I_o_ref': 8.196e-10,
            'R_s': 1.065,
            'R_sh_ref': 381.68
        }
        self._cache = {}
        self._vscale = 1
        self._iscale = 1
        ivp = self.getIVpoints(1, 25, 50)
        self._vscale = VMax / ivp[3]
        self._iscale = IMax / ivp[2]
        
    def getIVpoints(self, IrradianceFactor : float = 1, Temperature : float = 25, PointsCount = 100) -> tuple:
        if self._cache.get((IrradianceFactor, Temperature), None) is not None:
            return self._cache[(IrradianceFactor, Temperature)]
        Irradiance = IrradianceFactor * 1000
        if Irradiance < 1:
            Irradiance = 1
        IL, I0, Rs, Rsh, nNsVth = pvsystem.calcparams_desoto(
            Irradiance,
            Temperature,
            alpha_sc=self.parameters['alpha_sc'],
            a_ref=self.parameters['a_ref'],
            I_L_ref=self.parameters['I_L_ref'],
            I_o_ref=self.parameters['I_o_ref'],
            R_sh_ref=self.parameters['R_sh_ref'],
            R_s=self.parameters['R_s'],
            EgRef=1.121,
            dEgdT=-0.0002677
        )
        curve_info = pvsystem.singlediode(
            photocurrent=IL,
            saturation_current=I0,
            resistance_series=Rs,
            resistance_shunt=Rsh,
            nNsVth=nNsVth,
            ivcurve_pnts=PointsCount,
            method='lambertw'
        )
        vopenmax = self.parameters['V_oc_ref']
        IList = [x * self._iscale for x in curve_info['i']]
        VList = [x * self._vscale if x*self._vscale<vopenmax else vopenmax for x in curve_info['v']]
        im = curve_info['i_mp']*self._iscale
        vm = curve_info['v_mp']*self._vscale
        self._cache[(IrradianceFactor, Temperature)] = (IList, VList, im, vm, im*vm)
        return (IList, VList, im, vm, im*vm)
    
    def getVoltage(self, Current : float, IrradianceFactor : float = 1, Temperature : float = 25) -> float:
        ivp = self.getIVpoints(IrradianceFactor, Temperature)
        return Stats.predict(Current, ivp[0], ivp[1])
    
    def getIVCharacteristics(self, IrradianceFactor : float = 1, Temperature : float = 25, IStart : float = 0, IStop : float = 10, IStep : float = 0.1) -> tuple:
        ivp = self.getIVpoints(IrradianceFactor, Temperature)
        ilist,vlist = [],[]
        i = IStart
        while i < IStop:
            ilist.append(i)
            vlist.append(Stats.predict(i, ivp[0], ivp[1]))
            i += IStep
        return (ilist,vlist,ivp[2],ivp[3],ivp[2]*ivp[3])
        
        
class SolarMPPTModule:
    
    slots = ("_panels", "_pmax", "_imax", "_vminmppt", "_vmaxmppt", "_eff")
    
    def __len__(self) -> int:
        return len(self._panels)
    
    def __init__(self, VMinMppt : float, VMaxMppt : float, PMax : float, IMax : float, SolarPanelsList : list = [], Efficiency : float = 0.85) -> None:
        self._imax = float(IMax)
        self._pmax = float(PMax)
        self._vminmppt = float(VMinMppt)
        self._vmaxmppt = float(VMaxMppt)
        self._eff = float(Efficiency)
        self._panels = []
        for sp in SolarPanelsList:
            if type(sp) is SolarPanel:
                self._panels.append(sp)
        
    def getSolarPanels(self) -> list:
        return self._panels
    
    def getIVCharacteristics(self, IrradianceFactors : list = 1, Temperature : float = 25, IStart : float = 0, IStop : float = 10, IStep : float = 0.1) -> tuple:
        if len(self._panels) < 1:
            return None
        if type(IrradianceFactors) is not list:
            IrradianceFactors = [IrradianceFactors for _ in range(len(self._panels))]
        for spi in range(len(self._panels)):
            sp = self._panels[spi]
            spiv = sp.getIVCharacteristics(IrradianceFactors[spi], Temperature, IStart, IStop, IStep)
            if spi == 0:
                IList = spiv[0]
                VList = spiv[1]
            else:
                for j in range(len(VList)):
                    VList[j] += spiv[1][j]
        I,V,P = 0,0,0
        for i in range(len(IList)):
            if VList[i] > self._vmaxmppt:
                continue
            if VList[i] < self._vminmppt:
                break
            if IList[i] > self._imax:
                break
            p = IList[i] * VList[i]
            if p > self._pmax:
                break
            if p > P:
                P = p
                I = IList[i]
                V = VList[i]
        return (IList, VList, I, V, P, P*self._eff)
    

class SolarMPPTSimulator:
    
    __slots__ = ("_mppt", "_pmax", "_imax", "_vminmppt", "_vmaxmppt", "_eff", "_panels", "_shadows", "_panelpos", "_lat", "_long")
    
    def __init__(self, LocationLat : float, LocationLong : float,  MpptVMinMppt : float, MpptVMaxMppt : float, MpptPMax : float, MpptIMax : float, MpptEfficiency : float = 0.85) -> None:
        self._pmax = MpptPMax
        self._imax = MpptIMax
        self._vminmppt = MpptVMinMppt
        self._vmaxmppt = MpptVMaxMppt
        self._eff = MpptEfficiency
        self._lat = LocationLat
        self._long = LocationLong
        self._panels = []
        self._shadows = []
        self._panelpos = []
        self._mppt = None
        
    def addPanel(self, PanelPV : SolarPanel, TiltDegrees : float = 5, AzimuthDegrees : float = 0,
                MorningShadow : float = 0, MorningShadowAzimuthLimitDegrees : float = 0, MorningNonShadowAltitudeLimitDegrees : float = 90,
                EveningShadow : float = 0, EveningShadowAzimuthLimitDegrees : float = 0, EveningNonShadowAltitudeLimitDegrees : float = 90,
                DaytimeShadow : float = 0, DaytimeShadowMorningAzimuthLimitDegrees : float = -10, DaytimeShadowEveningAzimuthLimitDegrees = 10, DaytimeNonShadowAltitudeLimitDegrees : float = 90):
        self._panels.append(PanelPV)
        self._shadows.append([
            [MorningShadow, MorningShadowAzimuthLimitDegrees, MorningNonShadowAltitudeLimitDegrees],
            [EveningShadow, EveningShadowAzimuthLimitDegrees, EveningNonShadowAltitudeLimitDegrees],
            [DaytimeShadow, DaytimeShadowMorningAzimuthLimitDegrees, DaytimeShadowEveningAzimuthLimitDegrees, DaytimeNonShadowAltitudeLimitDegrees]
        ])
        self._panelpos.append([TiltDegrees, AzimuthDegrees])
        self._mppt = None
        
    def _getShadowedFactor(self, Index : int, SunAzimuthDegrees : float, SunAltitudeDegrees : float) -> float:
        Shadows = self._shadows[Index]
        Result = 1.0
        if Shadows[0][0] > 0:
            Result *= SolarSun.getPVEfficiencyFactorMorningShadow(Shadows[0][1], SunAzimuthDegrees, SunAltitudeDegrees, Shadows[0][0], Shadows[0][2])
        if Shadows[1][0] > 0:
            Result *= SolarSun.getPVEfficiencyFactorEveningShadow(Shadows[1][1], SunAzimuthDegrees, SunAltitudeDegrees, Shadows[1][0], Shadows[1][2])
        if Shadows[2][0] > 0:
            Result *= SolarSun.getPVEfficiencyFactorDaytimeShadow(Shadows[2][1], Shadows[2][2], SunAzimuthDegrees, SunAltitudeDegrees, Shadows[2][0], Shadows[2][3])
        return Result
    
    def _getEfficiencyFsctor(self, Index : int, SunAzimuthDegrees : float, SunAltitudeDegrees : float) -> float:
        SunEff = SolarSun.getPVEfficiencyFactor(self._panelpos[Index][0], self._panelpos[Index][1], SunAzimuthDegrees, SunAltitudeDegrees)
        ShadowEff = self._getShadowedFactor(Index, SunAzimuthDegrees, SunAltitudeDegrees)
        return SunEff * ShadowEff
    
    def getMpptPower(self, Month : int, Day : int, Hour : float, Temperature : float = 25, GlobalFactor : float = 0.9) -> float:
        SunAzimuth, SunAltitude = SolarSun.getAzimuthAndAltitudeDegrees(2020, Month, Day, Hour, self._lat, self._long)
        Factors = []
        for i in range(len(self._panels)):
            Factors.append(self._getEfficiencyFsctor(i, SunAzimuth, SunAltitude) * GlobalFactor)
        if self._mppt is None:
            self._mppt = SolarMPPTModule(self._vminmppt, self._vmaxmppt, self._pmax, self._imax, self._panels, self._eff)
        IV = self._mppt.getIVCharacteristics(Factors, Temperature, 0, self._imax, IStep = 0.1)
        return IV[-1]
    
    def getDaytimePower(self, Month : int, Day : int, Temperature : float = 25, HStep = 1, GlobalFactor : float = 0.9) -> tuple:
        Hours, Powers, Wh = [], [], 0
        H = (HStep/2)
        while H < 24:
            P = self.getMpptPower(Month, Day, H, Temperature, GlobalFactor)
            Hours.append(H)
            Powers.append(P)
            Wh += (P * HStep)
            H += HStep
        return (Hours, Powers, Wh/1000)
    
    def getMonthEnergy(self, Month : int, Temperature : float = 25, GlobalFactor : float = 0.9) -> tuple:
        Days, Energies, kWh = [], [], 0
        Day = 1
        from datetime import datetime
        while 1:
            _, _, DaykWh = self.getDaytimePower(Month, Day, Temperature, 1, GlobalFactor)
            Days.append(Day)
            kWh += DaykWh
            Energies.append(DaykWh)
            Day += 1
            if Day > 28:
                try:
                    datetime(2020, Month, Day)
                except:
                    break
        return (Days, Energies, kWh)
    
    def getYearEnergy(self, GlobalFactor : float = 0.9) -> tuple:
        Months, Energies, kWh = [], [], 0
        Temps = [0, 0, 5, 10, 15, 25, 35, 30, 20, 15, 10, 0]
        def calc(Month) -> float:
            Temperature = Temps[Month-1]
            _, _, MkWh = self.getMonthEnergy(Month, Temperature, GlobalFactor)
            return [Month, MkWh]
        for Result in p_imap(calc, range(1, 13)):
            Energies.append(Result[1])
            kWh += Result[1]
            Months.append(Result[0])
        #for Month in tqdm(range(1, 13), desc="Solar system simulating"):
        #    _, _, MonthkWh = self.getMonthEnergy(Month, Temperature, GlobalFactor)
        #    Energies.append(MonthkWh)
        #    kWh += MonthkWh
        #    Months.append(Month)
        AioShell.removeLastLine()
        return (Months, Energies, kWh)