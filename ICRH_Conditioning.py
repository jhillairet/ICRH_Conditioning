# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 13:19:21 2017

@author: JH218595

Data files (.csv) are located on dfci:/media/ssd/Conditionnement/
"""
import subprocess
import os
import glob




def list_remote_files(remote_path='/media/ssd/Conditionnement/'):
    """
    Returns a list of the .csv file located in the remote acquisition computer.
    """
    ls = subprocess.Popen(['ssh', 'dfci@dfci', 'ls', remote_path ], 
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          universal_newlines=True) # deals with Python3 string
    out, err =  ls.communicate()
    remote_file_list = out.split(sep='\n')
    remote_file_list.pop() # The last one is a dummy ''
    return(remote_file_list)

def copy_remote_files_to_local(remote_file_list, local_data_path = 'data/'):
    """
    Copy a list of remote files into the local directory, only if the files do
    not exist locally.
    """
    # Get the list of local files
    local_file_list = [os.path.basename(x) for x in glob.glob(local_data_path+'/*.csv')]
    # Copy files through scp when the file does not exist locally
    for file in remote_file_list:
        if file not in local_file_list:
            print('Copying file {}'.format(os.path.join(remote_data_path, file)))
            cp=subprocess.Popen(['scp', 'dfci@dfci:'+os.path.join(remote_data_path, file), local_data_path],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True)
        
# Copy the recent data file into the local directory
remote_file_list = list_remote_files()
copy_remote_files_to_local(remote_file_list)






