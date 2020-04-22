import netCDF4
from netCDF4 import Dataset
import os
import numpy as np
import numpy.ma as ma
import pandas as pd
import random
from os import path

##################################################################################################################################3
## Parameters ##
dir_in = r'C:\Users\Rafael\Documents\Local\Mathematical Data Science\Project\Data_WQ'
version = 'rand'
rand_rows = 100
repeat = False
year_month = '20180101'
save = False
dir_out = r'C:\Users\Rafael\Documents\Local\Mathematical Data Science\Project\Data_WQ'
##################################################################################################################################3


def build_master_table(dir_in, version = 'rand', rand_rows = 100, repeat = True, year_month = '201801', save = False, dir_out = None):
    """
    This function creates the master table. The output is a pandas dataframe
    Inputs required:
        dir_in: folder where the datasets in .nc format are
        version: 'rand' (default), 'yearmonth' or 'all':
            -'rand'. Generates the table with a random number of lan-lon-time measurements. Arguments rand_rows and repeat must be also specified
            -'yearmonth'. Generates the table using only the specified year, yearmonth or yearmonthday and all the locations. Argument year_month must be also specified
            -'all'. Generates the table using all the timesteps and all the locations.
        rand_rows (Default 100). Int.  When 'rand' is selected, rand_rows is the number of random lan-lon-time measurements used to build the table
        repeat (Default True). Boolean. When 'rand' is selected, this value specifies if repeated lan-lon-time measurements are allowed in the table. Set to False to not allow repeated rows
        year_month (Default '201801'). String. When 'yearmonth' is selected, this value specifies which year, yearmonth or yearmonthday will be used to huild the table. Examples: '2010', '201008', '20100824'
        save (Default False). Boolean. Indicates if the generated table will be saved locally. The generate table is saved in .csv format with '|' as separators
        dir_out. Needed when save is selected. Folder where the table will be saved locally.
    """
    
    # Check if selected version is correct
    if (version != 'rand') and (version != 'yearmonth') and (version != 'all'):
        print('Error: invalid input for \"version\" argument. Choose \"rand\", \"yearmonth\" or \"all\"')
        return
    
    if (save == True) and (path.exists(dir_out) ==  False):
        print('Error: the directory given to \"dir_out\" does not exist')
        return
    
    # Open Chl
    file = dir_in + "\\dataset-CHL-model-daily.nc"
    dataset_chl = Dataset(file, "r")

    # Auxiliary variables and lists
    pairs = list(zip(*np.where(dataset_chl.variables['chl'][-1,0,:,:].mask == False))) # List of pairs (lat, lon) with unmasked values
    len_pairs = len(pairs) # Number of coordinates with unmasked values
    len_times = len(dataset_chl.variables['time']) # Number of timesteps
    times = list(map(lambda i: i.strftime("%Y%m%d"), netCDF4.num2date(dataset_chl.variables['time'][:],dataset_chl.variables['time'].units, only_use_cftime_datetimes=False, only_use_python_datetimes = True))) # Times
    latitudes = dataset_chl.variables['latitude'][:].data # Latitudes
    longitudes = dataset_chl.variables['longitude'][:].data # Longitudes

    # Open O2
    file = dir_in + "\\dataset-DOXYL-model-daily.nc"
    dataset_o2 = Dataset(file, "r")

    # Open NO3
    file = dir_in + "\\dataset-NITR-model-daily.nc"
    dataset_no3 = Dataset(file, "r")

    # Open PO4
    file = dir_in + "\\dataset-PHOS-model-daily.nc"
    dataset_po4 = Dataset(file, "r")

    # Create the master table
    dictionary_list = []
    
    # Version = rand
    if version == 'rand':
        # Ask for confirmation
        cont = input("The master table will be created with {} random lan-lon-time measurements. Are you sure you want to continue? This process can take some time (y/n)".format(rand_rows))
        if cont != "y" and cont != "Y":
            print('Process stopped')
            return 
        print('Process started')
        
        chosen = ['0']
        for i in range(rand_rows):
            coordinate_time_ix = '0'
            if repeat == False:
                count = 0
                while coordinate_time_ix in chosen:
                    count += 1
                    if count == 1000000:
                        print('Error: Timeout generating random samples')
                        return
                    coordinate_ix = random.randint(0,len_pairs-1) # Random coordinate
                    time_ix = random.randint(0,len_times-1) # Random timestep
                    coordinate_time_ix = str(coordinate_ix) + '-' + str(time_ix)
                chosen.append(coordinate_time_ix)
            else:
                coordinate_ix = random.randint(0,len_pairs-1) # Random coordinate
                time_ix = random.randint(0,len_times-1) # Random timestep
             
            # Create row of table
            dictionary_data = {'Time' : times[time_ix], 'Lat' : latitudes[pairs[coordinate_ix][0]], 'Lon' : longitudes[pairs[coordinate_ix][1]], 'Chl' : dataset_chl['chl'][time_ix,0,pairs[coordinate_ix][0],pairs[coordinate_ix][1]], 'O2' : dataset_o2['o2'][time_ix,0,pairs[coordinate_ix][0],pairs[coordinate_ix][1]], 'NO3' : dataset_no3['no3'][time_ix,0,pairs[coordinate_ix][0],pairs[coordinate_ix][1]], 'PO4' : dataset_po4['po4'][time_ix,0,pairs[coordinate_ix][0],pairs[coordinate_ix][1]]}
            dictionary_list.append(dictionary_data)
        
        # Convert to pandas dataframe
        my_df = pd.DataFrame.from_dict(dictionary_list)
         
        # Save dataframe locally
        if save == True:
            my_df.to_csv(dir_out + '\\table_rand{}.csv'.format(rand_rows), index=False, sep='|')

    # Version = yearmonth
    elif version == 'yearmonth':
        # Ask for confirmation
        cont = input("The master table will be created with the timesteps starting with {} and all the locations. Are you sure you want to continue? This process can take some time (y/n)".format(year_month))
        if cont != "y" and cont != "Y":
            print('Process stopped')
            return 
        print('Process started')
        
        ix = [times.index(l) for l in times if l.startswith(year_month)] # Filter timesteps according to year_month
        len_ix = len(ix)
        
        counter = 0
        for i in ix:
            counter += 1
            if counter%5==0:
                print("{}/{} timesteps processed".format(counter, len_ix))
            for j in pairs:
                # Create row of table
                dictionary_data = {'Time' : times[i] , 'Lat' : latitudes[j[0]], 'Lon' : longitudes[j[1]], 'Chl' : dataset_chl['chl'][i,0,j[0],j[1]]}
                dictionary_list.append(dictionary_data)
        
        # Convert to pandas dataframe
        my_df = pd.DataFrame.from_dict(dictionary_list)
        
        # Save dataframe locally
        if save == True:
            my_df.to_csv(dir_out + '\\table_{}.csv'.format(year_month), index=False, sep='|')
            
    # Version = all       
    elif version == 'all':
        # Ask for confirmation
        cont = input("The master table will be created with all the timesteps and all the locations. Are you sure you want to continue? This process will take some time (y/n)")
        if cont != "y" and cont != "Y":
            print('Process stopped')
            return 
        print('Process started')
        
        for i in range(len_times):
            if i%10==0:
                print("{}/{} timesteps processed".format(i, len_times))
            for j in pairs:
                # Create row of table
                dictionary_data = {'Time' : times[i] , 'Lat' : latitudes[j[0]], 'Lon' : longitudes[j[1]], 'Chl' : dataset_chl['chl'][i,0,j[0],j[1]]}
                dictionary_list.append(dictionary_data)
        
        # Convert to pandas dataframe
        my_df = pd.DataFrame.from_dict(dictionary_list)
        
        # Save dataframe locally
        if save == True:
            my_df.to_csv(dir_out + '\\table_all.csv', index=False, sep='|')
    else:
        return
    
    dataset_chl.close()
    dataset_o2.close()
    dataset_no3.close()
    dataset_po4.close()
    
    return my_df


table = build_master_table(dir_in = dir_in, version = version, rand_rows = rand_rows, repeat = repeat, year_month = year_month, save = save, dir_out = dir_out)