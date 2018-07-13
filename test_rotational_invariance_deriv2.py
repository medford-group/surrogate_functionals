import numpy as np
from convolutions import get_differenciation_conv, get_integration_stencil,get_auto_accuracy,get_fftconv_with_known_stencil_no_wrap,get_asym_integration_stencil,get_asym_integration_fftconv,get_asym_integral_fftconv_with_known_stencil
from convolutions import get_first_grad_stencil, get_second_grad_stencil, get_third_grad_stencil
import itertools
from math import cos,sin,tan,acos,asin,pi,exp,pow
import itertools
import pandas as pd
import seaborn as sns

import sys
import matplotlib
#matplotlib.use('Agg') 
import matplotlib.cm as cm
from mpl_toolkits.mplot3d import Axes3D
import mpl_toolkits.mplot3d.axes3d as p3
import matplotlib.pyplot as plt

def generate(dim):
    """Generate a random rotation matrix.

    https://github.com/qobilidop/randrot

    Args:
        dim (int): The dimension of the matrix.

    Returns:
        np.matrix: A rotation matrix.

    Raises:
        ValueError: If `dim` is not 2 or 3.

    """
    if dim == 2:
        return generate_2d()
    elif dim == 3:
        return generate_3d()
    else:
        raise ValueError('Dimension {} is not supported. Use 2 or 3 instead.'
                         .format(dim))


def generate_2d():
    """Generate a 2D random rotation matrix.

    Returns:
        np.matrix: A 2D rotation matrix.

    """
    x = np.random.random()
    M = np.matrix([[np.cos(2 * np.pi * x), -np.sin(2 * np.pi * x)],
                   [np.sin(2 * np.pi * x), np.cos(2 * np.pi * x)]])
    return M


def generate_3d():
    """Generate a 3D random rotation matrix.

    Returns:
        np.matrix: A 3D rotation matrix.

    """
    #x1, x2, x3 = np.random.rand(3)
    x1, x2, x3 = (0.25, 0.25, 0.25)
    R = np.matrix([[np.cos(2 * np.pi * x1), np.sin(2 * np.pi * x1), 0],
                   [-np.sin(2 * np.pi * x1), np.cos(2 * np.pi * x1), 0],
                   [0, 0, 1]])
    v = np.matrix([[np.cos(2 * np.pi * x2) * np.sqrt(x3)],
                   [np.sin(2 * np.pi * x2) * np.sqrt(x3)],
                   [np.sqrt(1 - x3)]])
    H = np.eye(3) - 2 * v * v.T
    M = -H * R
    return M

def generate_3d2(x1, x2, x3):

    R = np.matrix([[np.cos(2 * np.pi * x1), np.sin(2 * np.pi * x1), 0],
                   [-np.sin(2 * np.pi * x1), np.cos(2 * np.pi * x1), 0],
                   [0, 0, 1]])
    v = np.matrix([[np.cos(2 * np.pi * x2) * np.sqrt(x3)],
                   [np.sin(2 * np.pi * x2) * np.sqrt(x3)],
                   [np.sqrt(1 - x3)]])
    H = np.eye(3) - 2 * v * v.T
    M = -H * R
    return M

def rotate_coord_mat2(x,y,z,theta1,theta2,theta3):
	#rot_mat = generate(3)
	#rot_mat = np.eye(3)
	rot_mat = generate_3d2(theta1,theta2,theta3) 
	temp_shape = x.shape
	temp_coord = np.stack([x.copy().flatten(),y.copy().flatten(),z.copy().flatten()], axis=0)
	after_rotate = np.asarray(np.dot(rot_mat,temp_coord))

	x_res = after_rotate[0].reshape(temp_shape)
	y_res = after_rotate[1].reshape(temp_shape)
	z_res = after_rotate[2].reshape(temp_shape)

	#fig = plt.figure()
	#ax = fig.add_subplot(111, projection='3d')
	#ax.scatter(x_res, y_res, z_res, c='k')
	#plt.show()


	return x_res, y_res , z_res 


def f(x,y,z,sig_x,sig_y,sig_z,x0,y0,z0):

	#return np.exp(-(np.square(x.copy()-x0)/(2.0*sig_x*sig_x)) -(np.square(y.copy()-y0)/(2.0*sig_y*sig_y)) -(np.square(z.copy()-z0)/(2.0*sig_z*sig_z))  )
	return np.exp(-np.divide(np.square(x.copy()),(2.0*sig_x*sig_x)) - np.divide(np.square(y.copy()),(2.0*sig_y*sig_y)) - np.divide(np.square(z.copy()),(2.0*sig_z*sig_z))  )


def f2(x,y,z,sig_x,sig_y,sig_z,x0,y0,z0):

	result = np.zeros_like(x)

	for index, temp in np.ndenumerate(x):
		temp1 = pow((x[index] - x0),2) / (2.0*sig_x*sig_x)
		temp2 = pow((y[index] - y0),2) / (2.0*sig_y*sig_y)
		temp3 = pow((z[index] - z0),2) / (2.0*sig_z*sig_z)
		result[index] = exp(-temp1 - temp2 - temp3)
	return result

def f3(x,y,z,sig_x,sig_y,sig_z,x0,y0,z0):
	return np.sin(sig_x * (x-x0)) * np.sin(sig_y * (y-y0)) * np.sin(sig_z * (z-z0))


def rotate_coord_mat(x,y,z,theta1,theta2,theta3):
	x_result = x
	y_result = y
	z_result = z

	x_result = x_result
	y_result = y_result*cos(theta1) - z_result*sin(theta1)
	z_result = y_result*sin(theta1) + z_result*cos(theta1)

	x_result = x_result*cos(theta2) + z_result*sin(theta2)
	y_result = y_result
	z_result = z_result*cos(theta2) - x_result*sin(theta2)

	x_result = x_result*cos(theta3) - y_result*sin(theta3)
	y_result = x_result*sin(theta3) + y_result*cos(theta3)
	z_result = z_result

	return x_result,y_result,z_result

def get_result(x_temp, y_temp, z_temp,sig_x,sig_y,sig_z,x0,y0,z0, h, stencil, pad):

	n = f(x_temp, y_temp, z_temp,sig_x,sig_y,sig_z,x0,y0,z0)

	temp,_ = get_fftconv_with_known_stencil_no_wrap(n,h,h,h,1,stencil,pad)


	#fig = plt.figure()
	#cmap = plt.get_cmap("bwr")
	#ax = fig.add_subplot(111, projection='3d')
	#ax.scatter(x_temp, y_temp, z_temp, c=n, cmap=cmap,linewidths=0,s=10.0)
	#plt.show()

	return abs(temp[(temp.shape[0]-1)/2, (temp.shape[1]-1)/2, (temp.shape[2]-1)/2]) / n[(n.shape[0]-1)/2, (n.shape[1]-1)/2, (n.shape[2]-1)/2]

def plot_result(data):
	plt.figure()
		
	sns.set(style="whitegrid", palette="pastel", color_codes=True)

	ax = sns.violinplot(x="order",y="percent_error",data=data)
	plt.tight_layout()
	plt.savefig("deriv_rotational_invariance_test_percent_error.png")


	plt.figure()
		
	sns.set(style="whitegrid", palette="pastel", color_codes=True)

	ax = sns.violinplot(x="order",y="error",data=data)
	plt.tight_layout()
	plt.savefig("deriv_rotational_invariance_test_error.png")


	plt.figure()
	
	sns.set(style="whitegrid", palette="pastel", color_codes=True)

	ax = sns.violinplot(x="order",y="log_percent_error",data=data)
	plt.tight_layout()
	plt.savefig("deriv_rotational_invariance_test_percent_error_log.png")


	plt.figure()
		
	sns.set(style="whitegrid", palette="pastel", color_codes=True)

	ax = sns.violinplot(x="order",y="log_error",data=data)
	plt.tight_layout()
	plt.savefig("deriv_rotational_invariance_test_error_log.png")



	return


#r = float(sys.argv[1])
num_rot = int(sys.argv[1])
num_grid = int(sys.argv[2])
nx, ny, nz = (25,25,25)
h = 0.02

temp_x = (float(nx)-1.0)*h/2.0
temp_y = (float(ny)-1.0)*h/2.0
temp_z = (float(nz)-1.0)*h/2.0


xv = np.linspace(-temp_x,temp_x,nx)
yv = np.linspace(-temp_y,temp_y,ny)
zv = np.linspace(-temp_z,temp_z,nz)

x, y, z = np.meshgrid(xv, yv, zv)
#x,y,z = rotate_coord_mat2(x1,y1,z1)

#x0,y0,z0 = (0.0,0.0,0.0)

#x0,y0,z0 = (np.random.uniform(-0.3, 0.3), np.random.uniform(-0.3, 0.3), np.random.uniform(-0.3, 0.3))
#sig_x = 0.2
#sig_y = 0.8
#sig_z = 0.4
sig_x = np.random.uniform(0.05, 0.3)
sig_y = np.random.uniform(0.05, 0.3)
sig_z = np.random.uniform(0.05, 0.3)

#stencil,pad = get_integration_stencil(h, h, h, r, accuracy = get_auto_accuracy(h,h,h, r))
#truth = get_result(x,y,z,sig_x,sig_y,sig_z,x0,y0,z0, h, r, stencil, pad)

result_percent_error_list = []
result_error_list = []
gradient_list = []
theta1_list = []
theta2_list = []
theta3_list = []

temp_x0_list = np.linspace(-0.5, 0.5, num_grid)
temp_y0_list = np.linspace(-0.5, 0.5, num_grid) 
temp_z0_list = np.linspace(-0.5, 0.5, num_grid) 
origin_list = list(itertools.product(temp_x0_list,temp_y0_list,temp_z0_list))

counter_origin = 0
for x0, y0, z0 in origin_list:
	counter_origin +=1 
	for gradient, stencil_type in [("first","mid"), ("second","times2")]:


		if gradient == 'first':
			stencil, Gx, Gy, Gz, pad = get_first_grad_stencil(h, h, h, 
	                                                    stencil_type = stencil_type, 
	                                                    accuracy = '2')
		elif gradient == 'second':
			stencil, Gx, Gy, Gz, pad = get_second_grad_stencil(h, h, h, 
	                                                    stencil_type = stencil_type, 
	                                                    accuracy = '2')                    
		elif gradient == 'third':
			stencil, Gx, Gy, Gz, pad = get_third_grad_stencil(h, h, h, 
	                                                    stencil_type = stencil_type, 
	                                                    accuracy = '2') 



		truth = get_result(x,y,z,sig_x,sig_y,sig_z,x0,y0,z0, h, stencil, pad)

		theta1 = theta2 = theta3 = 0.0
		temp_theta1_list = np.linspace(0.0, 1.0, num_rot)
		temp_theta2_list = np.linspace(0.0, 1.0, num_rot) 
		temp_theta3_list = np.linspace(0.0, 1.0, num_rot) 
		paramlist = list(itertools.product(temp_theta1_list,temp_theta2_list,temp_theta3_list))
	    
		counter = 0
		for theta1, theta2, theta3 in paramlist:
			counter +=1

			x_temp, y_temp, z_temp = rotate_coord_mat2(x.copy(),y.copy(),z.copy(),theta1,theta2,theta3)
			error = get_result(x_temp, y_temp, z_temp,sig_x,sig_y,sig_z,x0,y0,z0, h, stencil, pad) - truth
			print "origin:{}\t{}\t{}\t{}\t{}\t{}".format(counter_origin,counter,gradient,error/truth, truth, error)

			result_percent_error_list.append(error/truth)
			result_error_list.append(error)
			gradient_list.append(str(gradient))
			theta1_list.append(str(theta1))
			theta2_list.append(str(theta2))
			theta3_list.append(str(theta3))

	d = {"order":gradient_list, "error":result_error_list, "percent_error":result_percent_error_list,"log_error": np.log10(np.abs(result_error_list)).tolist(), "log_percent_error": np.log10(np.abs(result_percent_error_list)).tolist(), "theta1":theta1_list, "theta2":theta2_list, "theta3": theta3_list}
	data = pd.DataFrame(data=d)
	plot_result(data)





