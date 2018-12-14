# -*- coding: utf-8 -*-
"""
Created on Thu Mar 23 14:36:48 2017

@author: ray
"""

import numpy as np
from sklearn.neighbors import NearestNeighbors



import random
from sklearn import preprocessing
import time
import sys
#from sklearn.decomposition import RandomizedPCA, PCA
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
try: import cPickle as pickle
except: import pickle
from math import ceil
from pykdtree.kdtree import KDTree

import seaborn as sns
import pandas as pd



'''
Helper functions
'''


def plot(data):
    df = pd.DataFrame(data, columns=["x", "y"])
    sns.jointplot(x="x", y="y", data=df);
    sns.plt.show()



def get_data_process(li, list_of_index):
    result = []
    for entry in li:
        temp = ()
        for index in list_of_index:
            temp += (entry[index],)
        result.append(temp)
    return np.asarray(result)
    
def PCA_analysis(data, n_components = 2):
    #pca = RandomizedPCA(n_components = n_components )
    pca = PCA(n_components = n_components, svd_solver = "randomized" )
    X_pca = pca.fit_transform(data)
#    plot(X_pca)
    return X_pca, sum(pca.explained_variance_ratio_)
    
def PCA_analysis_desc(data,list_desc):
    data_process = get_data_process(data, list_desc)
    #pca = RandomizedPCA(n_components=2)
    pca = PCA(n_components = 2, svd_solver = "randomized" )
    X_pca = pca.fit_transform(data_process)
#    plot(X_pca)
    return X_pca, pca.components_[0], pca.components_[1]



def remove_list_from_list(a,b):
    return list(set(a)-set(b))


def standard_scale(data_original):
    scaler = preprocessing.StandardScaler().fit(data_original)
    return scaler.transform(data_original)
    
    
    

'''
subsample based on kD-tree

'''

def get_subsampling_index2(data_process, cutoff_sig = 0.02, rate = 0.3):
    data_process = StandardScaler().fit_transform(np.asarray(data_process).copy())

    list_of_descs = zip(*data_process)
    sum_std2 = 0.    
    for descs in list_of_descs:
        temp_std = np.std(descs)
        sum_std2 += temp_std**2
    
    #setting cutoff distance
    cutoff = cutoff_sig * np.sqrt(sum_std2)
      
    overall_keep_list = np.arange(len(data_process)).tolist() 
    
    len_old = len(data_process)
    len_new = 0
    keep_going = True
    while keep_going:
        print 'start total length:' + str(len_old)
        start = time.time()
        len_old = len(data_process)
   
        try:
            kd_tree = KDTree(data_process,leafsize=6)
            distances, indices = kd_tree.query(data_process, k=2)
        except:
            nbrs = NearestNeighbors(n_neighbors=2, algorithm='kd_tree',n_jobs=-1).fit(data_process)
            distances, indices = nbrs.kneighbors(data_process)

        remove_index_li = []
        
        for index, distance in zip(indices, distances):
            if distance[1] <= cutoff:
                remove_index_li.append(index[1])
        if len(remove_index_li) == 0:
            keep_going = False

        temp_num = int(ceil(float(len(remove_index_li))*rate))
        remove_index_li = random_subsampling(remove_index_li,temp_num)
        keep_index_li = remove_list_from_list(np.arange(len(data_process)).tolist(), remove_index_li)
        data_process = [data_process[i] for i in keep_index_li]
        overall_keep_list = [overall_keep_list[i] for i in keep_index_li]
        len_new = len(data_process)
        print 'new total length:' + str(len_new)


    return overall_keep_list
    

    
def subsampling_system(data, list_desc = [], cutoff_sig = 0.05, rate = 0.3):
    
    '''
    list_desc: list of dimensions/descriptors used in subsampling
    
    '''
    
    if len(list_desc) == 0:
        data_process = data
    else:
        data_process = get_data_process(data, list_desc)
    
    overall_keep_list = get_subsampling_index2(data_process, cutoff_sig = cutoff_sig)
    sampling_result = [data[i] for i in overall_keep_list]
    return sampling_result    


def subsampling_system_with_PCA(data, list_desc = [], cutoff_sig = 0.05, rate = 0.3,start_trial_component = 2):
    if len(list_desc) == 0:
        data_process = data
    else:
        data_process = get_data_process(data, list_desc)
    
    print 'start PCA'
    start = time.time()
    trial_component = start_trial_component
    keep_going = True
    while keep_going:
        pca_result, sum_explained_variance = PCA_analysis(data_process, n_components = trial_component)
        if sum_explained_variance > 0.999999:
            keep_going = False

        trial_component +=1
        print str(time.time()-start)
        if trial_component >= 20 or trial_component >= len(data_process[0]):
            keep_going = False
            pca_result = data_process
    print 'end trial PCA'
    print str(time.time()-start)
    overall_keep_list = get_subsampling_index2(pca_result, cutoff_sig = cutoff_sig,rate = rate)
    sampling_result = [data[i] for i in overall_keep_list]
    return sampling_result 

def subsampling_system_with_PCA_batch(data, list_desc = [], batch_size = 10000,layers = 3, cutoff_sig = 0.05, rate = 0.3,start_trial_component = 2):

    data_process = data
    while layers > 1 and len(data_process) > batch_size:
        temp_data = []
        for i in range(0, len(data_process), batch_size):
            temp_data += subsampling_system_with_PCA(data_process[i:i+batch_size], list_desc = list_desc, cutoff_sig = cutoff_sig,rate = rate,start_trial_component = start_trial_component)
        data_process = temp_data
        layers -= 1
    
    return data_process





def random_subsampling(li,num):
    '''
    return chosen number of random entries from a list
    '''

    if len(li) > num:
        # generate random list of indecies
        index_list = random.sample(range(0, len(li)-1),num)
        return [li[i] for i in index_list]
    else:
        print 'no sampling'
        return li
        

