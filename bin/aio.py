import shutil
import copy
import gc
import os
import inspect
import collections
import multiprocessing
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
from libs.binstr import *
from libs.binstream import *
from libs.ca import *
from libs.cache import *
from libs.cas import *
from libs.database import *
from libs.eseries import *
from libs.files import *
from libs.flags import *
from libs.gcd import *
from libs.gcode import *
from libs.interactive_menu import *
from libs.icarus_verilog import *
from libs.lfsr import *
from libs.logic import *
from libs.multi_process import *
from libs.nist import *
from libs.polynomial import *
from libs.preprocessor import *
import libs.PolynomialsArithmetic as PolynomialsArithmetic
from libs.ring_oscillator import *
from libs.stats import *
from libs.unitnumber import *
from libs.utils_array import *
from libs.utils_int import *
from libs.utils_list import *
from libs.utils_serial import *
from libs.utils_str import *
from libs.verilog import *
from tqdm import *
from simple_term_menu import *
import pathos
from sympy import *
import matplotlib
#import matplotlib_inline
import matplotlib.pyplot as plt
import latex
import libs.jt as JT
import re


pbar = tqdm
sleep = time.sleep


