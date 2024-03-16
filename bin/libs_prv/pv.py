from libs.aio import *
from math import log, exp

from pvlib import pvsystem


class SolarPanel:
    
    __slots__ = ("parameters")
    
    def __init__(self, VMax : float, IMax : float, VOpen : float, IShort : float) -> None:
        self.parameters = {
            #'Name': 'Canadian Solar CS5P-220M',
            'BIPV': 'N',
            'Date': '10/5/2009',
            'T_NOCT': 42.4,
            'A_c': 1.7,
            'N_s': 96,
            'I_sc_ref': IShort,
            'V_oc_ref': VOpen,
            'I_mp_ref': IMax,
            'V_mp_ref': VMax,
            'alpha_sc': 0.004539,
            'beta_oc': -0.22216,
            'a_ref': 2.6373,
            'I_L_ref': 5.114,
            'I_o_ref': 8.196e-10,
            'R_s': 1.065,
            'R_sh_ref': 381.68,
            'Adjust': 8.7,
            'gamma_r': -0.476,
            'Version': 'MM106',
            'PTC': 200.1,
            'Technology': 'Mono-c-Si',
        }
        
    def getIVpoints(self, IrradianceFactor : float = 1, Temperature : float = 25) -> tuple:
        Irradiance = IrradianceFactor * 1000
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
            ivcurve_pnts=100,
            method='lambertw'
        )
        return (list(curve_info['i']), list(curve_info['v']), curve_info['i_mp'], curve_info['v_mp'], curve_info['p_mp'])
    