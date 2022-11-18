import ast
import shutil
import copy
import gc
import os
import inspect
import collections
import multiprocess
from p_tqdm import p_map
import imp
#import numba
from asyncore import ExitNow
import random
import re
import sys
import plotext
import time
import openpyxl
import openpyxl.styles
import pickle
import xlsxwriter
import numpy
import zlib
import gzip
import statistics
import pathlib
import fileinput
import tempfile
import shelve
import dbm
from ansi2html import *
from libs.asci_drawing import *
from libs.bent_function import *
from libs.binstr import *
from libs.binstream import *
from libs.ca import *
from libs.cache import *
from libs.cas import *
from libs.cpp_program import *
from libs.database import *
from libs.eseries import *
from libs.esp32 import *
from libs.esp8266 import *
from libs.files import *
from libs.flags import *
from libs.gcd import *
from libs.gcode import *
from libs.interactive_menu import *
from libs.icarus_verilog import *
from libs.iterators import *
from libs.lfsr import *
from libs.logic import *
from libs.multi_process import *
from libs.nlfsr import *
from libs.nist import *
from pyeda.inter import *
from libs.phaseshifter import *
from libs.pandas_table import *
from libs.polynomial import *
from libs.preprocessor import *
from libs.programmable_lfsr import *
from libs.simplecommandparser import *
import libs.PolynomialsArithmetic as PolynomialsArithmetic
from libs.ring_oscillator import *
from libs.stats import *
from libs.unitnumber import *
from libs.utils_array import *
from libs.utils_bitarray import *
from libs.utils_int import *
from libs.utils_serial import *
from libs.utils_str import *
from libs.verilog import *
from tqdm import *
from simple_term_menu import *
import pathos
import pandas
from sympy import *
import matplotlib
#import matplotlib_inline
import matplotlib.pyplot as plt
import latex
import libs.jt as JT
import re
import cProfile, pstats, io
from libs.utils_list import *

pbar = tqdm
sleep = time.sleep

def printf(something):
    """Prints formatted data.
    Uses Aio.format() proc in the back.

    EXAMPLE
    
    printf([10,20,30])
    >>>
    [
        10
        20
        30
    ]
    """
    print(Aio.format(something))

def timeIt(Code : str, Iterations = 1):
    exec(Aio.timeItCode(Code, Iterations))
    
def profile(Code : str, FilterBuiltIns = True, FilterInternals = True):
    pr = cProfile.Profile()
    pr.enable()
    exec(Code)
    pr.disable()
    s = io.StringIO()
    sortby = pstats.SortKey.TIME
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    for Line in str(s.getvalue()).split("\n"):
        if FilterInternals and ("lib/python" in Line or 
                               "<frozen " in Line or
                               "__enter__" in Line or
                               "__exit__" in Line or
                               "'_thread." in Line or
                               "'_multiprocessing." in Line or
                               "'_pickle." in Line or
                               "'_random." in Line or
                               "'_socket." in Line or
                               "'_queue." in Line or
                               "__len__" in Line or
                               "__getitem__" in Line or
                               "'_hashlib." in Line or
                               "'_io." in Line or
                               "<string>:" in Line or
                               "function Random." in Line or
                               "function socket." in Line or
                               "built-in method" in Line):
            continue
        if FilterBuiltIns and (" of 'str' objects" in Line or 
                               " of 'dict' objects" in Line or 
                               " of 'set' objects" in Line or 
                               " of 'property' objects" in Line or 
                               " of 'bytes' objects" in Line or 
                               " of 'collections." in Line or 
                               " of 'int' objects" in Line or 
                               " of 'list' objects" in Line):
            continue
        if "'_lsprof.Profiler'" in Line:
            continue
        print(Line)


