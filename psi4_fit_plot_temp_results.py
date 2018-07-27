# -*- coding: utf-8 -*-
"""
Created on Tue Oct 24 09:43:05 2017

@author: ray
"""
import matplotlib
matplotlib.use('Agg') 
import matplotlib.cm as cm
from mpl_toolkits.mplot3d import Axes3D
import mpl_toolkits.mplot3d.axes3d as p3
import matplotlib.pyplot as plt

import numpy as np
import csv
import sys
import os
import time
import math
import json
from glob import glob
from sklearn import linear_model
from keras.models import Sequential
from keras.models import load_model
from keras.layers import Dense, Activation
from keras import backend as K
import keras
import scipy

import itertools
import multiprocessing

try: import cPickle as pickle
except: import pickle
import matplotlib.pyplot as plt
from subsampling import subsampling_system,random_subsampling,subsampling_system_with_PCA
import keras.backend as K

def sae(y_true, y_pred):
    return K.sum(K.abs(y_pred - y_true))

def map_to_n1_1(arr, maxx, minn):
    return np.divide(np.subtract(arr,minn),(maxx-minn)/2.)-1.
    
def log(log_filename, text):
    with open(log_filename, "a") as myfile:
        myfile.write(text)
    return


def write(log_filename, text):
    with open(log_filename, "w") as myfile:
        myfile.write(text)
    return

def map_to_0_1(arr, maxx, minn):
    return np.divide(np.subtract(arr,minn),(maxx-minn))
    
def map_back(arr, maxx, minn):
    return np.add(np.multiply(arr,(maxx-minn)),minn)

def get_start_loss(log_filename):
    
    with open(log_filename, 'r') as f:
        for line in f:
            pass
        temp = line
    
    if temp.strip().startswith('updated'):
        return float(temp.split()[2]), temp.split()[9]
    else:
        raise ValueError



def fit_with_LDA(density,energy):

    filename = "LDA_model.sav"
    text_filename = "LDA_model_result.txt"

    temp_res = pickle.load(open(filename, 'rb'))
    res = temp_res


    predict_y = predict_LDA(density,res.x)
    residual = energy - predict_y

    return residual, res


def LDA_least_suqare_fit(x,density,energy):

    #result = 0
    #for n, e in density, energy:
    #    result += (lda_x(n,x) + lda_c(n,x) - e)**2

    result = np.mean(np.square(lda_x(density,x) + lda_c(density,x) - energy))
    return result


def get_x0():
    x = [ -0.45816529328314287, 0.031091, 0.21370, 7.5957, 3.5876, 1.6382, 0.49294]
    return x

def optimization_constants(x):
    #C0I = x[0]
    #C1  = x[1]
    #CC1 = x[2]
    #CC2 = x[3]
    #IF2 = x[4]

    C1  = x[0]
    gamma = x[1]
    alpha1 = x[2]
    beta1 = x[3]
    beta2 = x[4]
    beta3 = x[5]
    beta4 = x[6]

    #return C0I, C1, CC1, CC2, IF2, gamma, alpha1, beta1, beta2, beta3, beta4
    return C1, gamma, alpha1, beta1, beta2, beta3, beta4

def G(rtrs, gamma, alpha1, beta1, beta2, beta3, beta4):
    Q0 = -2.0 * gamma * (1.0 + alpha1 * rtrs * rtrs)
    Q1 = 2.0 * gamma * rtrs * (beta1 +
                           rtrs * (beta2 +
                                   rtrs * (beta3 +
                                           rtrs * beta4)))
    G1 = Q0 * np.log(1.0 + 1.0 / Q1)
    return G1

def lda_x( n, x):
#    C0I, C1, CC1, CC2, IF2 = lda_constants()
    C1, gamma, alpha1, beta1, beta2, beta3, beta4 = optimization_constants(x)

    C0I = 0.238732414637843
    #C1 = -0.45816529328314287
    rs = (C0I / n) ** (1 / 3.)
    ex = C1 / rs
    return n*ex
    #e[:] += n * ex

def lda_c( n, x):
    #C0I, C1, CC1, CC2, IF2 = lda_constants()
    C1, gamma, alpha1, beta1, beta2, beta3, beta4 = optimization_constants(x)

    C0I = 0.238732414637843
    #C1 = -0.45816529328314287
    rs = (C0I / n) ** (1 / 3.)
    ec = G(rs ** 0.5, gamma, alpha1, beta1, beta2, beta3, beta4)
    return n*ec
    #e[:] += n * ec

def predict_LDA(n,LDA_x):

    n = np.asarray(n)

    return lda_x(n,LDA_x) + lda_c(n,LDA_x)

def predict_LDA_residual(n,LDA_x,X,NN_model):

    n = np.asarray(n)

    return lda_x(n,LDA_x) + lda_c(n,LDA_x) + ((NN_model.predict(X*1e6))/1e6)

def save_resulting_figure(n,LDA_x,X,NN_model,y,loss,loss_result):

    dens = n
    predict_y = predict_LDA_residual(n,LDA_x,X,NN_model)

    LDA_predict_y = predict_LDA(n,LDA_x)

    error = y - predict_y

    log_dens = np.log10(n)

    log_predict_y = np.log10(np.multiply(-1.,predict_y))
    log_y = np.log10(np.multiply(-1.,y))

    log_a_error = np.log10(np.abs(error))

#    fig=plt.figure(figsize=(40,40))
#
#    plt.scatter(dens, y,            c= 'red',  lw = 0,label='original',alpha=1.0)
#    plt.scatter(dens, predict_y,    c= 'blue',  lw = 0,label='predict',alpha=1.0)
#    plt.scatter(dens, error,            c= 'yellow',  lw = 0,label='error',alpha=1.0)
#
#    legend = plt.legend(loc="best", shadow=False, scatterpoints=1, fontsize=30, markerscale=3)
#
#    plt.tick_params(labelsize=60)
#    
#    plt.savefig('result_plot.png')
#
#    fig=plt.figure(figsize=(40,40))
#
#    plt.scatter(dens, error,            c= 'red',  lw = 0,label='error',alpha=1.0)
#
#    legend = plt.legend(loc="best", shadow=False, scatterpoints=1, fontsize=30, markerscale=3)
#
#    plt.tick_params(labelsize=60)
#    
#    plt.savefig('error_plot.png')


    fig, axes = plt.subplots(2, 2, figsize=(100,100))
    ((ax1, ax2),(ax3,ax4)) = axes
    ax1.scatter(dens, y,            c= 'red',  lw = 0,label='original',alpha=1.0)
    ax1.scatter(dens, predict_y,    c= 'blue',  lw = 0,label='predict',alpha=1.0)
    ax1.scatter(dens, error,            c= 'yellow',  lw = 0,label='error',alpha=1.0)
    legend = ax1.legend(loc="best", shadow=False, scatterpoints=1, fontsize=80, markerscale=10)
    ax1.tick_params(labelsize=80)
    ax1.set_xlabel('density', fontsize=100)
    ax1.set_ylabel('energy density', fontsize=100)

    ax2.scatter(log_dens, y,            c= 'red',  lw = 0,label='original',alpha=1.0)
    ax2.scatter(log_dens, predict_y,    c= 'blue',  lw = 0,label='predict',alpha=1.0)
    ax2.scatter(log_dens, error,            c= 'yellow',  lw = 0,label='error',alpha=1.0)
    legend = ax2.legend(loc="best", shadow=False, scatterpoints=1, fontsize=80, markerscale=10)
    ax2.tick_params(labelsize=80)
    ax2.set_xlabel('log10 density', fontsize=100)
    ax2.set_ylabel('energy density', fontsize=100)

    ax3.scatter(dens, log_y,            c= 'red',  lw = 0,label='original',alpha=1.0)
    try:
        ax3.scatter(dens, log_predict_y,    c= 'blue',  lw = 0,label='predict',alpha=1.0)
    except:
        pass
    legend = ax3.legend(loc="best", shadow=False, scatterpoints=1, fontsize=80, markerscale=10)
    ax3.tick_params(labelsize=80)
    ax3.set_xlabel('density', fontsize=100)
    ax3.set_ylabel('log10 negative energy density', fontsize=100)

    ax4.scatter(log_dens, log_y,            c= 'red',  lw = 0,label='original',alpha=1.0)
    try:
        ax4.scatter(log_dens, log_predict_y,    c= 'blue',  lw = 0,label='predict',alpha=1.0)
    except:
        pass
    legend = ax4.legend(loc="best", shadow=False, scatterpoints=1, fontsize=80, markerscale=10)
    ax4.tick_params(labelsize=80)
    ax4.set_xlabel('log10 density', fontsize=100)
    ax4.set_ylabel('log10 negative energy density', fontsize=100)

    plt.savefig('result_plot_{}_{}.png'.format(loss,loss_result))


    fig, axes = plt.subplots(2, 2, figsize=(100,100))
    ((ax1, ax2),(ax3,ax4)) = axes
    ax1.scatter(dens, error,            c= 'red',  lw = 0,label='error',alpha=1.0)
    legend = ax1.legend(loc="best", shadow=False, scatterpoints=1, fontsize=80, markerscale=10)
    ax1.tick_params(labelsize=80)
    ax1.set_xlabel('density', fontsize=100)
    ax1.set_ylabel('error', fontsize=100)

    ax2.scatter(log_dens, error,            c= 'red',  lw = 0,label='error',alpha=1.0)
    legend = ax2.legend(loc="best", shadow=False, scatterpoints=1, fontsize=80, markerscale=10)
    ax2.tick_params(labelsize=80)
    ax2.set_xlabel('log10 density', fontsize=100)
    ax2.set_ylabel('error', fontsize=100)

    ax3.scatter(dens, log_a_error,            c= 'red',  lw = 0,label='absolute error',alpha=1.0)
    legend = ax3.legend(loc="best", shadow=False, scatterpoints=1, fontsize=80, markerscale=10)
    ax3.tick_params(labelsize=80)
    ax3.set_xlabel('density', fontsize=100)
    ax3.set_ylabel('log10 absolute error', fontsize=100)

    ax4.scatter(log_dens, log_a_error,            c= 'red',  lw = 0,label='absolute error',alpha=1.0)
    legend = ax4.legend(loc="best", shadow=False, scatterpoints=1, fontsize=80, markerscale=10)
    ax4.tick_params(labelsize=80)
    ax4.set_xlabel('log10 density', fontsize=100)
    ax4.set_ylabel('log10 absolute error', fontsize=100)

    plt.savefig('error_plot_{}_{}.png'.format(loss,loss_result))



    #csv_result = []
    #csv_result.append(np.transpose(dens).tolist()[0])
    #csv_result.append(np.transpose(y).tolist()[0])
    #csv_result.append(np.transpose(LDA_predict_y).tolist()[0])
    #csv_result.append(np.transpose(predict_y).tolist()[0])
    #csv_result.append(np.transpose(error).tolist()[0])

    #result = np.stack(csv_result,axis=1).tolist()
    #with open('training_result.csv', "wb") as f:
    #    writer = csv.writer(f)
    #    writer.writerow(['density','y','LDA_predict_y','predict_y','error'])
    #    writer.writerows(result)

    return


def read_data_from_one_dir(directory):
    temp_cwd = os.getcwd()
    os.chdir(directory)

    print directory

    subsampled_filename = "overall_subsampled_data.p"
    random_filename = "overall_random_data.p"

    try:
        molecule_subsampled_data = pickle.load(open(subsampled_filename,'rb'))
        print "read subsampled data"
    except:
        molecule_subsampled_data = []

    try:
        molecule_random_data = pickle.load(open(random_filename,'rb'))
        print "read random data"
    except:
        molecule_random_data = []
    #molecule_random_data = []

    os.chdir(temp_cwd)

    return molecule_subsampled_data, molecule_random_data



def get_training_data(dataset_name,setup):

    data_dir_name = setup["working_dir"] + "/data/*/" 
    data_paths = glob(data_dir_name)
    print data_paths


    overall_subsampled_data = []
    overall_random_data = []
    num_samples = len(data_paths)
    num_random_per_molecule = int(math.ceil(float(setup["random_pick"])/float(num_samples)))
    for directory in data_paths:
        temp_molecule_subsampled_data, temp_molecule_random_data = read_data_from_one_dir(directory)
        overall_subsampled_data += temp_molecule_subsampled_data
        overall_random_data += random_subsampling(temp_molecule_random_data, num_random_per_molecule)



    list_subsample = setup["subsample_feature_list"]
    temp_list_subsample = setup["subsample_feature_list"]
    if temp_list_subsample == []:
        for m in range(len(overall_subsampled_data[0])):
            temp_list_subsample.append(m)

    #if len(temp_list_subsample) <= 10:
    #    overall_subsampled_data = subsampling_system(overall_subsampled_data, list_desc = list_subsample, cutoff_sig = float(setup["subsample_cutoff_sig"]), rate = float(setup["subsample_rate"]))
    #else:
    #    overall_subsampled_data = subsampling_system_with_PCA(overall_subsampled_data, list_desc = list_subsample, cutoff_sig = float(setup["subsample_cutoff_sig"]), rate = float(setup["subsample_rate"]),start_trial_component = 9)


    overall = overall_random_data + overall_subsampled_data
    #overall = overall_subsampled_data



    X_train = []
    y_train = []
    dens = []

    for entry in overall:
#        if entry[0] >= lower and entry[0] <= upper:
        X_train.append(list(entry[1:]))
        dens.append(entry[1])
        y_train.append(entry[0])
    
    
    X_train = (np.asarray(X_train))
    y_train = np.asarray(y_train).reshape((len(y_train),1))
    dens = np.asarray(dens).reshape((len(dens),1))
    
    return X_train, y_train, dens


def fit_model(LDA_result, dens, X_train, residual, loss, tol, slowdown_factor, early_stop_trials):

    NN_model,loss_result = fit_with_KerasNN(X_train * 1e6, residual * 1e6, loss, tol, slowdown_factor, early_stop_trials)
    save_resulting_figure(dens,LDA_result.x,X_train,NN_model,y,loss,loss_result)

    return NN_model


if __name__ == "__main__":


    setup_filename = sys.argv[1]
    dataset_name = sys.argv[2]
    NN_model_name = sys.argv[3]


    with open(setup_filename) as f:
        setup = json.load(f)


    K.set_floatx('float64')
    K.floatx()

    h = float(setup['grid_spacing'])
    L = float(setup['box_dimension'])
    N = int(setup['number_segment_per_side'])
    dir_name = "{}_{}_{}".format(str(L).replace('.','-'),str(h).replace('.','-'),N)

    working_dir = os.getcwd() + '/' + dir_name + '/' + dataset_name

    setup["working_dir"] = working_dir

    model_save_dir = working_dir + "/" + "NN_LDA_residual_1M_{}_{}_{}".format(setup["NN_setup"]["number_neuron_per_layer"], setup["NN_setup"]["number_layers"], setup["NN_setup"]["activation"])
   
    setup["model_save_dir"] = model_save_dir

    
    
    X_train,y, dens = get_training_data(dataset_name,setup)
   
    if os.path.isdir(model_save_dir) == False:
        os.makedirs(model_save_dir)

    os.chdir(model_save_dir)
    
    #residual,li_model = fit_with_Linear(dens,y)

    residual, LDA_result = fit_with_LDA(dens,y)
    setup['LDA_model'] = LDA_result


    if NN_model_name == "NN.h5":

        loss_value,loss = get_start_loss("NN_fit_log.log")
        try:
            NN_model = load_model(NN_model_name, custom_objects={'sae': sae})
        except:
            NN_model = load_model(NN_model_name)
        NN_model.save("NN_{}_{}_backup.h5".format(loss,loss_value))


    else:
        temp = NN_model_name.split("_")
        if temp[1] == "mean" and temp[2] == "absolute" and temp[3] == "percentage":
            loss = "mean_absolute_percentage_error"
            loss_value = temp[5]
        else:
            loss = temp[1]
            loss_value = temp[2]
        try:
            NN_model = load_model(NN_model_name, custom_objects={'sae': sae})
        except:
            NN_model = load_model(NN_model_name)




    loss_result,loss = get_start_loss("NN_fit_log.log")

    try:
        NN_model = load_model(NN_model_name, custom_objects={'sae': sae})
    except:
        NN_model = load_model(NN_model_name)
    NN_model.save("NN_{}_{}_backup.h5".format(loss,loss_value))

    save_resulting_figure(dens,LDA_result.x,X_train,NN_model,y,loss,loss_value)




    