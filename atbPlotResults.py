import json
import sys
import numpy as np
from math import *
#import matplotlib.pyplot as plt
import matplotlib.pyplot as plt

#BEGIN ATB_PLOT_RESULTS CLASS
class ATB_PLOT_RESULTS(object):

  #__INIT__#
  def __init__(self,fileName=None,boardName=None):
    self.fileName = fileName
    self.boardName = boardName
    self.runResults = None
    self.plotResults = True
    self.plotWithLimits = False

  #finally make some plots using info in results dict
  def makePlots(self, asic, ch, titleTextBase = "Example", figureName = "fig", low=0,high=60000):
    if 'results' not in self.runResults :
      return None
    boardResult = self.runResults['results']
    if asic not in boardResult:
      return None
    chResult = boardResult[asic]
    if ch not in chResult:
      return None
    chInfo = chResult[ch]

    amps = []
    peds = []
    rmss = []
    maxs = []
    peaks = []
    snrs = []
    for amp in chInfo.keys():
      ampInfo = chInfo[amp]
      ampVal = float(amp)
      amps.append(ampVal)
      peds.append(ampInfo['ped'])
      rmss.append(ampInfo['rms'])
      maxs.append(ampInfo['max'])
      peaks.append(ampInfo['max'] - ampInfo['ped'])
      snr = 0
      if ampInfo['rms'] > 0 :
        snr = (ampInfo['max'] - ampInfo['ped'])/ampInfo['rms']
      snrs.append(snr)

      #print( amp, "\t", ampInfo['ped'], "\t", ampInfo['max'] )
      #peaks.append( chResult[amp]['max'])
      #peaks.append( chResult[amp]['ped'])
      #peaks.append( chResult[amp]['min']- chResult[amp]['ped'])

    order = np.argsort(amps)
    xs = np.array(amps)[order]
    ys = np.array(peaks)[order]
    #ys = np.array(snrs)[order]
    #ys = np.array(rmss)[order]

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(xs, ys,'.')
    if self.plotWithLimits :
      ax.set_xlim(low,high)
    #ax.set_xlabel('Pulser DAC [DAC code]', horizontalalignment='right', x=1.0)
    ax.set_xlabel('Pulse Signal Amplitude [V]', horizontalalignment='right', x=1.0)
    ax.set_ylabel('Pulse Height [ADC counts]', horizontalalignment='left', x=1.0)
    #ax.set_ylabel('SNR', horizontalalignment='left', x=1.0)
    #ax.set_ylabel('RMS', horizontalalignment='left', x=1.0)
    #ax.set_ylabel('Pulse Peak Sample Value [ADC counts]', horizontalalignment='left', x=1.0)
    #ax.set_title(titleTextBase + " : Pulse Peak vs Pulser DAC")
    #ax.set_title(titleTextBase + " : Pulse Height count vs Pulser DAC")
    ax.set_title(titleTextBase + " : Pulse Height vs Signal Amplitude")
    #ax.set_title(titleTextBase + " : SNR vs Signal Amplitude")
    #ax.set_title(titleTextBase + " : RMS vs Signal Amplitude")
    fig.tight_layout()
    plt.savefig(figureName + "_pulseHeightVsSig")
    #plt.savefig(figureName + "_RMSVsSig")
    if self.plotResults :
      plt.show() #plt.clf()

    return None

  def processResults(self):
    if self.runResults == None :
      return None
    fileName = self.fileName
    boardName= self.boardName

  def makeAllPlots(self):
    """
    self.makePlots(('coluta1', 'channel1'),self.boardName + " COLUTA 1 Low Gain",self.boardName+'_coluta1_lg',0,100000)
    self.makePlots(('coluta1', 'channel2'),self.boardName + " COLUTA 1 High Gain",self.boardName+'_coluta1_hg',0,5000)
    self.makePlots(('coluta2', 'channel1'),self.boardName + " COLUTA 2 High Gain",self.boardName+'_coluta2_hg',0,5000)
    self.makePlots(('coluta2', 'channel2'),self.boardName + " COLUTA 2 Low Gain",self.boardName+'_coluta2_lg',0,100000)
    """
    
    self.makePlots('coluta1', 'channel1',self.boardName + " COLUTA 1 Ch 1 Low Gain",self.boardName+'_coluta1_ch1_lg',0,0.5)
    self.makePlots('coluta1', 'channel2',self.boardName + " COLUTA 1 Ch 2 High Gain",self.boardName+'_coluta1_ch2_hg',0,0.5)
    self.makePlots('coluta2', 'channel1',self.boardName + " COLUTA 2 Ch 1 High Gain",self.boardName+'_coluta2_ch1_hg',0,0.5)
    self.makePlots('coluta2', 'channel2',self.boardName + " COLUTA 2 Ch 2 Low Gain",self.boardName+'_coluta2_ch2_lg',0,0.5)
    
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

  atbPlotResults = ATB_PLOT_RESULTS(fileName)
  atbPlotResults.fileName = fileName
  atbPlotResults.boardName = boardName
  atbPlotResults.processFile()
  atbPlotResults.processResults()
  atbPlotResults.makeAllPlots()

#-------------------------------------------------------------------------
if __name__ == "__main__":
  main()
