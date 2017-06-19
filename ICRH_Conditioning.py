# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 13:19:21 2017

@author: JH218595

Data files (.csv) are located on dfci:/media/ssd/Conditionnement/
"""
import pandas as pd
import matplotlib.pyplot as plt

def read_conditoning_data(filename):
    """
    Import and return the ICRH Conditioning data into a pandas DataFrame
    """
    data = pd.read_csv(filename, delimiter='\t', skiprows=18, 
                names=('Temps',
                       'PiG','PrG','PiD','PrD',
                       'V1','V2','V3','V4', 
                       'Ph(V1-V3)','Ph(V2-V4)','Ph(Pig-Pid)', 'bidon'),
                index_col='Temps')
    return data 

def read_conditioning_metadata(filename):
    """
    Import and return the ICRH Conditioning metadata into a dictionary
    """
    para_dic = {}
    with  open(filename,'r') as cmt_file:    # open file
        for line in cmt_file:    # read each line
            if line[0] == '#':    # check the first character
                line = line[1:]    # remove first '#'
                para = line.split('=')     # seperate string by '='
                if len(para) == 2:
                    para_dic[ para[0].strip()] = para[1].strip()
    return para_dic    

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

if __name__ == '__main__':
    import ICRH_FileIO as io
    # Copy the recent data file into the local directory
    remote_file_list = io.list_remote_files()
    io.copy_remote_files_to_local(remote_file_list)
    
    # Plot the last data file. 
    local_file_list = io.list_local_files()
    data = read_conditoning_data(local_file_list[-1])
    plot_conditionning_data(data)



