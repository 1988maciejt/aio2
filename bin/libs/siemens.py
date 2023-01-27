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
    def getDbFile(TechnologyNm = 65) -> str:
        if TechnologyNm == 16:
            return Siemens.get16nmDbFile()
        return Siemens.get65nmDbFile()
    
    @staticmethod
    def getLibFiles(TechnologyNm = 65) -> list:
        if TechnologyNm == 16:
            return Siemens.get16nmLibFiles()
        return Siemens.get65nmLibFiles()