from libs.aio import *
from math import log, exp
from libs.stats import *
from tqdm import *
from p_tqdm import *
from pvlib import pvsystem
import suncalc
from libs.generators import *

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
            TiltEfficiency = 0
        if AzimuthEfficiency < 0: 
            AzimuthEfficiency = 0
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
        return SolarPanel(self.parameters['V_mp_ref'], self.parameters['I_mp_ref'], self.parameters['V_oc_ref'], self.parameters['I_sc_ref'],
                self.parameters['tilt'], self.parameters['azimuth'],
                self.parameters['morning_shadow'], self.parameters['morning_shadow_azimuth'], self.parameters['morning_nonshadow_altitude'],
                self.parameters['evening_shadow'], self.parameters['evening_shadow_azimuth'], self.parameters['evening_nonshadow_altitude'],
                self.parameters['daytime_shadow'], self.parameters['daytime_morning_shadow_azimuth'], self.parameters['daytime_evening_shadow_azimuth'], self.parameters['daytime_nonshadow_altitude'])
    
    def __init__(self, VMax : float, IMax : float, VOpen : float, IShort : float, TiltDegrees : float = 5, AzimuthDegrees : float = 0,
                MorningShadow : float = 0, MorningShadowAzimuthLimitDegrees : float = 0, MorningNonShadowAltitudeLimitDegrees : float = 90,
                EveningShadow : float = 0, EveningShadowAzimuthLimitDegrees : float = 0, EveningNonShadowAltitudeLimitDegrees : float = 90,
                DaytimeShadow : float = 0, DaytimeShadowMorningAzimuthLimitDegrees : float = -10, DaytimeShadowEveningAzimuthLimitDegrees = 10, DaytimeNonShadowAltitudeLimitDegrees : float = 90,
                BypasDiodesIncluded = True) -> None:
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
            'R_sh_ref': 381.68,
            "morning_shadow": MorningShadow,
            "morning_shadow_azimuth": MorningShadowAzimuthLimitDegrees,
            "morning_nonshadow_altitude": MorningNonShadowAltitudeLimitDegrees,
            "evening_shadow": EveningShadow,
            "evening_shadow_azimuth": EveningShadowAzimuthLimitDegrees,
            "evening_nonshadow_altitude": EveningNonShadowAltitudeLimitDegrees,
            "daytime_shadow": DaytimeShadow,
            "daytime_morning_shadow_azimuth": DaytimeShadowMorningAzimuthLimitDegrees,
            "daytime_evening_shadow_azimuth": DaytimeShadowEveningAzimuthLimitDegrees,
            "daytime_nonshadow_altitude": DaytimeNonShadowAltitudeLimitDegrees,
            "bypass_diodes": BypasDiodesIncluded,
        }
        self._vscale = 1
        self._iscale = 1
        self._cache = {}
        self.parameters["tilt"] = 0
        self.parameters["azimuth"] = 0
        ivp = self.getIVpoints(1, 25, 50)
        self.parameters["tilt"] = TiltDegrees
        self.parameters["azimuth"] = AzimuthDegrees
        self._cache = {}
        self._vscale = VMax / ivp[3]
        self._iscale = IMax / ivp[2]
        ivp = self.getIVpoints(1, 25, 50)
        
    def getVOC(self):
        return self.parameters['V_oc_ref']
        
    def _getShadowedFactor(self, SunAzimuthDegrees : float, SunAltitudeDegrees : float) -> float:
        Result = 1.0
        if self.parameters["morning_shadow"] > 0:
            Result *= SolarSun.getPVEfficiencyFactorMorningShadow(self.parameters["evening_shadow_azimuth"], SunAzimuthDegrees, SunAltitudeDegrees, self.parameters["morning_shadow"], self.parameters["morning_nonshadow_altitude"])
        if self.parameters["evening_shadow"] > 0:
            Result *= SolarSun.getPVEfficiencyFactorEveningShadow(self.parameters["evening_shadow_azimuth"], SunAzimuthDegrees, SunAltitudeDegrees, self.parameters["evening_shadow"], self.parameters["evening_nonshadow_altitude"])
        if self.parameters["daytime_shadow"] > 0:
            Result *= SolarSun.getPVEfficiencyFactorDaytimeShadow(self.parameters["daytime_morning_shadow_azimuth"], self.parameters["daytime_evening_shadow_azimuth"], SunAzimuthDegrees, SunAltitudeDegrees, self.parameters["daytime_shadow"], self.parameters["daytime_nonshadow_altitude"])
        return Result
        
    def getIVpoints(self, IrradianceFactor : float = 1, Temperature : float = 25, PointsCount = 20, SunAzimuthDegrees : float = 0, SunAltitudeDegrees : float = 90) -> tuple:
        IrradianceFactor *= self._getShadowedFactor(SunAzimuthDegrees, SunAltitudeDegrees)
        IrradianceFactor *= SolarSun.getPVEfficiencyFactor(self.parameters["tilt"], self.parameters["azimuth"], SunAzimuthDegrees, SunAltitudeDegrees)
        Irradiance = int(IrradianceFactor * 1000)
        if Irradiance < 1:
            Irradiance = 1
        Temperature = int(Temperature)
        if self._cache.get((Irradiance, Temperature, PointsCount), None) is not None:
            return self._cache[(Irradiance, Temperature, PointsCount)]
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
        self._cache[(Irradiance, Temperature, PointsCount)] = (IList, VList, im, vm, im*vm)
        return (IList, VList, im, vm, im*vm)
    
    def getVoltage(self, Current : float, IrradianceFactor : float = 1, Temperature : float = 25, SunAzimuthDegrees : float = 0, SunAltitudeDegrees : float = 90) -> float:
        ivp = self.getIVpoints(IrradianceFactor, Temperature, 100, SunAzimuthDegrees, SunAltitudeDegrees)
        v = Stats.predict(Current, ivp[0], ivp[1])
        if self.parameters["bypass_diodes"]:
            if v < -0.7:
                v = -0.7
    
    def getIVCharacteristics(self, IrradianceFactor : float = 1, Temperature : float = 25, IStart : float = 0, IStop : float = 10, IStep : float = 0.1, SunAzimuthDegrees : float = 0, SunAltitudeDegrees : float = 90, VMin = 0) -> tuple:
        ivp = self.getIVpoints(IrradianceFactor, Temperature, 100, SunAzimuthDegrees, SunAltitudeDegrees)
        ilist,vlist = [],[]
        i = IStart
        while i < IStop:
            ilist.append(i)
            v = Stats.predict(i, ivp[0], ivp[1])
            if self.parameters["bypass_diodes"]:
                if v < -0.7:
                    v = -0.7
            vlist.append(v)
            i += IStep
        return (ilist,vlist,ivp[2],ivp[3],ivp[2]*ivp[3])
    
    
class SolarPanelSeries:
    pass
class SolarPanelSeries:
    
    __slots__ = ("_panels", "_voc")
    
    def copy(self) -> SolarPanelSeries:
        return SolarPanelSeries(self._panels)
    
    def __init__(self, Panels : list) -> None:
        self._panels = Panels.copy()
        self._voc = 0
        for Panel in Panels:
            self._voc += Panel.getVOC()
        
    def getVOC(self):
        return self._voc
    
    def getIVCharacteristics(self, IrradianceFactor : float = 1, Temperature : float = 25, IStart : float = 0, IStop : float = 10, IStep : float = 0.1, SunAzimuthDegrees : float = 0, SunAltitudeDegrees : float = 90, VMin = 0) -> tuple:
        if len(self._panels) < 1:
            return None
        Imax, Vmax, Pmax = 0,0,0
        for i in range(len(self._panels)):
            iv = self._panels[i].getIVCharacteristics(IrradianceFactor, Temperature, IStart, IStop, IStep, SunAzimuthDegrees, SunAltitudeDegrees, VMin)
            if i == 0:
                IList, VList = Stats.interAndExtrapolate(iv[0], iv[1], IStart, IStop, IStep)
            else:
                il, vl = Stats.interAndExtrapolate(iv[0], iv[1], IStart, IStop, IStep)
                for j in range(len(IList)):
                    VList[j] += vl[j]
        for ind in range(len(IList)):
            I = IList[ind]
            if I <= 0:
                continue
            V = VList[ind]
            if 0 < V < VMin:
                break
            P = I * V
            if Pmax < P:
                Pmax = P
                Imax = I
                Vmax = V
            else:
                if Pmax > 0:
                    break
        return (IList, VList, Imax, Vmax, Pmax)
    
        
class SolarPanelParallel:
    pass
class SolarPanelParallel:
    
    __slots__ = ("_panels", "_voc")
    
    def copy(self) -> SolarPanelParallel:
        return SolarPanelParallel(self._panels)
    
    def __init__(self, Panels : list) -> None:
        self._panels = Panels.copy()
        self._voc = 0
        for Panel in Panels:
            pvoc = Panel.getVOC()
            if pvoc > self._voc:
                self._voc = pvoc
        
    def getVOC(self):
        return self._voc
    
    def getIVCharacteristics(self, IrradianceFactor : float = 1, Temperature : float = 25, IStart : float = 0, IStop : float = 10, IStep : float = 0.1, SunAzimuthDegrees : float = 0, SunAltitudeDegrees : float = 90, VMin = 0) -> tuple:
        if len(self._panels) < 1:
            return None
        VStop = self._voc
        VStep = VStop / 50
        Imax, Vmax, Pmax = 0,0,0
        for i in range(len(self._panels)):
            iv = self._panels[i].getIVCharacteristics(IrradianceFactor, Temperature, IStart, IStop, IStep, SunAzimuthDegrees, SunAltitudeDegrees, VMin)
            if i == 0:
                VList, IList = Stats.revertFunction(iv[0], iv[1], 0, VStop, VStep)
            else:
                vl, il = Stats.revertFunction(iv[0], iv[1], 0, VStop, VStep)
                for j in range(len(IList)):
                    IList[j] += il[j]
        #Plot([IList, VList]).print()
        for ind in range(len(IList)):
            I = IList[len(IList)-ind-1]
            if I <= 0:
                continue
            V = VList[len(VList)-ind-1]
            if 0 < V < VMin:
                break
            P = I * V
            if Pmax < P:
                Pmax = P
                Imax = I
                Vmax = V
            else:
                if Pmax > 0:
                    break
        #print(Imax, Vmax, Pmax)
        IRes, VRes = Stats.revertFunction(VList, IList, IStart, IStop, IStep)
        #print ((IRes, VRes, Imax, Vmax, Pmax))
        return (IRes, VRes, Imax, Vmax, Pmax)

        
        
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
            if type(sp) in [SolarPanel, SolarPanelParallel, SolarPanelSeries]:
                self._panels.append(sp)
        
    def getSolarPanels(self) -> list:
        return self._panels
    
    def getIVCharacteristics(self, IrradianceFactor : float = 1, Temperature : float = 25, IStart : float = 0, IStop : float = 10, IStep : float = 0.1, SunAzimuthDegrees : float = 0, SunAltitudeDegrees : float = 90, VMin = 0) -> tuple:
        if len(self._panels) < 1:
            return None
        return SolarPanelSeries(self._panels).getIVCharacteristics(IrradianceFactor, Temperature, IStart, IStop, IStep, SunAzimuthDegrees, SunAltitudeDegrees, VMin)    


class SolarMPPTSimulator:
    
    __slots__ = ("_mppt", "_pmax", "_imax", "_vminmppt", "_vmaxmppt", "_eff", "_panels", "_lat", "_long")
    
    def __init__(self, LocationLat : float, LocationLong : float,  MpptVMinMppt : float, MpptVMaxMppt : float, MpptPMax : float, MpptIMax : float, MpptEfficiency : float = 0.85) -> None:
        self._pmax = MpptPMax
        self._imax = MpptIMax
        self._vminmppt = MpptVMinMppt
        self._vmaxmppt = MpptVMaxMppt
        self._eff = MpptEfficiency
        self._lat = LocationLat
        self._long = LocationLong
        self._panels = []
        self._mppt = None
        
    def addPanel(self, PanelPV : SolarPanel):
        self._panels.append(PanelPV)
        self._mppt = None
    
    def _getEfficiencyFsctor(self, Index : int, SunAzimuthDegrees : float, SunAltitudeDegrees : float) -> float:
        SunEff = SolarSun.getPVEfficiencyFactor(self._panelpos[Index][0], self._panelpos[Index][1], SunAzimuthDegrees, SunAltitudeDegrees)
        ShadowEff = self._getShadowedFactor(Index, SunAzimuthDegrees, SunAltitudeDegrees)
        return SunEff * ShadowEff
    
    def getMpptPower(self, Month : int, Day : int, Hour : float, Temperature : float = 25, GlobalFactor : float = 0.9) -> float:
        SunAzimuth, SunAltitude = SolarSun.getAzimuthAndAltitudeDegrees(2020, Month, Day, Hour, self._lat, self._long)
        if SunAltitude < 0:
            return 0.0
        if self._mppt is None:
            self._mppt = SolarMPPTModule(self._vminmppt, self._vmaxmppt, self._pmax, self._imax, self._panels, self._eff)
        IV = self._mppt.getIVCharacteristics(GlobalFactor, Temperature, 0, self._imax, IStep = 0.1, SunAzimuthDegrees=SunAzimuth, SunAltitudeDegrees=SunAltitude, VMin=self._vminmppt)
        if (IV[-2]) < self._vminmppt:
            return 0
        if (IV[-1]) > self._pmax:
            return self._pmax
        return IV[-1]
    
    def getDaytimePower(self, Month : int, Day : int, Temperature : float = 25, HStep = 1, GlobalFactor : float = 0.9) -> tuple:
        Hours, Powers, Wh = [], [], 0
        H = (HStep/2)
        while H < 24:
            #print(H)
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
        #def calc(MDD) -> float:
        #    Temperature = Temps[MDD[0]]
        #    _, _, DkWh = self.getDaytimePower(MDD[0], MDD[1], Temperature, 1, GlobalFactor)
        #    return [MDD[2], DkWh]
        #for Result in p_imap(calc, Generators().dayAndMonthOfYear(2020, True), total=365):
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
    
    def findOptimalPanelPosition(self) -> tuple:
        Azimuths = []
        Altitudes = []
        AltitudesEff = []
        from math import sin, radians
        for Moy, Dom, Doy in Generators().dayAndMonthOfYear(2020, True):
            AlMax = 0
            AzList = []
            for H in range(0, 24):
                Az, Al = SolarSun.getAzimuthAndAltitudeDegrees(2020, Moy, Dom, H+0.5, self._lat, self._long)
                if Al > 0:
                    AzList.append(Az)
                    if Al > AlMax:
                        AlMax = Al
                        SunFactor = (sin((radians(Al))) * 0.5) + 0.5
            AltitudesEff.append(SunFactor)
            Azimuths.append(AzList[len(AzList)//2])
            Altitudes.append(AlMax)
            BestAltitude = 0
            for i in range(len(Altitudes)):
                BestAltitude += Altitudes[i] * AltitudesEff[i]
            BestAltitude /= sum(AltitudesEff)
            BestTilt = 90 - BestAltitude
            BestAzimuth = sum(Azimuths) / len(Azimuths)
        return (BestAzimuth, BestTilt)