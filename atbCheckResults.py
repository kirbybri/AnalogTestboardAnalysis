import json
import sys
import numpy as np
from math import *
#import matplotlib.pyplot as plt
import matplotlib.pyplot as plt

class ATB_CHECK_RESULTS(object):

  #__INIT__#
  def __init__(self,fileName=None,boardName=None):
    self.fileName = fileName
    self.boardName = boardName
    self.runResults = None
    self.boardResult = None
    self.plotResults = True
    self.plotWithLimits = True

  # plot waveform samples
  def plot_wf(self,wf_data,a=0,b=1000):
    plt.plot(wf_data[a:b],'.-')#plt.plot(wf_data,'.-')#
    plt.xlabel('samples', horizontalalignment='right', x=1.0)
    plt.ylabel('ADC counts')
    plt.title("Example Waveform")
    plt.show() #plt.clf()

  def processResults(self):
    if self.runResults == None :
      return None
    fileName = self.fileName
    boardName= self.boardName
    if 'results' not in self.runResults :
      return None
    boardMeas =  self.runResults['results']

    for asic in boardMeas :
      print("ASIC\t",asic)
      for ch in boardMeas[asic] :
        print("\tCH  \t",ch)
        for amp in boardMeas[asic][ch] :
          print("\t\tAMP \t",amp)
          print("\t\tped\t",boardMeas[asic][ch][amp]['ped'] )
          print("\t\trms\t",boardMeas[asic][ch][amp]['rms'] )
          print("\t\tmax\t",boardMeas[asic][ch][amp]['max'] )
          print("\t\tmin\t",boardMeas[asic][ch][amp]['min'] )
          if 'wf' in boardMeas[asic][ch][amp] and self.plotResults :
            self.plot_wf(boardMeas[asic][ch][amp]['wf'] )
    
  def processFile(self):
    #open list of measurements, get all results
    with open(self.fileName) as json_data:
      self.runResults = json.load(json_data)

def main():
  if len(sys.argv) < 2 :
    print("ERROR, program requires filename as argument")
    return

  fileName = sys.argv[1]
  boardName = 'Board'
  if len(sys.argv) == 3 :
    boardName = sys.argv[2]

  atbCheckResults = ATB_CHECK_RESULTS(fileName)
  atbCheckResults.fileName = fileName
  atbCheckResults.boardName = boardName
  atbCheckResults.processFile()
  atbCheckResults.processResults()

#-------------------------------------------------------------------------
if __name__ == "__main__":
  main()
