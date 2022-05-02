import subprocess
from libs.aio import *
import os
import re
from libs.files import *

class Nist:
  def sp800_22_execute(FileName : str) -> str:
    try:
      tmp = TempDir()
      Aio.shellExecute(f'cp -a ~/nist/sp800_22_tests {tmp.path()}')
      exefile = tmp.path() + "/sp800_22_tests/sp800_22_tests.py"
      raw = Aio.shellExecute(f'python3 {exefile} {FileName}')
      result = { "raw": raw }
      for test in ['monobit_test','frequency_within_block_test',
          'runs_test','longest_run_ones_in_a_block_test',
          'binary_matrix_rank_test','dft_test',
          'non_overlapping_template_matching_test','overlapping_template_matching_test',
          'maurers_universal_test','linear_complexity_test',
          'serial_test','approximate_entropy_test',
          'cumulative_sums_test','random_excursion_test','random_excursion_variant_test']:
        rg = re.search(f'{test}\s+([0-9.]+)\s+(PASS|FAIL)', raw)
        if rg:
          result[test] = [rg.group(2), rg.group(1)]
        del t
      return result
    except:
      Aio.printError("No SP800-22 test suite installed. Install using the script from aio2/utils/nist.")
  def sp800_90b_execute(FileName : str, iid = True) -> str:
    try:
      if iid:
        result = Aio.shellExecute("~/nist/SP800-90B_EntropyAssessment/cpp/ea_iid " + FileName)
      else:
        result = Aio.shellExecute("~/nist/SP800-90B_EntropyAssessment/cpp/ea_non_iid " + FileName)
      return result
    except:
      Aio.printError("No SP800-90b test suite installed. Install using the script from aio2/utils/nist.")
