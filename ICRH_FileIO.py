#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 30 11:42:47 2017

@author: JH218595
"""
import subprocess
import os
import glob

def list_remote_files(remote_path='/home/dfci/media/ssd/Conditionnement/'):
    """
    Returns a list of the remote files (.csv) located in the remote acquisition computer.
    """
    ls = subprocess.Popen(['ssh', 'dfci@dfci', 'ls', remote_path ], 
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          universal_newlines=True) # deals with Python3 string
    out, err =  ls.communicate()
    remote_file_list = out.split(sep='\n')
    remote_file_list.pop() # The last one is a dummy ''
    remote_file_list = sorted(remote_file_list, reverse=True) # Most recent first
    return remote_file_list

def list_local_files(local_data_path='data/'):
    """ 
    Returns the list of local files 
    """
    local_file_list = [os.path.basename(x) for x in glob.glob(local_data_path+'/*')]    
    # Sorted to most recent
    local_file_list = sorted(local_file_list, reverse=True)
    return local_file_list

def copy_remote_files_to_local(remote_file_list, local_data_path = 'data/', 
                               remote_data_path='/home/dfci/media/ssd/Conditionnement/', 
                               nb_last_file_to_download=1000):
    """
    Copy a list of remote files into the local directory, only if the files do
    not exist locally.
    Download only the last (most recent) nb_last_file_to_download files.
    """
    # List the files allready present in the local directory
    local_file_list = list_local_files(local_data_path)
    # Copy files through scp when the file does not exist locally
    print('Looking for new files on dfci...')
    for file in remote_file_list[:nb_last_file_to_download]:
        if file not in local_file_list:
            print('Copying file {} to {}'.format(os.path.join(remote_data_path, file), local_data_path))
            # Use call() instead of Popen() in order to block and not continue until end of copying
            cp=subprocess.call(['scp', 'dfci@dfci:'+os.path.join(remote_data_path, file), local_data_path],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True)
            
    print('OK, done.')
    
def delete_remote_files(remote_file_list, remote_data_path):
    """ delete a  list of files on the remote server """
    # TODO: deal properly with errors
    for file in remote_file_list:
        path=os.path.join(remote_data_path, file)
        print(f'Deleting remote file: {path}')
        command = ["ssh", "dfci@dfci", 'rm', path]
        output=subprocess.call(command, 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                universal_newlines=True)

def delete_local_files(local_file_list, local_data_path):
    """ delete a list of files locally """
    # TODO: deal properly with errors 
    for file in local_file_list:
        path=os.path.join(local_data_path, file)
        print(f'Deleting local file: {file}')
        os.remove(path)

def is_empty(file, local_data_path=''):
    ''' Return True is the file is empty '''
    return os.stat(os.path.join(local_data_path, file)).st_size == 0

def clean_empty_files(local_data_path=''):
    local_files = list_local_files(local_data_path)
    for file in local_files:
        if is_empty(file, local_data_path):
            print(f'{file} is empty')
        
    
if __name__ == '__main__':
    # Copy the recent data file into the local directory
    remote_file_list = list_remote_files()
    copy_remote_files_to_local(remote_file_list)
    
    # Plot the last data file. 
    local_file_list = list_local_files()
