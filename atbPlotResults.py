import json
import sys
import numpy as np
from math import *
import matplotlib.pyplot as plt

#BEGIN ATB_PLOT_RESULTS CLASS
class ATB_PLOT_RESULTS(object):

  #__INIT__#
  def __init__(self,fileName=None,boardName=None):
    self.fileName = fileName
    self.boardName = boardName
    self.runResults = None

  #reorganize measurement data by ASIC, ch and pulser DAC
  def collect(self, runResults):
    if 'results' not in runResults :
      return None
    results = runResults['results']

    #loop over the measurements, organize by ASIC + ch, dac
    boardMeas = {}
    for results_key in results.keys() :
      meas = results[results_key]
      for result in meas :
        asic = result['coluta']
        ch = result['channel']
        if ( asic, ch) not in boardMeas :
          boardMeas[ ( asic, ch) ] = {}
        amp = result['pulser']
        if amp not in boardMeas[ ( asic, ch) ] :
          boardMeas[ ( asic, ch) ][amp] = []
        boardMeas[ ( asic, ch) ][amp].append( { 'ped' : result['ped'] , 'rms' : result['rms'], 'max' : result['max'] } )
    return boardMeas

  #combine the multiple measurements made with the same DAC into one value
  def calcAvg(self, boardMeas):
    #loop over the measurements, average 
    boardResult = {}
    for board_key in boardMeas.keys() :
      chMeas = boardMeas[board_key]
      if board_key not in boardResult:
        boardResult[board_key] = {}

      #loop over the pulser dacs
      for ch_key in chMeas.keys() :
        amp = ch_key
        ampMeas = chMeas[amp]
        pedMeas = []
        rmsMeas = []
        maxMeas = []
        #loop over the repeated measurements made at the same DAC
        for meas in ampMeas :
          pedMeas.append(meas['ped'])
          rmsMeas.append(meas['rms'])
          maxMeas.append(meas['max'])
        #average or combine results
        pedVal = np.mean(pedMeas)
        rmsVal = np.mean(rmsMeas)
        maxVal = int( np.amax(maxMeas) )
        #store average value in results dict
        if amp not in boardResult[board_key] :
          boardResult[board_key][amp] = {}
        boardResult[board_key][amp]['ped'] = pedVal
        boardResult[board_key][amp]['rms'] = rmsVal
        boardResult[board_key][amp]['max'] = maxVal
    return boardResult

  #finally make some plots using info in results dict
  def makePlots(self,boardResult, board_key, titleTextBase = "Example", figureName = "fig", low=0,high=60000):
    if board_key not in boardResult:
      return None

    chResult = boardResult[board_key]
    amps = []
    peds = []
    rmss = []
    maxs = []
    peaks = []
    for amp in chResult.keys():
      print(amp,"\t",chResult[amp])
      amps.append(amp)
      peds.append(chResult[amp]['ped'])
      rmss.append(chResult[amp]['rms'])
      maxs.append(chResult[amp]['max'])
      peaks.append( chResult[amp]['max'] - chResult[amp]['ped'])

    #fig = plt.figure()
    #ax = fig.add_axes()
    plt.plot(amps, peaks,'.')
    plt.xlim(low,high)
    plt.xlabel('Pulser DAC [DAC code]', horizontalalignment='right', x=1.0)
    plt.ylabel('Pulse Height [ADC counts]')
    plt.title(titleTextBase + " : Pulse Height count vs Pulser DAC")
    #plt.savefig(figureName)
    plt.show() #plt.clf()
    return None

  def showPlots(self):
    plt.show()

  def processResults(self):
    if self.runResults == None :
      return None
    fileName = self.fileName
    boardName= self.boardName
    boardMeas = self.collect( self.runResults )
    boardResult = self.calcAvg( boardMeas )

    self.makePlots(boardResult,('coluta1', 'channel1'),boardName + " COLUTA 1 Low Gain",boardName+"_coluta1_lg",0,70000)
    self.makePlots(boardResult,('coluta1', 'channel2'),boardName + " COLUTA 1 High Gain",boardName+"_coluta1_hg",0,5000)
    self.makePlots(boardResult,('coluta2', 'channel1'),boardName + " COLUTA 2 High Gain",boardName+"_coluta2_hg",0,5000)
    self.makePlots(boardResult,('coluta2', 'channel2'),boardName + " COLUTA 2 Low Gain",boardName+"_coluta2_lg",0,70000)

  def processFile(self):
    #open list of measurements, get all results
    with open(self.fileName) as json_data:
      self.runResults = json.load(json_data)

def main():
  if len(sys.argv) < 2 :
    print("ERROR, program requires filename as argument")
    return

  fileName = sys.argv[1]
  boardName = "Board "
  if len(sys.argv) == 3 :
    boardName = sys.argv[2]

  atbPlotResults = ATB_PLOT_RESULTS(fileName)
  atbPlotResults.fileName = fileName
  atbPlotResults.boardName = boardName
  atbPlotResults.processFile()
  atbPlotResults.processResults()

#-------------------------------------------------------------------------
if __name__ == "__main__":
  main()
