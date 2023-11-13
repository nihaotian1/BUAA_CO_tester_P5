#!/bin/bash
python main.py
java -jar Mars_CO_v0.4.1.jar code.asm db nc mc CompactLargeText coL1 ig > log.txt
java -jar Mars_CO_v0.4.1.jar code.asm db mc CompactDataAtZero a dump .text HexText D:\\CO\\CO_P5\\pipelineCPU\\code.txt
python runISE.py
python compare.py