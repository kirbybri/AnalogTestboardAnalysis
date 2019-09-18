import h5py
import numpy as np
from math import *
import matplotlib.pyplot as plt
import argparse
import glob
from scipy import stats
#from helperfunctions import *
import pickle
#from itertools import product
#from collections import defaultdict
import json
import sys

def plot_wf(wf_data,a=0,b=1000):
   # plot waveform samples
   plt.plot(wf_data[a:b],'.-')
   #plt.plot(wf_data,'.-')
   plt.xlabel('samples', horizontalalignment='right', x=1.0)
   plt.ylabel('ADC counts')
   plt.title("Example Waveform")
   plt.show()
   #plt.clf()

#interlace code from testhdf5_elena.py
def interlace(block_length, pulse_length, samples):
  new_samples = np.empty(block_length)
  for s in range(block_length-1):
    new_samples[s] = samples[(s*pulse_length)%(block_length-1)]
  new_samples[block_length-1] = samples[block_length-1]
  return new_samples

def processMeasurement(file_key, meas):
  print( "Measurement","\t",file_key)
  #print( "Measurement keys","\t", meas.keys() ) #group keys
  #print( "Measurement attr keys","\t", meas.attrs.keys() ) #group key
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
    #print("\t", "Group","\t", group_key )
    #print("\t", "Group keys""\t",mysubgroup.keys() )
    #print("\t", "Group attr keys","\t",mysubgroup.attrs.keys() )
    for subgroup_key in mysubgroup.keys() :
        mysubsubgroup = mysubgroup[subgroup_key] #group object
        #print("\t\t", "Subgroup","\t", subgroup_key)
        #print("\t\t", "Subgroup keys","\t",mysubsubgroup.keys() )
        #print("\t\t", "Subgroup attr keys","\t",mysubsubgroup.attrs.keys() )
        if 'samples' in mysubsubgroup :
          #print( mysubsubgroup['samples'] )
          myds = mysubsubgroup['samples'] #dataset object
          #print("\t\t\t", file_key, "\t", group_key, "\t", subgroup_key, "\t", pulser_amp )

          if myds.len() < 4000 :
            continue

          pedVal = np.mean(myds[0:50])
          pedRms = np.std(myds[0:50])
          maxVal = int(np.amax(myds[50:75]))

          #skip waveforms with no pulses
          if maxVal - pedVal < 25 :
            continue
          
          #for samp in range(0, myds.len() ):
          #  print(samp,"\t",myds[samp])
          #intWf = interlace(block_length, pulse_length, myds)
          #pedVal = np.mean(intWf[0:400])
          #pedRms = np.std(intWf[0:400])
          #maxVal = np.amax(intWf[400:500])
          
          #store results
          resultsDict = {}
          resultsDict['coluta'] = group_key
          resultsDict['channel'] = subgroup_key
          resultsDict['pulser'] = pulser_amp
          resultsDict['ped'] = pedVal
          resultsDict['rms'] = pedRms
          resultsDict['max'] = maxVal
          #print( resultsDict )
          resultsList.append( resultsDict )
          #print( "\t", pedVal ,"\t", pedRms,"\t", maxVal)
          #plot_wf(myds,0,200)
          #plot_wf(intWf)

  #if len(resultsList) == 0 :
  #  return None
  return resultsList
    
def processFile(hdf5File):
  #check for required attributes
  #print( "FILE Keys ", "\t", hdf5File.keys() )
  #print( "FILE attr Keys ", "\t", hdf5File.attrs.keys() )

  #extract run # from file name
  print( hdf5File.filename )
  nameSplit = hdf5File.filename.split('_')
  if len(nameSplit) < 2 :
    return
  if nameSplit[0] != 'Run' :
    return
  runNo = nameSplit[1]

  #get board serial #
  serialNo = None
  if 'serial_number' in hdf5File.attrs :
    serialNo = hdf5File.attrs['serial_number']

  runResultsDict = {}
  runResultsDict['file'] = hdf5File.filename
  runResultsDict['run'] = runNo
  runResultsDict['serial'] = serialNo

  #loop through measurements
  measResultsDict = {}
  for file_key in hdf5File.keys() :
    #print( file_key ) #file object key
    meas = hdf5File[file_key] #group object
    measResults = processMeasurement(file_key, meas)
    if measResults != None :
      measResultsDict[file_key] = measResults

  runResultsDict['results'] = measResultsDict
  #print("RESULTS")
  #print( runResultsDict )

  jsonFileName = 'results_' + runNo + '.json'
  with open( jsonFileName , 'w') as outfile:
    json.dump( runResultsDict, outfile, indent=4)

def main():
  print("HELLO")

  if len(sys.argv) != 2 :
    print("ERROR, program requires filename as argument")
    return

  fileName = sys.argv[1]
  hdf5File = h5py.File(fileName, "r") #file object
  processFile(hdf5File)
  return

#-------------------------------------------------------------------------
if __name__ == "__main__":
  main()
