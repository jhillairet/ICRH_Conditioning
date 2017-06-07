# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 13:19:21 2017

@author: JH218595

Data files (.dat) are located on dfci:/media/ssd/Fast_Data/
"""
import os
import pandas as pd
import matplotlib.pyplot as plt

import ICRH_FileIO as io

def filter_by_shot(file_list, shot):
    '''
    Return the Fast Data file names associated to a given shot number
    '''
    shot_file_list = []
    for file in file_list:
        fn_split = file.split('_')
        if fn_split[1] == str(shot):
            shot_file_list.append(file)
    return shot_file_list


def read_fast_data_7851(filename):
    '''
    Import and return the ICRH Conditioning data into a pandas DataFrame
    
    Phase Fast Data from the NI 7853 board
    Time in µs
    '''
    phases = pd.read_csv(os.path.join('data/Fast_Data', filename), delimiter='\t',
                     index_col=7, 
                     names=('Ph1', 'Ph2', 'Ph3', 'Ph4', 'Ph5', 'Ph6', 'Ph7', ''))
    return phases
    
def read_fast_data_7853(filename):
    """
    Import and return the ICRH Conditioning data into a pandas DataFrame
    
    Voltage and Power Fast Data from the NI 7851 board. 
    Time in µs
    """
    amplitudes = pd.read_csv(os.path.join('data/Fast_Data',filename), delimiter='\t',
                       index_col=8,
                       names=('V1', 'V2', 'V3', 'V4', 
                              'PiG', 'PrG', 'PiD', 'PrD', 
                              'CGH', 'CGB', 'CDH', 'CDB', ''))
    return amplitudes 


if __name__ == '__main__':
    # Copy the recent data file into the local directory
    remote_files = io.list_remote_files(remote_path='/media/ssd/Fast_Data/')
    
    #files_to_copy = filter_by_shot(all_fast_data_remote_files, 50)
    
    io.copy_remote_files_to_local(remote_files, 
                                  local_data_path='data/Fast_Data', 
                                  remote_data_path='/media/ssd/Fast_Data/', 
                                  nb_last_file_to_download=50)
    
    # Plot the last data file. 
    #local_file_list = io.list_local_files()



