# Funkcje od Profesora JT

randU_GenVal = 123456789
def randU (Lower : int, Upper : int):
    global randU_GenVal
    h = int(randU_GenVal/127773) & 0xFFFFFFFF
    randU_GenVal = (16807*(randU_GenVal - 127773*h) - 2836*h) & 0xFFFFFFFF
    if (randU_GenVal & 80000000 == 80000000):
        randU_GenVal += 2147483647 & 0xFFFFFFFF
    x = float(randU_GenVal) / 2147483647.0;
#    return randU_GenVal & 1
    return Lower + int(x*(Upper - Lower + 1));