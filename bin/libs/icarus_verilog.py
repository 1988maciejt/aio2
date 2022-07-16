from libs.aio import *


class IcarusVerilog:
  def vlog(FileList):
    if not Aio.isType(FileList, []):
      FileList = [str(FileList)]
    cmd = "iverilog -o work_design.iverilog"
    for File in FileList:
      cmd += f' {File}'
    Aio.shellExecute(cmd)