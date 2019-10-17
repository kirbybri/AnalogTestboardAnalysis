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
    self.SAR_weights_coluta1_ch1 = None
    self.SAR_weights_coluta2_ch2 = None
    self.SAR_weights_coluta1_ch1 = None
    self.SAR_weights_coluta2_ch2 = None

  #analysis process applied to each "measurement"
  def processMeasurement(self, meas):
    #loop over measurement group members, process waveform data
    resultsList = []
    for group_key in meas.keys() :
      mysubgroup = meas[group_key] #group object
      for subgroup_key in mysubgroup.keys() :
        mysubsubgroup = mysubgroup[subgroup_key] #group object
        colutaNum = group_key
        channelNum = subgroup_key
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
        resultsDict = {'coluta' : colutaNum, 'channel' : channelNum, 'wf' : samples.tolist()}
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

  def initSarWeights(self) :
    if self.hdf5File == None :
      return None
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
    return True

  def getReqAttrs(self,meas):
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
    if meas.attrs['run_type'] == 'sine' :
      print("Measurement has invalid run_type")
      return None
    if meas.attrs['run_type'] == 'pulse' and 'pulse_amplitude' not in meas.attrs :
      print("Measurement is missing required metadata: pulse_amplitude")
      return None
    pulse_amplitude = None
    if meas.attrs['run_type'] == 'pulse' :
      pulse_amplitude = float(meas.attrs['pulse_amplitude'])
    return { 'awg_freq' : int(meas.attrs["awg_freq"]), 'pulser_amp': int(meas.attrs['pulser_amp']), 'pulse_length': int(meas.attrs['pulse_length']),
             'run_type' : meas.attrs['run_type'], 'pulse_amplitude': pulse_amplitude }

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
    self.initSarWeights()

    self.runResultsDict = {}
    self.runResultsDict['file'] = self.hdf5File.filename
    self.runResultsDict['run'] = runNo
    self.runResultsDict['serial'] = serialNo

    #loop through measurements, store results in dict
    measResultsDict = {}
    for file_key in self.hdf5File.keys() :
      print( "Measurement","\t",file_key)
      meas = self.hdf5File[file_key]
      measAttrs = self.getReqAttrs(meas)
      if measAttrs == None :
        print("Missing required attribute, will not process measurement")
        continue
      measData = self.processMeasurement(meas)
      if measData == None :
        print("Missing waveform data, will not process measurement")
        continue
      measResultsDict[file_key] = {'attrs':measAttrs,'data':measData}
  
    self.runResultsDict['results'] = measResultsDict
    return

  #output results dict to json file
  def outputFile(self):
    if self.runResultsDict == None:
      return None
    pathSplit = self.fileName.split('/')[-1]
    jsonFileName = 'output_atbProcessFile_' + pathSplit + '.json'
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

#-------------------------------------------------------------------------
if __name__ == "__main__":
  main()
