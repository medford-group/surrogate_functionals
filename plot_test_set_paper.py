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


def predict_svwn(n,LDA_x,y):

    dens = n

    predict_y = predict_LDA(n,LDA_x)

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
    
def initialize_svwn(setup,key):
    os.chdir(setup[key]["model_save_dir"])
    fit_log_name = "NN_fit_log.log"
    
    LDA_model_name = "LDA_model.sav"
    #NN_model_name = "NN.h5"


    LDA_model = pickle.load(open("LDA_model.sav", 'rb'))

    setup["refit VWN"]["LDA_model"] = LDA_model
    setup["refit VWN"]["model"] = "refitted_SVWN"
    setup["refit VWN"]["dataset"] = "epxc_refitted_SVWN"

    os.chdir(setup[key]["working_dir"])

    with open("test_data_to_plot.pickle", 'rb') as handle:
        test_data = pickle.load(handle)

    setup["refit VWN"]["test_X"] = test_data[0]
    setup["refit VWN"]["test_y"] = test_data[1]
    setup["refit VWN"]["test_dens"] = test_data[2]

    return


def process_one_model(setup,key):
    print "start: " + key
    initialize(setup,key)
    temp_predict_y, temp_error = predict(setup[key]["test_dens"],setup[key]["LDA_model"].x,setup[key]["test_X"],setup[key]["NN_model"],setup[key]["test_y"])
    setup[key]["predict_y"] = temp_predict_y
    setup[key]["error"] = temp_error
    print "end: " + key
    return temp_predict_y, temp_error
    
    
def process_svwn_model(setup,key):
    print "start: SVWN"
    initialize_svwn(setup,key)
    temp_predict_y, temp_error = predict_svwn(setup["refit VWN"]["test_dens"],setup["refit VWN"]["LDA_model"].x,setup["refit VWN"]["test_y"])
    setup["refit VWN"]["predict_y"] = temp_predict_y
    setup["refit VWN"]["error"] = temp_error
    print "end: SVWN"
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

    d = {"error": error_list, "dens": dens_list, "dataset":dataset_name_list, "model_name": model_name_list, "model":model_list, "log_y":log_y_list, "log_dens":log_dens_list, "y":y_list}

    return pd.DataFrame(data=d)
    
def plot_group_1(data,order):
    colors = ["windows blue", "amber", "greyish", "faded green", "dusty purple"]

    plt.figure()
    
    sns.set(style="white", palette="pastel", color_codes=True)

    ax = sns.lmplot(x="dens",y="error",hue="model_name",hue_order = order,data=data,legend=False,fit_reg=False,size=20,scatter_kws={"s": 40}, palette=("Dark2"))
    plt.xlabel("Density (1/A$^3$)",fontsize=50)
    plt.ylabel("Prediction Error (eV/A$^3$)",fontsize=50)
    plt.tick_params(labelsize=40)
    lgnd = plt.legend(order,fontsize=40)
    
    print lgnd.legendHandles[0]

    for i in range(len(lgnd.legendHandles)):
        lgnd.legendHandles[i]._sizes = [500]

    #lgnd.legendHandles[0]._sizes = [500]
    #lgnd.legendHandles[1]._sizes = [500]
    #lgnd.legendHandles[2]._sizes = [500]
    #lgnd.legendHandles[3]._sizes = [500]
    #lgnd.legendHandles[4]._sizes = [500]
    #lgnd.legendHandles[4]._sizes = [500]

    plt.tight_layout()
    plt.savefig("test_set_plot_real_real.png")
    
    
    plt.figure()
    
    sns.set(style="white", palette="pastel", color_codes=True)

    ax = sns.FacetGrid(data, hue="model_name",col="model_name")
    ax = (ax.map(plt.scatter, "dens","error", edgecolor="w"))

    #ax = sns.lmplot(x="dens",y="error",hue="model_name",data=data,legend=False,fit_reg=False,size=20,scatter_kws={"s": 40}, palette=("Dark2"))
    #plt.xlabel("Density (1/A$^3$)",fontsize=50)
    #plt.ylabel("Presiction Error (eV/A$^3$)",fontsize=50)
    #plt.tick_params(labelsize=40)
    #lgnd = plt.legend(["Model 1", "Model 2", "Model 3", "Model 4", "Model 5"],fontsize=40)
    
    #print lgnd.legendHandles

    #lgnd.legendHandles[0]._sizes = [500]
    #lgnd.legendHandles[1]._sizes = [500]
    #lgnd.legendHandles[2]._sizes = [500]
    #lgnd.legendHandles[3]._sizes = [500]
    #lgnd.legendHandles[4]._sizes = [500]

    #plt.tight_layout()
    plt.savefig("test_set_plot_real_real2.png")
    
    
    
    
    
    
    #g = sns.FacetGrid(df, col="group", hue="group")
    #g = (g.map(plt.scatter, "x", "y", edgecolor="w"))
    
   
        
    plt.figure(figsize=(10,5))
    
    sns.set(style="white", palette="pastel", color_codes=True)

    ax = sns.lmplot(x="dens",y="error",hue="model_name",hue_order = order,data=data,legend=False,fit_reg=False,size=10,aspect=2,scatter_kws={"s": 40}, palette=("Dark2"))
    ax.fig.get_axes()[0].set_xscale('log')
    ax.fig.get_axes()[0].set_xlim(1e-9, 1000)
    plt.xlabel("Density (1/A$^3$)",fontsize=50)
    plt.ylabel("Prediction Error (eV/A$^3$)",fontsize=50)
    plt.tick_params(labelsize=40)
    lgnd = plt.legend(order,fontsize=40,loc="upper left")
    
    print lgnd.legendHandles[0]

    for i in range(len(lgnd.legendHandles)):
        lgnd.legendHandles[i]._sizes = [500]

    #lgnd.legendHandles[0]._sizes = [500]
    #lgnd.legendHandles[1]._sizes = [500]
    #lgnd.legendHandles[2]._sizes = [500]
    #lgnd.legendHandles[3]._sizes = [500]
    #lgnd.legendHandles[4]._sizes = [500]
    #lgnd.legendHandles[4]._sizes = [500]

    plt.tight_layout()
    plt.savefig("test_set_plot_log_real.png", transparent=True)
    
    
    
    
    
    
    
    plt.figure()
    
    sns.set(style="white", palette="pastel", color_codes=True)

    ax = sns.lmplot(x="dens",y="error",hue="model_name",data=data,legend=False,fit_reg=False,size=20,scatter_kws={"s": 40}, palette=("Dark2"))
    ax.fig.get_axes()[0].set_xscale('log')
    ax.fig.get_axes()[0].set_yscale('symlog')
    print ax.fig.get_axes()[0].get_ylim()
    ax.fig.get_axes()[0].set_xlim(1e-9, 1000)
    plt.xlabel("Density (1/A$^3$)",fontsize=50)
    plt.ylabel("Prediction Error (eV/A$^3$)",fontsize=50)
    plt.tick_params(labelsize=40)
    lgnd = plt.legend(order,fontsize=40)
    
    print lgnd.legendHandles[0]

    for i in range(len(lgnd.legendHandles)):
        lgnd.legendHandles[i]._sizes = [500]

    #lgnd.legendHandles[0]._sizes = [500]
    #lgnd.legendHandles[1]._sizes = [500]
    #lgnd.legendHandles[2]._sizes = [500]
    #lgnd.legendHandles[3]._sizes = [500]
    #lgnd.legendHandles[4]._sizes = [500]
    #lgnd.legendHandles[4]._sizes = [500]

    plt.tight_layout()
    plt.savefig("test_set_plot_log_symlog.png")
    
    
    
    
    
    
    plt.figure()
    
    sns.set(style="white", palette="pastel", color_codes=True)

    ax = sns.lmplot(x="dens",y="error",hue="model_name",data=data,legend=False,fit_reg=False,size=20,scatter_kws={"s": 40}, palette=("Dark2"))
    ax.fig.get_axes()[0].set_xscale('log')
    ax.fig.get_axes()[0].set_yscale('symlog')
    print ax.fig.get_axes()[0].get_ylim()
    ax.fig.get_axes()[0].set_xlim(1e-6, 0.1)
    ax.fig.get_axes()[0].set_ylim(-0.001, 0.001)
    plt.xlabel("Density (1/A$^3$)",fontsize=50)
    plt.ylabel("Prediction Error (eV/A$^3$)",fontsize=50)
    plt.tick_params(labelsize=40)
    #lgnd = plt.legend(["Model 1", "Model 2", "Model 3", "Model 4", "Model 5"],fontsize=40)
    
    #print lgnd.legendHandles[0]

    #lgnd.legendHandles[0]._sizes = [500]
    #lgnd.legendHandles[1]._sizes = [500]
    #lgnd.legendHandles[2]._sizes = [500]
    #lgnd.legendHandles[3]._sizes = [500]
    #lgnd.legendHandles[4]._sizes = [500]

    plt.tight_layout()
    plt.savefig("test_set_plot_log_symlog2.png")


def get_intervals(li):
    result = []
    median_result = []
    
    for i in range(len(li)-1):
        result.append([li[i],li[i+1]])
        median_result.append((li[i]+li[i+1])/2.0)
    
    return result, median_result
  
 

def plot_group_2(data):
    sns.set(font_scale = 2)
    plt.figure()
    sns.set(style="white", palette="pastel", color_codes=True)
    #ax = sns.distplot(data["dens"],bw=.0015)
    #ax.fig.get_axes()[0].set_xscale('log')
    ax = sns.distplot(data["dens"],bins=100,kde=True,hist_kws={"linewidth": 0,"alpha": 1},kde_kws={"color": "k", "lw": 0})
    plt.savefig("test_set_plot_dens_dist_real.png")
    
    plt.figure(figsize=(10,3.5))
    sns.set(style="white", palette="pastel", color_codes=True)
    #ax = sns.distplot(data["log_dens"],bw=.0015)
    #ax.fig.get_axes()[0].set_xscale('log')
    ax = sns.distplot(data["log_dens"],bins=100,kde=True,hist_kws={ "linewidth": 0,"alpha": 1},kde_kws={"color": "k", "lw": 0})
    ax.set_xlim(-9.,3.)
    plt.savefig("test_set_plot_dens_dist_log.png")
    
    
    number_models = data['model_name'].nunique()
    
    
    
    
    dens_max = data["dens"].max()
    dens_min = data["dens"].min()
    
    dens_intervals,dens_interval_medians = get_intervals(np.linspace(dens_min,dens_max, num=100))
    
    
    
    groups = data.groupby("model_name")
    
    fig = plt.figure()
    sns.set(style="white", color_codes=True)
    current_palette = sns.color_palette("cubehelix", number_models)
    sns.set_palette(current_palette)
    for name, group in groups:
        print name
        if name == "refit VWN":
            sum_error_result = []
            for count, interval in enumerate(dens_intervals):
	        temp = group[ (group['dens'] >= interval[0]) & (group['dens'] < interval[1])]
	        sum_error_result.append(temp['error'].sum())

            plt.plot(dens_interval_medians, sum_error_result,label=name)
    for name, group in groups:
        print name
        if name != "refit VWN":
            sum_error_result = []
            for count, interval in enumerate(dens_intervals):
	        temp = group[ (group['dens'] >= interval[0]) & (group['dens'] < interval[1])]
	        sum_error_result.append(temp['error'].sum())

            plt.plot(dens_interval_medians, sum_error_result,label=name)
    #ax.fig.get_axes()[0].set_xscale('log')
    plt.legend(["0","1", "2", "3", "4", "5"], loc='upper right')
    plt.savefig("test_set_plot_dens_sumerror_real_real.png")
    
    
    
    
    
    
    dens_max = data["dens"].max()
    dens_min = data["dens"].min()
    
    dens_intervals,dens_interval_medians = get_intervals(np.linspace(dens_min,dens_max, num=100))
    
    
    
    groups = data.groupby("model_name")
    
    fig = plt.figure()
    sns.set(style="white", color_codes=True)
    current_palette = sns.color_palette("cubehelix", number_models)
    sns.set_palette(current_palette)
    for name, group in groups:
        if name == "refit VWN":
            sum_error_result = []
            for count, interval in enumerate(dens_intervals):
	        temp = group[ (group['dens'] >= interval[0]) & (group['dens'] < interval[1])]
	        sum_error_result.append(temp['error'].sum())

            plt.plot(dens_interval_medians, sum_error_result,label=name)
    for name, group in groups:
        if name != "refit VWN":
            sum_error_result = []
            for count, interval in enumerate(dens_intervals):
	        temp = group[ (group['dens'] >= interval[0]) & (group['dens'] < interval[1])]
	        sum_error_result.append(temp['error'].sum())

            plt.plot(dens_interval_medians, sum_error_result,label=name)
    fig.get_axes()[0].set_yscale('symlog')
    plt.legend(["0","1", "2", "3", "4", "5"],loc='upper right')
    plt.savefig("test_set_plot_dens_sumerror_real_symlog.png")
    
    
    
    
    
    
    
    
    log_dens_max = data["log_dens"].max()
    log_dens_min = data["log_dens"].min()
    
    log_dens_intervals,log_dens_interval_medians = get_intervals(np.linspace(log_dens_min,log_dens_max, num=100))
    
    
    
    groups = data.groupby("model_name")
    
    fig = plt.figure(figsize=(10,3.5))
    sns.set(style="white", color_codes=True)
    current_palette = sns.color_palette("cubehelix", number_models)
    print current_palette
    sns.set_palette(current_palette)
    for name, group in groups:
        if name == "refit VWN":
            log_sum_error_result = []
            for count, interval in enumerate(log_dens_intervals):
	        temp = group[ (group['log_dens'] >= interval[0]) & (group['log_dens'] < interval[1])]
	        log_sum_error_result.append(temp['error'].sum())

            plt.plot(log_dens_interval_medians, log_sum_error_result,label=name,linewidth=5.0)
    for name, group in groups:
        if name != "refit VWN":
            log_sum_error_result = []
            for count, interval in enumerate(log_dens_intervals):
	        temp = group[ (group['log_dens'] >= interval[0]) & (group['log_dens'] < interval[1])]
	        log_sum_error_result.append(temp['error'].sum())

            plt.plot(log_dens_interval_medians, log_sum_error_result,label=name,linewidth=5.0)
    #ax.fig.get_axes()[0].set_xscale('log')
    plt.legend(["0","1", "2", "3", "4", "5"],loc='upper left',fontsize=15)
    
    
    #plt.xlabel(r"$log_{10} (\rho)$",fontsize=20)
    plt.xlabel("",fontsize=0)
    plt.ylabel("Error (eV)",fontsize=20)
    plt.tick_params(axis='y', labelsize=20)
    plt.tick_params(axis='x', labelsize=0)
    plt.xlim(-9,3)
    plt.tight_layout()
    plt.savefig("test_set_plot_dens_sumerror_log_real.png", transparent=True)
    
    
    
    
    
    
    log_dens_max = data["log_dens"].max()
    log_dens_min = data["log_dens"].min()
    
    log_dens_intervals,log_dens_interval_medians = get_intervals(np.linspace(log_dens_min,log_dens_max, num=100))
    
    
    
    groups = data.groupby("model_name")
    
    fig = plt.figure()
    sns.set(style="white", color_codes=True)
    current_palette = sns.color_palette("cubehelix", number_models)
    sns.set_palette(current_palette)
    for name, group in groups:
        if name == "refit VWN":
            log_sum_error_result = []
            for count, interval in enumerate(log_dens_intervals):
	        temp = group[ (group['log_dens'] >= interval[0]) & (group['log_dens'] < interval[1])]
	        log_sum_error_result.append(temp['error'].sum())

            plt.plot(log_dens_interval_medians, log_sum_error_result,label=name)
    for name, group in groups:
        if name != "refit VWN":
            log_sum_error_result = []
            for count, interval in enumerate(log_dens_intervals):
	        temp = group[ (group['log_dens'] >= interval[0]) & (group['log_dens'] < interval[1])]
	        log_sum_error_result.append(temp['error'].sum())

            plt.plot(log_dens_interval_medians, log_sum_error_result,label=name)
    fig.get_axes()[0].set_yscale('symlog')
    plt.legend(["0","1", "2", "3", "4", "5"],loc='upper left')
    plt.savefig("test_set_plot_dens_sumerror_log_symlog.png")
    
    

    
    
    return
    
    
    
    
def plot_group_3(data):

    fig, axes = plt.subplots(1, 3, figsize=(20, 60), sharex=True, sharey=True)
    
    sns.set(style="white", color_codes=True)
    current_palette = sns.color_palette("cubehelix", 6)
    sns.set_palette(current_palette)
    
    ax1, ax2, ax3 = axes.flat
    
    sns.regplot(x="dens",y="error",hue="model_name",hue_order = ["SVWN","1","2","3","4","5"],data=data,legend=False,fit_reg=False,size=20,scatter_kws={"s": 40}, palette=("cubehelix", 6),ax=ax1)
    plt.xlabel("Density (1/A$^3$)",fontsize=50)
    plt.ylabel("Prediction Error (eV/A$^3$)",fontsize=50)
    plt.tick_params(labelsize=40)
    lgnd = plt.legend(["Refitted SVWN","Model 1", "Model 2", "Model 3", "Model 4", "Model 5"],fontsize=40)
    
    print lgnd.legendHandles[0]

    lgnd.legendHandles[0]._sizes = [500]
    lgnd.legendHandles[1]._sizes = [500]
    lgnd.legendHandles[2]._sizes = [500]
    lgnd.legendHandles[3]._sizes = [500]
    lgnd.legendHandles[4]._sizes = [500]
    lgnd.legendHandles[5]._sizes = [500]

    plt.tight_layout()
    plt.savefig("test_set_combined_plot_real_real.png")
    
    
def plot_group_4(data):
    fig, ax = plt.subplots()
    ax.plot(np.random.rand(10))
    ax2 =ax.twinx()

    ax = sns.distplot(data["log_dens"],bins=100,kde=True,hist_kws={ "linewidth": 0,"alpha": 1},kde_kws={"color": "k", "lw": 0})


    log_dens_max = data["log_dens"].max()
    log_dens_min = data["log_dens"].min()
    
    log_dens_intervals,log_dens_interval_medians = get_intervals(np.linspace(log_dens_min,log_dens_max, num=100))
    
    
    
    groups = data.groupby("model_name")
    
    fig = plt.figure()
    sns.set(style="white", color_codes=True)
    current_palette = sns.color_palette("cubehelix", number_models)
    sns.set_palette(current_palette)
    for name, group in groups:
        if name == "refit VWN":
            log_sum_error_result = []
            for count, interval in enumerate(log_dens_intervals):
	        temp = group[ (group['log_dens'] >= interval[0]) & (group['log_dens'] < interval[1])]
	        log_sum_error_result.append(temp['error'].sum())

            plt.plot(log_dens_interval_medians, log_sum_error_result,label=name)
    for name, group in groups:
        if name != "refit VWN":
            log_sum_error_result = []
            for count, interval in enumerate(log_dens_intervals):
	        temp = group[ (group['log_dens'] >= interval[0]) & (group['log_dens'] < interval[1])]
	        log_sum_error_result.append(temp['error'].sum())

            plt.plot(log_dens_interval_medians, log_sum_error_result,label=name)
    #ax.fig.get_axes()[0].set_xscale('log')
    plt.legend(["0","1", "2", "3", "4", "5"],loc='upper left')
    plt.savefig("test_set_plot_test_test.png")
    

if __name__ == "__main__":

    print "start"
    
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
        import keras.backend as K
        K.set_floatx('float64')
        K.floatx()
        
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
        setup["refit VWN"] = {}
        try:
            process_svwn_model(setup,"LDA")
        except:
            process_svwn_model(setup,"LDA")
        os.chdir(main_dir)

        data = create_df(setup)

        with open('test_set_plot.pickle', 'wb') as handle:
            pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)

    print "start ploting"

    order_filename = sys.argv[2]


    with open(order_filename) as f:
        temp_order = json.load(f)
    order = temp_order["order"]
    
    plot_group_1(data,order)
