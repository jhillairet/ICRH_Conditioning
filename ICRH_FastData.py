# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 13:19:21 2017

@author: JH218595

Data files (.dat) are located on dfci:/media/ssd/Fast_Data/

-	Carte 0 : 7853 de Q1 : PiG, PrG, PiD, PrD
-	Carte 1 : 7851 de Q1 : 7 mesures de phase
-	Carte 2 : 7853 de Q2 : PiG, PrG, PiD, PrD
-	Carte 3 : 7851 de Q2 : 7 mesures de phase
-	Carte 4 : 7853 de Q4 : PiG, PrG, PiD, PrD
-	Carte 5 : 7851 de Q4 : 7 mesures de phase

"""
import os
import glob
import pandas as pd
import ICRH_FileIO as io

def get_shot_filenames(shot, path='data/Fast_Data'):
    '''Returns the filenames associated to a shot number'''
    file_list = glob.glob(os.path.join(path, 'shot_'+str(shot)+'*'))
    return file_list

def get_shot_list(file_list):
    '''
    Returns the list of shot numbers for which Fast Data acquisition has been saved  
    '''
    shot_list = set()
    for file in file_list:
        shot_list.add(int(file.split('_')[1]))
    return sorted(shot_list, reverse=True)       

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
    try:
        phases = pd.read_csv(filename, delimiter='\t',
                     index_col='t', 
                     names=('Ph1', 'Ph2', 'Ph3', 'Ph4', 'Ph5', 'Ph6', 'Ph7', 't', ''))
        return phases
    except Exception as e:
        print(f'Error in reading phase (7851) file {filename}: {e}')
        return None
    
def read_fast_data_7853(filename):
    """
    Import and return the ICRH Conditioning data into a pandas DataFrame
    
    Voltage and Power Fast Data from the NI 7853 board. 
    Time in µs
    """
    try:
        amplitudes = pd.read_csv(filename, delimiter='\t',
                       index_col='t',
                       names=('PiG', 'PrG', 'PiD', 'PrD',
                              'V1', 'V2', 'V3', 'V4', 'Consigne', 't',
                               ''))
        return amplitudes
    except Exception as e:
        print(f'Error in reading amplitude (7853) file {filename}: {e}')
        return None

class FastData():
    '''Fast Data structure'''
    def __init__(self, shot):
        self.shot = shot
        self.shot_files = get_shot_filenames(shot)

        for filename in self.shot_files:
            print(f'Reading file {filename}')
            if '_0.dat' in filename:
                self.Q1_amplitude = read_fast_data_7853(filename)
            if '_1.dat' in filename:
                self.Q1_phase = read_fast_data_7851(filename)
            if '_2.dat' in filename:
                self.Q2_amplitude = read_fast_data_7853(filename)
            if '_3.dat' in filename:
                self.Q2_phase = read_fast_data_7851(filename)
            if '_4.dat' in filename:
                self.Q4_amplitude = read_fast_data_7853(filename)
            if '_5.dat' in filename:
                self.Q4_phase = read_fast_data_7851(filename)


if __name__ == '__main__':
    # Copy the recent data file into the local directory
    remote_files = io.list_remote_files(remote_path='/home/dfci/media/ssd/Fast_Data/')
    #files_to_copy = filter_by_shot(all_fast_data_remote_files, 50)
    
    io.copy_remote_files_to_local(remote_files, 
                                  local_data_path='data/Fast_Data', 
                                  remote_data_path='/home/dfci/media/ssd/Fast_Data/', 
                                  nb_last_file_to_download=5)
    
    # Plot the last data file. 
    local_file_list = io.list_local_files()



