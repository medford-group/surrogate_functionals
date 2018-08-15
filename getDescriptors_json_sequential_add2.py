# -*- coding: utf-8 -*-
"""
Created on Tue Aug 15 15:53:10 2017

@author: ray
"""

import numpy as np
import sys
import math

from convolutions import get_differenciation_conv, get_integration_stencil,get_auto_accuracy,get_fftconv_with_known_stencil_no_wrap,get_asym_integration_stencil,get_asym_integration_fftconv,get_asym_integral_fftconv_with_known_stencil,calc_harmonic_stencil
import h5py
import os
#from joblib import Parallel, delayed
#import multiprocessing
import itertools
import json


def read_system(mol,xc,Nx_center,Ny_center,Nz_center,Nx,Ny,Nz,data_name):
    def get_index(center,maxx,minn):
        if center > maxx or center < minn:
            raise NotImplementedError
        temp_first = center - 1
        if temp_first <0:
            temp_first = maxx
        temp_second = center
        temp_third = center +1
        if temp_third >maxx:
            temp_third = minn
        return [temp_first,temp_second,temp_third]
    
    Nx_max = Nx-1
    Ny_max = Ny-1
    Nz_max = Nz-1
    Nx_min = 0
    Ny_min = 0
    Nz_min = 0
    
    Nx_list = get_index(Nx_center,Nx_max,Nx_min)
    Ny_list = get_index(Ny_center,Ny_max,Ny_min)
    Nz_list = get_index(Nz_center,Nz_max,Nz_min)
    
    temp_x = None
    x_start = True
    print Nx_list, Ny_list,Nz_list
    for i in Nx_list:
        
        temp_y = None
        y_start = True
        for j in Ny_list:
            
            temp_z = None
            z_start = True
            for k in Nz_list:
                
                temp_filename =  '{}_{}_{}_{}_{}.hdf5'.format(mol,xc,i,j,k)            
                if os.path.isfile(temp_filename):
                    raw_data =  h5py.File(temp_filename,'r')
                    temp_data = np.asarray(raw_data[data_name])
                if z_start:
                    temp_z = temp_data
                    z_start = False
                else:
                    temp_z = np.concatenate((temp_z,temp_data),axis=2)
            
            if y_start:
                temp_y = temp_z
                y_start = False
            else:
                temp_y = np.concatenate((temp_y,temp_z),axis=1)
       
        if x_start:
            temp_x = temp_y
            x_start = False
        else:
            temp_x = np.concatenate((temp_x,temp_y),axis=0)
    
    return temp_x
    
def carve_out_matrix(matrix):
    old_shape_x, old_shape_y, old_shape_z = matrix.shape
    x = int(round(old_shape_x / 3. ,0))
    y = int(round(old_shape_y / 3. ,0))
    z = int(round(old_shape_z / 3. ,0))
   
    return matrix[x:2*x,y:2*y,z:2*z]

def get_homogeneous_gas_integral(n,r):
    return r*r*n*math.pi

def get_homo_nondimensional(int_arr, n_arr, r):
    temp = (4./3.)*r*r*r*math.pi
    result = np.divide(int_arr, n_arr)
    return np.divide(result, temp)

def get_homo_nondimensional_nave(int_arr, n_ave, r):
    temp = (4./3.)*r*r*r*math.pi*n_ave
    return np.divide(int_arr, temp)


def calculate_ave_density_desc(n,r,hx,hy,hz,stencil,pad):
    print 'start ave dens desc : ' + str(r) 
#    integration, temp_pad  = get_integration_fftconv(n, hx, hy, hz, r, accuracy = get_auto_accuracy(hx,hy,hz, r))
    integration, temp_pad = get_fftconv_with_known_stencil_no_wrap(n,hx,hy,hz,r,stencil,pad)
    ave_density = get_homo_nondimensional_nave(integration, 1.0, r)
    return ave_density, temp_pad

def create_dataset(database, dataset_name, data):
    if dataset_name not in database.keys():
        database.create_dataset(dataset_name,data=data)
    return



def process_range_descriptor(molecule, functional,i,j,k,h,N,r_list,harmonic_stencil_dict):
    
    result_filename = "{}_{}_{}_{}_{}_all_descriptors.hdf5".format(molecule,functional,i,j,k)
    Nx = Ny = Nz = N
#    print 'get range1'
    extented_n = read_system(molecule,functional,i,j,k,Nx,Ny,Nz,'rho')

#    print 'get range2'
    with h5py.File(result_filename,'a') as data:
        
#        temp_first_deri = np.gradient(extented_n.copy())
        try:
            ave_dens_grp = data['average_density']
            print "get ave_dens_grp"
        except:
            ave_dens_grp = data.create_group('average_density')

        try:
            asym_integral_grp = data['asym_integral']
            print "get asym_integral"
        except:
            asym_integral_grp = data.create_group('asym_integral')

        try:
            derivative_grp = data['derivative']
            print "get derivative"
        except:
            derivative_grp = data.create_group('derivative')

        try:
            spherical_harmonic_grp = data['spherical_harmonic']
            print "spherical_harmonic"
        except:
            spherical_harmonic_grp = data.create_group('spherical_harmonic')

        #ave_dens_grp = data.create_group('average_density')
        #asym_integral_grp = data.create_group('asym_integral')
        #derivative_grp = data.create_group('derivative')
        #for index, r in enumerate(r_list):
        #    dataset_name = 'average_density_{}'.format(str(r).replace('.','-'))

        #    if dataset_name not in ave_dens_grp.keys():
        #        print "start: {} ave density".format(r)
        #        temp_data, temp_pad = calculate_ave_density_desc(extented_n.copy(),r,h,h,h,stencil_list[index],pad_list[index])
        #        ave_dens_grp.create_dataset(dataset_name,data=carve_out_matrix(temp_data))
        
        #for index, r in enumerate(r_list):
        #    dataset_name = 'asym_integral_x_{}'.format(str(r).replace('.','-'))
        #    if dataset_name not in asym_integral_grp.keys():
        #        print "start: {} axym x".format(r)
        #        temp_data, temp_pad = get_asym_integral_fftconv_with_known_stencil(extented_n.copy(), h ,h ,h , r, asym_stencil_list[0][index], asym_pad_list[0][index] )
        #        asym_integral_grp.create_dataset(dataset_name,data=carve_out_matrix(temp_data))
        
        #for index, r in enumerate(r_list):
        #    dataset_name = 'asym_integral_y_{}'.format(str(r).replace('.','-'))
        #    if dataset_name not in asym_integral_grp.keys():
        #        print "start: {} axym y".format(r)
        #        temp_data, temp_pad = get_asym_integral_fftconv_with_known_stencil(extented_n.copy(), h ,h ,h , r, asym_stencil_list[1][index], asym_pad_list[1][index] )
        #        asym_integral_grp.create_dataset(dataset_name,data=carve_out_matrix(temp_data))
                
        #for index, r in enumerate(r_list):
        #    dataset_name = 'asym_integral_z_{}'.format(str(r).replace('.','-'))
        #    if dataset_name not in asym_integral_grp.keys():
        #        print "start: {} axym z".format(r)
        #        temp_data, temp_pad = get_asym_integral_fftconv_with_known_stencil(extented_n.copy(), h ,h ,h , r, asym_stencil_list[2][index], asym_pad_list[2][index] )
        #        asym_integral_grp.create_dataset(dataset_name,data=carve_out_matrix(temp_data))

        for r in r_list:
            dataset_name = 'shperical_harmonic_1_n1_{}'.format(str(r).replace('.','-'))
            if dataset_name not in spherical_harmonic_grp.keys():
                print "start: {} shperical 1 -1".format(r)
                stencil_Re = harmonic_stencil_dict["1"]["-1"][str(r)][0]
                stencil_Im = harmonic_stencil_dict["1"]["-1"][str(r)][1]
                pad = harmonic_stencil_dict["1"]["-1"][str(r)][2]
                temp_result_Re_extend,_ = get_fftconv_with_known_stencil_no_wrap(n,hx,hy,hz,1,stencil_Re,0)
                temp_result_Im_extend,_ = get_fftconv_with_known_stencil_no_wrap(n,hx,hy,hz,1,stencil_Im,0)

                temp_result_Re = carve_out_matrix(temp_result_Re_extend)
                temp_result_Im = carve_out_matrix(temp_result_Im_extend)

                temp_result = np.sqrt(np.add(np.square(temp_result_Re), np.square(temp_result_Im)))

                spherical_harmonic_grp.create_dataset(dataset_name,data=temp_result)

        for r in r_list:
            dataset_name = 'shperical_harmonic_1_0_{}'.format(str(r).replace('.','-'))
            if dataset_name not in spherical_harmonic_grp.keys():
                print "start: {} shperical 1 0".format(r)
                stencil_Re = harmonic_stencil_dict["1"]["0"][str(r)][0]
                stencil_Im = harmonic_stencil_dict["1"]["0"][str(r)][1]
                pad = harmonic_stencil_dict["1"]["0"][str(r)][2]
                temp_result_Re_extend,_ = get_fftconv_with_known_stencil_no_wrap(n,hx,hy,hz,1,stencil_Re,0)
                temp_result_Im_extend,_ = get_fftconv_with_known_stencil_no_wrap(n,hx,hy,hz,1,stencil_Im,0)

                temp_result_Re = carve_out_matrix(temp_result_Re_extend)
                temp_result_Im = carve_out_matrix(temp_result_Im_extend)

                temp_result = np.sqrt(np.add(np.square(temp_result_Re), np.square(temp_result_Im)))

                spherical_harmonic_grp.create_dataset(dataset_name,data=temp_result)

        for r in r_list:
            dataset_name = 'shperical_harmonic_1_1_{}'.format(str(r).replace('.','-'))
            if dataset_name not in spherical_harmonic_grp.keys():
                print "start: {} shperical 1 1".format(r)
                stencil_Re = harmonic_stencil_dict["1"]["1"][str(r)][0]
                stencil_Im = harmonic_stencil_dict["1"]["1"][str(r)][1]
                pad = harmonic_stencil_dict["1"]["1"][str(r)][2]
                temp_result_Re_extend,_ = get_fftconv_with_known_stencil_no_wrap(n,hx,hy,hz,1,stencil_Re,0)
                temp_result_Im_extend,_ = get_fftconv_with_known_stencil_no_wrap(n,hx,hy,hz,1,stencil_Im,0)

                temp_result_Re = carve_out_matrix(temp_result_Re_extend)
                temp_result_Im = carve_out_matrix(temp_result_Im_extend)

                temp_result = np.sqrt(np.add(np.square(temp_result_Re), np.square(temp_result_Im)))

                spherical_harmonic_grp.create_dataset(dataset_name,data=temp_result)

                

        
    return


def prepare_integral_stencils(r_list,h):
    print 'start preparing integral stencils'
    stencil_list = []
    pad_list = []
    #for r in r_list:
    #    temp_stencil,temp_pad = get_integration_stencil(h, h, h, r, accuracy = get_auto_accuracy(h,h,h, r))
    #    stencil_list.append(temp_stencil)
    #    pad_list.append(temp_pad)
    return stencil_list, pad_list


def prepare_asym_integral_stencils(r_list,h):
    print 'start preparing integral stencils'
    stencil_x_list = []
    stencil_y_list = []
    stencil_z_list = []
    pad_x_list = []
    pad_y_list = []
    pad_z_list = []
    #for r in r_list:
    #    temp_stencil,temp_pad = get_asym_integration_stencil(h, h, h, r, 'x')
    #    stencil_x_list.append(temp_stencil)
    #    pad_x_list.append(temp_pad)
        
    #    temp_stencil,temp_pad = get_asym_integration_stencil(h, h, h, r, 'y')
    #    stencil_y_list.append(temp_stencil)
    #    pad_y_list.append(temp_pad)
        
    #    temp_stencil,temp_pad = get_asym_integration_stencil(h, h, h, r, 'z')
    #    stencil_z_list.append(temp_stencil)
    #    pad_z_list.append(temp_pad)
    
    asym_stencil_list = [stencil_x_list, stencil_y_list, stencil_z_list]
    asym_pad_list = [pad_x_list, pad_y_list, pad_z_list]
    return asym_stencil_list,asym_pad_list


def prepare_harmonic_stencil_stencils(r_list,h):

    harmonic_stencil_dict = {}
    harmonic_stencil_dict["1"] = {}
    harmonic_stencil_dict["1"]["-1"] = {}
    harmonic_stencil_dict["1"]["0"] = {}
    harmonic_stencil_dict["1"]["1"] = {}

    for r in r_list:
        stencil_Re, stencil_Im, pad = calc_harmonic_stencil(h, h, h, r, 1, -1, accuracy = 6)
        harmonic_stencil_dict["1"]["-1"][str(r)] = [stencil_Re, stencil_Im, pad ]

        stencil_Re, stencil_Im, pad = calc_harmonic_stencil(h, h, h, r, 1, 0, accuracy = 6)
        harmonic_stencil_dict["1"]["0"][str(r)] = [stencil_Re, stencil_Im, pad ]

        stencil_Re, stencil_Im, pad = calc_harmonic_stencil(h, h, h, r, 1, 1, accuracy = 6)
        harmonic_stencil_dict["1"]["1"][str(r)] = [stencil_Re, stencil_Im, pad ]


    return harmonic_stencil_dict

def process(molecule, functional,i,j,k,h,N,r_list,harmonic_stencil_dict):
    result_filename = "{}_{}_{}_{}_{}_all_descriptors.hdf5".format(molecule,functional,i,j,k)
    #if os.path.isfile(result_filename) == False:
    print 'start {} {} {}'.format(i,j,k)
    process_range_descriptor(molecule, functional,i,j,k,h,N,r_list,harmonic_stencil_dict)
    

def process_one_molecule(molecule, functional,h,L,N,r_list):
    cwd = os.getcwd()
    dir_name = "{}_{}_{}_{}_{}".format(molecule,functional,str(L).replace('.','-'),str(h).replace('.','-'),N)
    print dir_name
    
    if os.path.isdir(dir_name) == False:
        print '\n****Error: Cant find the directory! ****\n'
        raise NotImplementedError
    
    os.chdir(cwd + '/' + dir_name)
    #stencil_list,pad_list = prepare_integral_stencils(r_list,h)
    #asym_stencil_list,asym_pad_list = prepare_asym_integral_stencils(r_list,h)

    harmonic_stencil_dict = prepare_harmonic_stencil_stencils(r_list,h)
    
    
    Nx = Ny = Nz = N
    i_li = range(Nx)
    j_li = range(Ny)
    k_li = range(Nz)
    
    paramlist = list(itertools.product(i_li,j_li,k_li))



    for i,j,k in paramlist:
        process(molecule, functional,i,j,k,h,N,r_list,harmonic_stencil_dict)
        
    
    
    os.chdir(cwd)
    return


if __name__ == "__main__":

    print "start adding dataset"

    setup_filename = sys.argv[1]
    choice = sys.argv[2]

    #with open(setup_filename, encoding='utf-8') as f:
    with open(setup_filename) as f:
        setup = json.load(f)

    print setup

    if choice not in ['single','set']:
        raise NotImplementedError
    
    if choice == 'single':
        molecule = sys.argv[3]
        print "start"
        h = float(setup['grid_spacing'])
        L = float(setup['box_dimension'])
        N = int(setup['number_segment_per_side'])
        functional = setup['functionals']
        r_list = setup['r_list']

        #for functional in functionals:
        print "start process molecule"
        process_one_molecule(molecule, functional,h,L,N,r_list)
