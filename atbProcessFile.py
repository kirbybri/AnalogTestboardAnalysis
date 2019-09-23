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
    self.runResultsDict = None

  # plot waveform samples
  def plot_wf(self,wf_data,a=0,b=1000):   
    plt.plot(wf_data[a:b],'.-') #plt.plot(wf_data,'.-')
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

  #analysis process applied to each "measurement"
  def processMeasurement(self,file_key, meas):
    print( "Measurement","\t",file_key)
    #check for required attributes
    if 'awg_freq' not in meas.attrs :
      print("HDF5 group is missing required metadata: awg_freq")
      return None
    if 'pulse_length' not in meas.attrs :
      print("HDF5 group is missing required metadata: pulse_length")
      return None
    if 'pulser_amp' not in meas.attrs :
      print("HDF5 group is missing required metadata: pulser_amp")
      return None
    if 'run_type' not in meas.attrs :
      print("HDF5 group is missing required metadata: run_type")
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

    #loop over measurement group members, store result dicts in a list
    resultsList = []
    for group_key in meas.keys() :
      mysubgroup = meas[group_key] #group object
      for subgroup_key in mysubgroup.keys() :
        mysubsubgroup = mysubgroup[subgroup_key] #group object
        #check if there is a waveform object
        if 'samples' in mysubsubgroup :
          myds = mysubsubgroup['samples'] #dataset object
          #require minimum # samples in waveform data
          if myds.len() < 4000 :
            continue
          #get initial pulse measurements
          pedVal = np.mean(myds[0:50])
          pedRms = np.std(myds[0:50])
          maxVal = int(np.amax(myds[50:75]))

          #skip waveforms with no pulses
          if maxVal - pedVal < 25 :
            continue
          
          #do interlacing, get refined pulse measurements
          intWf = self.interlace(block_length, pulse_length, myds)
          pedVal = np.mean(intWf[0:400])
          pedRms = np.std(intWf[0:400])
          maxVal = np.amax(intWf[400:500])
          
          #store results in dict
          resultsDict = {}
          resultsDict['coluta'] = group_key
          resultsDict['channel'] = subgroup_key
          resultsDict['pulser'] = pulser_amp
          resultsDict['ped'] = pedVal
          resultsDict['rms'] = pedRms
          resultsDict['max'] = maxVal
          resultsList.append( resultsDict )
          self.plot_wf(intWf) #self.plot_wf(myds,0,200)
          
    #if len(resultsList) == 0 :
    #  return None
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
    hdf5File = h5py.File(self.fileName, "r") #file object
    #check for required attributes
    #print( "FILE Keys ", "\t", hdf5File.keys() )
    #print( "FILE attr Keys ", "\t", hdf5File.attrs.keys() )
    runNo = self.getRunNo( hdf5File.filename )
    if runNo == None :
      print("ERROR: couldn't get run number")

    #get board serial #
    serialNo = None
    if 'serial_number' in hdf5File.attrs :
      serialNo = hdf5File.attrs['serial_number']

    self.runResultsDict = {}
    self.runResultsDict['file'] = hdf5File.filename
    self.runResultsDict['run'] = runNo
    self.runResultsDict['serial'] = serialNo

    #loop through measurements, store results in dict
    measResultsDict = {}
    for file_key in hdf5File.keys() :
      measResults = self.processMeasurement(file_key, hdf5File[file_key] )
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
