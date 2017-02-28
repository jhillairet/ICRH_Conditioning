# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 13:19:21 2017

@author: JH218595

Data files (.csv) are located on dfci:/media/ssd/Conditionnement/
"""
import subprocess
import os
import glob
import pandas as pd
import matplotlib.pyplot as plt


def list_remote_files(remote_path='/media/ssd/Conditionnement/'):
    """
    Returns a list of the remote files (.csv) located in the remote acquisition computer.
    """
    ls = subprocess.Popen(['ssh', 'dfci@dfci', 'ls', remote_path ], 
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          universal_newlines=True) # deals with Python3 string
    out, err =  ls.communicate()
    remote_file_list = out.split(sep='\n')
    remote_file_list.pop() # The last one is a dummy ''
    return remote_file_list

def list_local_files(local_data_path = 'data/'):
    """ 
    Returns the list of local files (.csv)
    """
    local_file_list = [os.path.basename(x) for x in glob.glob(local_data_path+'/*.csv')]    
    return local_file_list

def copy_remote_files_to_local(remote_file_list, local_data_path = 'data/', 
                               remote_data_path='/media/ssd/Conditionnement/'):
    """
    Copy a list of remote files into the local directory, only if the files do
    not exist locally.
    """
    # List the files allready present in the local directory
    local_file_list = list_local_files(local_data_path)
    # Copy files through scp when the file does not exist locally
    for file in remote_file_list:
        if file not in local_file_list:
            print('Copying file {}'.format(os.path.join(remote_data_path, file)))
            # Use call() instead of Popen() in order to block and not continue until end of copying
            cp=subprocess.call(['scp', 'dfci@dfci:'+os.path.join(remote_data_path, file), local_data_path],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True)

        
        
def read_conditoning_data(filename):
    """
    Import and return the ICRH Conditioning data into a pandas DataFrame
    """
    data = pd.read_csv('data/2017-02-27_14-58-03.csv', delimiter='\t', skiprows=16, 
                names=('Temps','PiG','PrG','PiD','PrD','V1','V2','V3','V4'),
                index_col='Temps')
    return data 


def plot_conditionning_data(data):
    """
    Plot the ICRH Conditoning data into a single figure. 
    Expect a pandas DataFrame as input
    """
    fig, ax = plt.subplots(2,2, sharex=True)
    time = data.index/1e3 # display time in ms
    ax[0,0].plot(time, data.PiG/10, time, data.PrG/10)
    ax[0,1].plot(time, data.PiD/10, time, data.PrD/10)
    ax[1,0].plot(time, data.V1, time, data.V2)
    ax[1,1].plot(time, data.V3, time, data.V4)
    ax[1,0].set_xlabel('Time [ms]')
    ax[1,1].set_xlabel('Time [ms]')
    ax[0,0].set_ylabel('Power [kW]')
    ax[1,0].set_ylabel('Voltage [V]')
    plt.tight_layout()


# Copy the recent data file into the local directory
remote_file_list = list_remote_files()
copy_remote_files_to_local(remote_file_list)

# Plot the last data file. 
local_file_list = list_local_files()
data = read_conditoning_data(local_file_list[-1])
plot_conditionning_data(data)



