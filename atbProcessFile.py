import h5py
import numpy as np
from math import *
import matplotlib.pyplot as plt
import json
import sys

#BEGIN ATB_PLOT_RESULTS CLASS
class ATB_PROCESS_FILE(object):

  #__INIT__#
  def __init__(self,fileName=None):
    self.fileName = fileName
    self.hdf5File = None
    self.runResultsDict = None
    self.doInterlace = True
    self.doPlot = False
    self.SAR_weights_coluta1_ch1 = None
    self.SAR_weights_coluta2_ch2 = None
    self.SAR_weights_coluta1_ch1 = None
    self.SAR_weights_coluta2_ch2 = None
    self.pedRange = [0,400]
    self.peakRange = [400,500]

  # plot waveform samples
  def plot_wf(self,wf_data,a=0,b=1000):   
    plt.plot(wf_data[a:b],'.-')#plt.plot(wf_data,'.-')#
    plt.xlabel('samples', horizontalalignment='right', x=1.0)
    plt.ylabel('ADC counts')
    plt.title("Example Waveform")
    plt.show() #plt.clf()

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
    #skip waveforms with no pulses
    if maxVal - pedVal < 25 :
      return None

    #do interlacing, get refined pulse measurements
    if self.doInterlace :
      samples = samples[n_pulse_skips*pulse_length :]
      samples = self.interlace(block_length, pulse_length, samples)
      #pedVal = np.mean( samples[pedRange[0]:pedRange[1]] )
      #pedRms = np.std( samples[pedRange[0]:pedRange[1]] )
      #maxVal = np.amax( samples[peakRange[0]:peakRange[1]] )
      pedVal = np.mean(samples[0:100])
      pedRms = np.std(samples[0:100])
      maxVal = np.amax(samples[125:300])

    #store results in dict
    resultsDict = {}
    resultsDict['coluta'] = colutaNum
    resultsDict['channel'] = channelNum
    resultsDict['pulser'] = pulserAmp
    resultsDict['ped'] = pedVal
    resultsDict['rms'] = pedRms
    resultsDict['max'] = maxVal
    #resultsDict['wf'] = intWf.tolist()
    if self.doPlot :
      print( 'ped\t', pedVal )
      print( 'rms\t', pedRms )
      print( 'max\t', maxVal )
      self.plot_wf(samples) #self.plot_wf(samples,0,200)
    return resultsDict

  #analysis process applied to each "measurement"
  def processMeasurement(self,file_key, meas):
    print( "Measurement","\t",file_key)
    #print( meas.attrs.keys() )
    #check for required attributes
    if 'awg_freq' not in meas.attrs :
      print("Measurement is missing required metadata: awg_freq")
      return None
    if 'pulse_length' not in meas.attrs :
      print("Measurement is missing required metadata: pulse_length")
      return None
    if 'pulser_amp' not in meas.attrs :
      print("Measurement is missing required metadata: pulser_amp")
      return None
    if 'run_type' not in meas.attrs :
      print("Measurement is missing required metadata: run_type")
      return None
    #ignore misconfigured runs
    if meas.attrs['run_type'] == 'sine' :
      return None
    
    #get required attributes
    adc_freq = 40
    awg_freq = meas.attrs["awg_freq"]
    pulser_amp = int(meas.attrs['pulser_amp'])
    pulse_length = meas.attrs['pulse_length']
    n_offset = 1
    block_length = int(((awg_freq/np.abs(n_offset))/adc_freq)*pulse_length)
    n_pulse_skips = 0
    if meas.attrs['run_type'] == 'pulse' :
      n_pulse_skips = 22
      pulser_amp = float(meas.attrs['pulse_amplitude'])
      self.pedRange = [0,100]
      self.peakRange = [125,300]

    #if 'SAR_weights' not in mysubsubgroup.attrs :
      #print("Channel is missing required metadata: SAR_weights")
      #continue

    #loop over measurement group members, process waveform data
    resultsList = []
    for group_key in meas.keys() :
      mysubgroup = meas[group_key] #group object
      for subgroup_key in mysubgroup.keys() :
        mysubsubgroup = mysubgroup[subgroup_key] #group object
        colutaNum = group_key
        channelNum = subgroup_key
        #if 'SAR_weights' not in mysubsubgroup.attrs :
        #  print("Channel is missing required metadata: SAR_weights")
        #  continue
        #sarWeights = mysubsubgroup.attrs['SAR_weights']
        #if 'samples' not in mysubsubgroup :
        #  print("Channel is missing required dataset: samples")
        #  continue
        #samples = mysubsubgroup['samples']
        if 'raw_data' not in mysubsubgroup :
          print("Channel is missing required dataset: raw_data")
          continue
        sarWeights = None
        if colutaNum == 'coluta1' and channelNum == 'channel1' :
          sarWeights = self.SAR_weights_coluta1_ch1
        if colutaNum == 'coluta1' and channelNum == 'channel2' :
          sarWeights = self.SAR_weights_coluta1_ch2
        if colutaNum == 'coluta2' and channelNum == 'channel1' :
          sarWeights = self.SAR_weights_coluta2_ch1
        if colutaNum == 'coluta2' and channelNum == 'channel2' :
          sarWeights = self.SAR_weights_coluta2_ch2

        raw_data = mysubsubgroup['raw_data'] #dataset object
        samples = np.dot(raw_data, sarWeights)
        resultsDict = self.processWaveform(samples,colutaNum,channelNum,pulser_amp,block_length, pulse_length,n_pulse_skips)
        if resultsDict != None :
          resultsList.append( resultsDict )
    return resultsList

  #extract run # from file name
  def getRunNo(self,fileName):
    pathSplit = fileName.split('/')
    nameSplit = pathSplit[-1].split('_')
    if len(nameSplit) < 2 :
      return None
    if nameSplit[0] != 'Run' :
      return None
    return nameSplit[1]

  #run analysis on input file
  def processFile(self):
    if self.fileName == None:
      return None
    self.hdf5File = h5py.File(self.fileName, "r") #file object
    #check for required attributes
    print( "FILE attr Keys ", "\t", self.hdf5File.attrs.keys() )
    runNo = self.getRunNo( self.hdf5File.filename )
    if runNo == None :
      print("ERROR: couldn't get run number")
    #get board serial #
    serialNo = None
    if 'serial_number' in self.hdf5File.attrs :
      serialNo = self.hdf5File.attrs['serial_number']
    #get SAR weights
    if 'coluta1_channel1_SAR_weights' not in self.hdf5File.attrs :
      print("HDF5 file missing attribute: coluta1_channel1_SAR_weights")
      return None
    if 'coluta1_channel2_SAR_weights' not in self.hdf5File.attrs :
      print("HDF5 file missing attribute: coluta1_channel2_SAR_weights")
      return None
    if 'coluta2_channel1_SAR_weights' not in self.hdf5File.attrs :
      print("HDF5 file missing attribute: coluta2_channel1_SAR_weights")
      return None
    if 'coluta2_channel2_SAR_weights' not in self.hdf5File.attrs :
      print("HDF5 file missing attribute: coluta2_channel2_SAR_weights")
      return None
    self.SAR_weights_coluta1_ch1 = self.hdf5File.attrs['coluta1_channel1_SAR_weights']
    self.SAR_weights_coluta1_ch2 = self.hdf5File.attrs['coluta1_channel2_SAR_weights']
    self.SAR_weights_coluta2_ch1 = self.hdf5File.attrs['coluta2_channel1_SAR_weights']
    self.SAR_weights_coluta2_ch2 = self.hdf5File.attrs['coluta2_channel2_SAR_weights']

    self.runResultsDict = {}
    self.runResultsDict['file'] = self.hdf5File.filename
    self.runResultsDict['run'] = runNo
    self.runResultsDict['serial'] = serialNo

    #loop through measurements, store results in dict
    measResultsDict = {}
    for file_key in self.hdf5File.keys() :
      measResults = self.processMeasurement(file_key, self.hdf5File[file_key] )
      if measResults != None :
        measResultsDict[file_key] = measResults
  
    self.runResultsDict['results'] = measResultsDict
    return

  #output results dict to json file
  def outputFile(self):
    if self.runResultsDict == None:
      return None
    pathSplit = self.fileName.split('/')[-1]
    jsonFileName = 'output_runAnalysis_' + pathSplit + '.json'
    with open( jsonFileName , 'w') as outfile:
      json.dump( self.runResultsDict, outfile, indent=4)

def main():
  print("HELLO")
  if len(sys.argv) != 2 :
    print("ERROR, program requires filename as argument")
    return
  fileName = sys.argv[1]
  atbProcessFile = ATB_PROCESS_FILE(fileName)
  atbProcessFile.processFile()
  atbProcessFile.outputFile()

  return

#-------------------------------------------------------------------------
if __name__ == "__main__":
  main()
