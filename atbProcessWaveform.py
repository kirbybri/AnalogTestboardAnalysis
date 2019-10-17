import h5py
import numpy as np
from math import *
import matplotlib.pyplot as plt
import json
import sys

class ATB_PROCESS_WAVEFORM(object):

  #__INIT__#
  def __init__(self,fileName=None):
    self.fileName = fileName
    self.runResultsDict = None
    self.doInterlace = True
    self.doPlot = False
    self.saveWf = True

  # plot waveform samples
  def plot_wf(self,wf_data,a=0,b=1000):
    plt.plot(wf_data[a:b],'.-')#plt.plot(wf_data,'.-')#
    plt.xlabel('samples', horizontalalignment='right', x=1.0)
    plt.ylabel('ADC counts')
    plt.title("Example Waveform")
    plt.show() #plt.clf()

  #average the measurements
  def averageMeasurements(self):
    if 'results' not in self.runResultsDict :
      return None
    results = self.runResultsDict['results']

    boardMeas = {}
    for asic in results :
      asicInfo = results[asic]
      if asic not in boardMeas:
        boardMeas[asic] = {}
      for ch in asicInfo :
        chanInfo = asicInfo[ch]
        if ch not in boardMeas[asic] :
          boardMeas[asic][ch] = {}
        for amp in chanInfo :
          if amp not in boardMeas[asic][ch]:
            boardMeas[asic][ch][amp] = {}
          ampInfo = chanInfo[amp]
          #have list of readouts, average over results
          pedMeas = []
          rmsMeas = []
          maxMeas = []
          minMeas = []
          wfDict = {}
          for measNum, meas in enumerate(ampInfo) :
            pedMeas.append(meas['ped'])
            rmsMeas.append(meas['rms'])
            maxMeas.append(meas['max'])
            minMeas.append(meas['min'])
            if 'wf' in meas :
              for sampNum, samp in enumerate(meas['wf']) :
                if sampNum not in wfDict :
                  wfDict[sampNum] = []
                wfDict[sampNum].append(samp)
          #average or combine results
          pedVal = np.mean(pedMeas)
          rmsVal = np.mean(rmsMeas)
          #maxVal = int( np.amax(maxMeas) )
          maxVal = np.mean(maxMeas)
          minVal = np.mean(minMeas)
          avgWf = []
          for sampNum in range(0,len(wfDict),1):
            if sampNum not in wfDict :
              continue
            avgVal = np.mean(wfDict[sampNum])
            avgWf.append(avgVal)
          #save results
          boardMeas[asic][ch][amp]['ped'] = pedVal
          boardMeas[asic][ch][amp]['rms'] = rmsVal
          boardMeas[asic][ch][amp]['max'] = maxVal
          boardMeas[asic][ch][amp]['min'] = minVal
          if len(avgWf) > 0 :
            boardMeas[asic][ch][amp]['wf'] = avgWf
    self.runResultsDict['results'] = boardMeas

  #reorganize measurement data by ASIC, ch and pulser DAC
  def collect(self):
    if 'results' not in self.runResultsDict :
      return None
    results = self.runResultsDict['results']

    #loop over the measurements, organize by ASIC + ch, dac
    boardMeas = {}
    for results_key in results.keys() :
      meas = results[results_key]
      for result in meas :
        asic = result['coluta']
        ch = result['channel']
        if asic not in boardMeas:
          boardMeas[asic] = {}
        if ch not in boardMeas[asic] :
          boardMeas[asic][ch] = {}
        amp = result['pulser']
        if amp not in boardMeas[asic][ch] :
          boardMeas[asic][ch][amp] = []
        readoutDict = { 'ped' : result['ped'] , 'rms' : result['rms'], 'max' : result['max'], 'min' : result['min'] }
        if 'wf' in result :
          readoutDict['wf'] = result['wf']
        boardMeas[asic][ch][amp].append( readoutDict )
    self.runResultsDict['results'] = boardMeas

  #interlace code from testhdf5_elena.py
  def interlace(self,block_length, pulse_length, samples):
    new_samples = np.empty(block_length)
    for s in range(block_length-1):
      new_samples[s] = samples[(s*pulse_length)%(block_length-1)]
    new_samples[block_length-1] = samples[block_length-1]
    return new_samples

  #process waveform
  def processWaveform(self,samples, colutaNum, channelNum, pulserAmp, block_length, pulse_length, n_pulse_skips='0'):
    if len(samples) < 4000 :
      return None
    #get initial pulse measurements
    pedVal = np.mean(samples[0:50])
    pedRms = np.std(samples[0:50])
    maxVal = int(np.amax(samples[50:75]))
    minVal = int(np.amin(samples[58:85]))

    #do interlacing, get refined pulse measurements
    if self.doInterlace :
      samples = samples[n_pulse_skips*pulse_length :]
      samples = self.interlace(block_length, pulse_length, samples)
      pedVal = np.mean(samples[0:100])
      pedRms = np.std(samples[0:100])
      maxVal = np.amax(samples[125:300])
      minVal = np.amin(samples[490:950])  

    #store results in dict
    resultsDict = {'coluta':colutaNum,'channel':channelNum,'pulser':pulserAmp,'ped':pedVal,'rms':pedRms,'max':maxVal,'min':minVal}
    if self.saveWf :
      resultsDict['wf'] = samples.tolist()
    if self.doPlot :
      print( 'colutaNum\t', colutaNum)
      print( 'channelNum\t', channelNum)
      print( 'pulserAmp\t', pulserAmp )
      print( 'ped\t', pedVal )
      print( 'rms\t', pedRms )
      print( 'max\t', maxVal )
      self.plot_wf(samples) #self.plot_wf(samples,0,200)
    return resultsDict

  #analysis process applied to each "measurement"
  def processChannel(self, measAttrs,chData):    
    #get required attributes
    adc_freq = 40
    awg_freq = measAttrs["awg_freq"]
    pulser_amp = measAttrs['pulser_amp']
    pulse_length = measAttrs['pulse_length']
    n_offset = 1
    block_length = int(((awg_freq/np.abs(n_offset))/adc_freq)*pulse_length)
    n_pulse_skips = 0
    if measAttrs['run_type'] == 'pulse' :
      n_pulse_skips = 22
      pulser_amp = measAttrs['pulse_amplitude']

    #loop over measurement group members, process waveform data
    colutaNum = chData['coluta']
    channelNum = chData['channel']
    samples = chData['wf']
    resultsDict = self.processWaveform(samples,colutaNum,channelNum,pulser_amp,block_length,pulse_length,n_pulse_skips)
    return resultsDict

  #process measurements
  def processMeasurements(self):
    if self.runResultsDict == None:
      return None
    if "results" not in self.runResultsDict :
      return None
    runMeas = self.runResultsDict['results']
    #loop over measurements
    allResultsDict = {}
    for measKey in runMeas :
      meas = runMeas[measKey]
      if 'attrs' not in meas or 'data' not in meas :
        continue
      measAttrs = meas['attrs']
      measData = meas['data']
      #each measurement has data from multiple channels
      resultsList = []
      for chData in measData :
        chResultsDict = self.processChannel(measAttrs,chData)
        if chResultsDict != None :
          resultsList.append( chResultsDict )
      allResultsDict[measKey] = resultsList
    self.runResultsDict['results'] = allResultsDict

  #run analysis on input file
  def processFile(self):
    if self.fileName == None:
      return None
    #open list of measurements, get all results
    with open(self.fileName) as json_data:
      self.runResultsDict = json.load(json_data)

  #output results dict to json file
  def outputFile(self):
    if self.runResultsDict == None:
      return None
    pathSplit = self.fileName.split('/')[-1]
    jsonFileName = 'output_atbProcessWaveform_' + pathSplit + '.json'
    with open( jsonFileName , 'w') as outfile:
      json.dump( self.runResultsDict, outfile, indent=4)

def main():
  print("HELLO")
  if len(sys.argv) != 2 :
    print("ERROR, program requires filename as argument")
    return
  fileName = sys.argv[1]
  atbProcessWaveform = ATB_PROCESS_WAVEFORM(fileName)
  atbProcessWaveform.processFile()
  atbProcessWaveform.processMeasurements()
  atbProcessWaveform.collect()
  atbProcessWaveform.averageMeasurements()
  atbProcessWaveform.outputFile()

#-------------------------------------------------------------------------
if __name__ == "__main__":
  main()
