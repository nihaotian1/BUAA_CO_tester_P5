# -*- coding:utf-8 -*-
import os

projectPath = "D:\\CO\\CO_P5\\pipelineCPU"
xilinxPath = "C:\\Xilinx\\14.7\\ISE_DS\\ISE\\"

os.chdir(projectPath)
os.environ['XILINX'] = xilinxPath # 设置环境变量
os.system(xilinxPath + "bin/nt64/fuse -nodebug -prj mips.prj -o mips.exe tb > mips.log") # 编译
os.system("mips.exe -nolog -tclbatch mips.tcl > res.txt") # 运行
