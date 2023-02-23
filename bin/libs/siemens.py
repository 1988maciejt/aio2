from libs.aio import *

class Siemens:
    
    @staticmethod
    def get65nmDbFile() -> str:
        return Aio.getPath() + "siemens/adk.db"
    
    @staticmethod
    def get65nmLibFiles() -> list:
        return [Aio.getPath() + "siemens/adk.v"]
    
    @staticmethod
    def get16nmDbFile() -> str:
        return "/wv/arm_tessent/work/jmayer/A75_Prometheus/arm_a75_prometheus_core_rtl.tshell/libs/tsmc16ffp_sc10t080v_pssg_s300_v0880_t125.db"
    
    @staticmethod
    def get16nmLibFiles() -> list:
        return ["/wv/arm_tessent/work/jmayer/A75_Prometheus/arm_a75_prometheus_core_rtl.tshell/libs/tsmc16ffp_sc10t080v_pssg_s300_v0800_t125.lib", "/wv/arm_tessent/work/jmayer/A75_Prometheus/arm_a75_prometheus_core_rtl.tshell/libs/tsmc16ffp_sc10t080v.lib"]
    
    @staticmethod
    def get7nmDbFile() -> str:
        return "/wv/arm_tessent/libraries/tsmc_7nm_library/tsmc/cln07ff41001/sch240mc_base_lvt_c11/r12p0/db/sch240mc_cln07ff41001_base_lvt_c11_ffg_typical_max_1p05v_125c.db"
    
    @staticmethod
    def get7nmLibFiles() -> list:
        return []
    
    @staticmethod
    def getDbFile(TechnologyNm = 65) -> str:
        if TechnologyNm == 16:
            return Siemens.get16nmDbFile()
        elif TechnologyNm == 7:
            return Siemens.get7nmDbFile()
        return Siemens.get65nmDbFile()
    
    @staticmethod
    def getLibFiles(TechnologyNm = 65) -> list:
        if TechnologyNm == 16:
            return Siemens.get16nmLibFiles()
        elif TechnologyNm == 7:
            return Siemens.get7nmLibFiles()
        return Siemens.get65nmLibFiles()
    
    @staticmethod
    def getNandGateArea(TechnologyNm = 65) -> int:
        if TechnologyNm == 16:
            return 0.18144
        elif TechnologyNm == 7:
            return 0.05472
        return 1.0
    