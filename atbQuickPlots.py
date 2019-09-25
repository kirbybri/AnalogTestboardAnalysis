import h5py
import numpy as np
from math import *
import matplotlib.pyplot as plt
import json
import sys

from atbProcessFile import ATB_PROCESS_FILE
from atbPlotResults import ATB_PLOT_RESULTS

def main():
  if len(sys.argv) < 2 :
    print("ERROR, program requires filename as arguments")
    #print("ERROR, program requires filename and board name as arguments")
    return

  fileName = sys.argv[1]
  boardName = "Board"
  if len(sys.argv) == 3 :
    boardName = sys.argv[2]

  atbProcessFile = ATB_PROCESS_FILE(fileName)
  atbProcessFile.processFile()
  #atbProcessFile.outputFile()
  results = atbProcessFile.runResultsDict

  atbPlotResults = ATB_PLOT_RESULTS()
  atbPlotResults.fileName = fileName
  atbPlotResults.boardName = boardName
  atbPlotResults.runResults = results
  #atbPlotResults.processFile()
  atbPlotResults.processResults()

#-------------------------------------------------------------------------
if __name__ == "__main__":
  main()
