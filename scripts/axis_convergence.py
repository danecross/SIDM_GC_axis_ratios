
import os
import nbody6pp_out as nb

import numpy as np
from scipy.stats import norm

def extract_ratios(filepath, maxiter, lower_shell=0, upper_shell=1, is_2d=False, is_percentile=False):
    M=[] ; T=[] ; A = [] ; P = []
    if is_2d:
        m_last = [1,1] ; axes_last = np.identity(2)
    else:
        m_last = [1,1,1] ; axes_last = np.identity(3)

    i=0
    while i < maxiter:
        file_conf3 = filepath+"/conf.3_"+str(i)
        if not os.path.exists(file_conf3):
            i+=1
            continue

        t, _, _, p, _ = nb.read_conf3(file_conf3)
        
        #cut the desired stars
        HALF_MASS_RADIUS = np.median([np.sqrt(p[i][0]**2 + p[i][1]**2 + p[i][2]**2) for i in range(len(p))])
        p = get_stars(p, HALF_MASS_RADIUS, lower_shell, upper_shell, is_percentile)
        
        if is_2d:
            mm, axes = iterate_2D(p, converge_radius=10e-7, M_last=m_last, evecs_last=axes_last)
        else:
            mm, axes = iterate(p, converge_radius=10e-7, M_last=m_last, evecs_last=axes_last)
        
        M +=[mm] ; T += [t]
        m_last = mm ; axes_last = axes

        if i%30==0:
            print(i)
        i+=1

    return M, T

def get_stars(p, half_mass_radius, lower_shell=0, upper_shell=1, is_percentile=False):

    radii = [np.sqrt(x**2 + y**2 + z**2) for x,y,z in p]
    
    if is_percentile:
        sorted_stars = [pi for _,pi in sorted(zip(radii,p))]
        lower_index = int(lower_shell*len(p))
        upper_index = int(upper_shell*len(p))
        p_new = p[lower_index:upper_index]
    else:
        p_new = np.array([p[i] for i in range(len(p)) if radii[i] <= half_mass_radius*upper_shell\
                                                         and radii[i] >= half_mass_radius*lower_shell])
    

    return p_new

def _q_calc(x, y, z, M):
    
    M.sort()
    ac = np.sqrt(M[0]/M[2])
    bc = np.sqrt(M[1]/M[2])

    return np.array([np.sqrt(x[i]**2 + (y[i]/ac)**2 + (z[i]/bc)**2) for i in range(len(z))])

def _M_calc(p, q):

    M = np.zeros((3, 3))
       
    M[0,0] = np.sum(p[:,0]*p[:,0]/q**2)
    M[0,1] = np.sum(p[:,0]*p[:,1]/q**2)
    M[0,2] = np.sum(p[:,0]*p[:,2]/q**2)
    M[1,1] = np.sum(p[:,1]*p[:,1]/q**2)
    M[1,2] = np.sum(p[:,1]*p[:,2]/q**2)
    M[2,2] = np.sum(p[:,2]*p[:,2]/q**2)

    M[1,0]=M[0,1] ; M[2,0]=M[0,2] ; M[2,1]=M[1,2]

    eigenvalues, eigenvectors = np.linalg.eig(M)
        
    return np.array(eigenvalues), eigenvectors

def _rotate_coords(evecs, p, is_2d=False):
    if is_2d:
        vec_new = [np.linalg.inv(np.array(evecs)).dot(coord) for coord in p[:,:2]]
    else:
        vec_new = [np.linalg.inv(np.array(evecs)).dot(coord) for coord in p]
    return np.array(vec_new)

def iterate(p, M_last=[1, 1, 1], evecs_last=np.identity(3), maxiter=25, converge_radius=10e-4):
    #starting points
    M = [1, .1, .1]
    p = _rotate_coords(evecs_last, p)
    q = _q_calc(p[:,0], p[:,1], p[:,2], M_last)

    # re-center coordinates
    center = [np.average(p[:,0]), np.average(p[:,1]), np.average(p[:,2])]
    p = np.array([[p[i,0]-center[0], p[i,1]-center[1], p[i,2]-center[2]] for i in range(len(p))])

    #iterate:
    i = 0
    while (np.abs((M[1]/M[0])-(M_last[1]/M_last[0]))>converge_radius\
          or np.abs((M[2]/M[0])-(M_last[2]/M_last[0])) > converge_radius)\
          and i < maxiter:
        M_last = M
        M, evecs = _M_calc(p, q)
        q_last = q
        p = _rotate_coords(evecs, p)
        q = _q_calc(p[:,0], p[:,1], p[:,2], M)
        i+=1 

    return M, evecs

def iterate_2D(p, M_last=[1, 1], evecs_last=np.identity(2), maxiter=25, converge_radius=10e-4):
   
    M = [1, .1]  
    p = _rotate_coords(evecs_last, p, is_2d=True)
    q = _q_calc_2d(p[:,0], p[:,1], M_last)

    #recenter coordinates
    center = [np.average(p[:,0]), np.average(p[:,1])]
    p = np.array([[p[i,0]-center[0], p[i,1]-center[1]] for i in range(len(p))])

    #iterate
    i = 0 
    while np.abs((M[1]/M[0])-(M_last[1]/M_last[0]))>converge_radius and i < maxiter:
        M_last = M
        M, evecs = _M_calc_2d(p, q)
        q_last = q
        p = _rotate_coords(evecs, p, is_2d=True)
        q = _q_calc_2d(p[:,0], p[:,1], M)
        i+=1

    return M, evecs

def _q_calc_2d(x, y, M):
    M.sort()
    ab = np.sqrt(M[0]/M[1])

    return np.array([np.sqrt(x[i]**2 + (y[i]/ab)**2) for i in range(len(x))])

def _M_calc_2d(p, q):

    M = np.zeros((2, 2))

    M[0,0] = np.sum(p[:,0]*p[:,0]/q**2)
    M[0,1] = np.sum(p[:,0]*p[:,1]/q**2)
    M[1,0]=M[0,1] 
    M[1,1] = np.sum(p[:,1]*p[:,1]/q**2)

    eigenvalues, eigenvectors = np.linalg.eig(M)

    return np.array(eigenvalues), eigenvectors



















