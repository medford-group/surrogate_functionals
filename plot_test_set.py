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

import scipy

import itertools
import multiprocessing

try: import cPickle as pickle
except: import pickle
import matplotlib.pyplot as plt
from subsampling import subsampling_system,random_subsampling,subsampling_system_with_PCA
import keras.backend as K

import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt

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

def predict(n,LDA_x,X,NN_model,y):

    dens = n
    predict_y = predict_LDA_residual(n,LDA_x,X,NN_model)

    #LDA_predict_y = predict_LDA(n,LDA_x)

    error = y - predict_y


    return predict_y, error


def initialize(setup,key):
    os.chdir(setup[key]["model_save_dir"])
    fit_log_name = "NN_fit_log.log"
    
    LDA_model_name = "LDA_model.sav"
    NN_model_name = setup[key]["model_filename"]
    #NN_model_name = "NN.h5"

    try:
        NN_model = load_model(NN_model_name, custom_objects={'sae': sae})
    except:
        NN_model = load_model(NN_model_name)


    LDA_model = pickle.load(open("LDA_model.sav", 'rb'))

    setup[key]["NN_model"] = NN_model
    setup[key]["LDA_model"] = LDA_model


    os.chdir(setup[key]["working_dir"])

    with open("test_data_to_plot.pickle", 'rb') as handle:
        test_data = pickle.load(handle)

    setup[key]["test_X"] = test_data[0]
    setup[key]["test_y"] = test_data[1]
    setup[key]["test_dens"] = test_data[2]

    return


def process_one_model(setup,key):
    print "start: " + key
    initialize(setup,key)
    temp_predict_y, temp_error = predict(setup[key]["test_dens"],setup[key]["LDA_model"].x,setup[key]["test_X"],setup[key]["NN_model"],setup[key]["test_y"])
    setup[key]["predict_y"] = temp_predict_y
    setup[key]["error"] = temp_error
    print "end: " + key
    return temp_predict_y, temp_error



def create_df(setup):

    error_list = []
    dens_list = []
    log_dens_list = []
    y_list = []
    log_y_list = []
    dataset_name_list = []
    model_name_list = []
    model_list = []
    filename_list = []

    for model_name in setup:
        temp_len = len(setup[model_name]["test_y"])
        error_list += setup[model_name]["error"].flatten().tolist()
        dens_list  += setup[model_name]["test_dens"].flatten().tolist()
        log_dens_list += np.log10(setup[model_name]["test_dens"]).flatten().tolist()
        y_list += setup[model_name]["test_y"].flatten().tolist()
        log_y_list += np.log10(-1. * setup[model_name]["test_y"]).flatten().tolist()
        dataset_name_list += [setup[model_name]["dataset"]] * temp_len
        model_name_list += [model_name] * temp_len
        model_list += [setup[model_name]["model"]] * temp_len

    d = {"error": error_list, "dens": dens_list, "dataset":dataset_name_list, "model_name": model_name_list, "model":model_list}

    return pd.DataFrame(data=d)

if __name__ == "__main__":

    print "start"
    K.set_floatx('float64')
    K.floatx()
    try:
        with open('test_set_plot.pickle', 'rb') as handle:
            data = pickle.load(handle)

    except:
        from sklearn import linear_model
        from keras.models import Sequential
        from keras.models import load_model
        from keras.layers import Dense, Activation
        from keras import backend as K
        import keras
        
        setup_filename = sys.argv[1]

        with open(setup_filename) as f:
            setup = json.load(f)


        main_dir = os.getcwd()

        for key in setup:

            dir_name = "10-0_0-02_5"

            working_dir = os.getcwd() + '/' + dir_name + '/' + setup[key]["dataset"]
            setup[key]["working_dir"] = working_dir

            model_save_dir = working_dir + "/" + setup[key]["model"]
            setup[key]["model_save_dir"] = model_save_dir


        for key in setup:
            os.chdir(main_dir)
            process_one_model(setup,key)
        os.chdir(main_dir)

        data = create_df(setup)

        with open('test_set_plot.pickle', 'wb') as handle:
            pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)

    print "start ploting"

    plt.figure()
    
    sns.set(style="whitegrid", palette="pastel", color_codes=True)

    ax = sns.lmplot(x="dens",y="error",hue="model_name",data=data)

    plt.savefig("test_set_plot.png")