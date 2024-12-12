import ast
import shutil
import copy
import cython
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
import zlib
import gzip
import statistics
import pathlib
import fileinput
import tempfile
import shelve
import dbm
from ansi2html import *
import atexit
from libs.aio_auto import *
from libs.asci_drawing import *
from libs.bent_function import *
from libs.binstr import *
from libs.binstream import *
from libs.ca import *
from libs.cache import *
from libs.cas import *
from libs.cpp_program import *
from libs.cython import *
from libs.database import *
from libs.eseries import *
from libs.esp32 import *
from libs.esp8266 import *
from libs.fast_anf_algebra import *
from libs.files import *
from libs.gf2_polynomial import *
from libs.gcd import *
from libs.gcode import *
from libs.gpt_tools import *
from libs.interactive_menu import *
from libs.lfsr import *
from libs.nlfsr import *
from libs.phaseshifter import *
from libs.pandas_table import *
from libs.polynomial import *
from libs.preprocessor import *
from libs.programmable_lfsr import *
from libs.remote_aio import *
from libs.simplecommandparser import *
import libs.PolynomialsArithmetic as PolynomialsArithmetic
from libs.ring_oscillator import *
from libs.simple_threading import *
from libs.simpletree import *
from libs.stats import *
from libs.temp_transcript import *
from libs.unitnumber import *
from libs.utils_array import *
from libs.utils_bitarray import *
from libs.utils_int import *
from libs.utils_tui import *
from libs.generators import *
from libs.udp import *
from libs.utils_serial import *
from libs.utils_str import *
from libs.utils_sympy import *
from libs.verilog import *
from libs.verilog_creator import *
from libs.utils_docx import *
from libs.utils_pdf import *
from libs.simulation import *
from tqdm import *
import bitarray.util
from bitarray import *
import pathos
import pandas
from sympy import *
import matplotlib
import rich
import rich.pretty
#import matplotlib_inline
import matplotlib.pyplot as plt
import latex
import libs.jt as JT
import re
import cProfile, pstats, io
from libs.utils_list import *
from libs.rpi import *
import pint
# research projects - libs
import libs.research_projects.root_of_trust.root_of_trust as RootOfTrust
import libs.research_projects.orthogonal_compactor.orthogonal_compactor as OrthogonalCompactor
import warnings

warnings.simplefilter("ignore")

from aio_config import shell_config

try:
    if shell_config.priv():
        from libs_prv.aio_priv import *
except:
    pass

unit = pint.UnitRegistry()

pbar = tqdm
sleep = time.sleep

printf = rich.pretty.pprint
pprint = rich.pretty.pprint
inspect = rich.inspect

random.seed(int(time.time() * 10000000) % (1<<63))

AioAuto.atStart()
atexit.register(AioAuto.atExit)

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


