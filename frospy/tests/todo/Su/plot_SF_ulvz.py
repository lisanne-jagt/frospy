#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar  1 16:57:55 2020

@author: sujania
"""

import os
import glob
import pickle
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from os.path import join, basename, splitext
from obspy.core import AttribDict
from collections import OrderedDict
from frospy.postprocessing.uncertainties import uncertainties_calculation
from frospy.postprocessing.AnalyseRuns.plot import misfits_cst, listdir
from frospy.postprocessing import plot
from frospy.postprocessing.plot import inv_summary, cst
from frospy.postprocessing.read import read_inversion_summary
from frospy.postprocessing.misfit import plot_Qf
from frospy.core.splittingfunc import Set
from frospy.core.splittingfunc import loadmodel # python2 branch
#from frospy.splitting.load import loadmodel # python3 master branch
from frospy.core.splittingfunc.read import read_cst, get_cst, read_cst_S20RTS
from frospy.util.read import read_modes_in, get_mode_names
from frospy.util.base import sort_human 
from frospy.core.setup.settings import Setup, get_mode_list
from frospy.util.base import (chunking_list, split_digit_nondigit,
                            max_cc_degrees, max_sc_degrees)
from frospy.core.setup.settings import read as read_setup
from frospy.core.splittingfunc.plot import sens_kernel
import shapefile
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from matplotlib.patches import PathPatch
from matplotlib import gridspec

##f = "/Users/sujania/Documents/PhD/NotesUU/Dst/polygons/0s6.dat"
#f = "/data/talavera/notes/Dst/polygons/0s6.dat"
#input2 = OrderedDict() #AttribDict()
#input2['modes'] =  OrderedDict([("00s06",12)])
#input2['modes_sc_dst'] = OrderedDict([("00s06",12)])
#input2['startmodel'] = 'PREM'
#setup2=Setup('CST', input2)
#sf = loadmodel(setup=setup2, ifile = f, name = '0s6', damp = '0s6')    

master_db_path = '/net/home/talavera/eejit/data/mycst.sqlite3'
sf = Set()         


modes = [
#         ["0S2"],#LM
#         ["0S5"],#LM
#         ["0S6"],#LM
#         ["0S7"],#LM
#         ["1S4"],#LM
#         ["1S7"],#LM
#         ["1S8"],#LM
#         ["1S9"],#LM
#         ["1S10"],#LM
#         ["2S6"],#UM
#         ["2S12"],#UM
#         ["2S13"],#UM
#         ["3S6"],#UM
#         ["3S9"],#UM
#         ["0T6"],#UM
#         ["0T8"],#UM
#         ["0T9"],#UM
#         ["1T2"],#UM
#         ["1T5"],#LM
         ["2T3"],#LM
         ["2T7"],#LM
         ]

scut = [
#         [2,2], #0S2
#         [8,4], #0S5
#         [10,4], #0S6
#         [12,4], #0S7
#         [6,4], #1S4
#         [10,4], #1S7
#         [12,4], #1S8
#         [12,4], #1S9
#         [12,4], #1S10
#         [10,6], #2S6
#         [12,10], #2S12
#         [12,2], #2S13
#         [6,2], #3S6
#         [12,4], #3S9
#         [6,2], #0T6
#         [8,2], #0T8
#         [8,4], #0T9
#         [2,2], #1T2
#         [8,2], #1T5
         [6,4], #2T3
         [6,2], #2T7
         ]

db_model = 'dst'
for m,smax in zip(modes,scut):
#    print(m)
    sf = loadmodel(ifile=master_db_path, modes=m,
                   name=db_model, damp='0', db_model=db_model)    
    
    mdir = "/data/talavera/notes/Dst/ulvz_polygons/All.*.grd.txt"
    ifiles = glob.glob(mdir)
    fig = plt.figure(figsize=(8.5,5))
    ax = fig.add_subplot(122)
    ax1 = fig.add_subplot(121)
    gs = gridspec.GridSpec(1, 2, width_ratios=[0.8,3.2], wspace=0.05)
    ax0 = plt.subplot(gs[0])
    sens_kernel(sf.stats.modes_in[0], title=False, ax=ax0, ticks=False,
                fontsize=12, linewidth=1.5)
    ax = plt.subplot(gs[1])
    m = Basemap(projection='kav7',lon_0=0,resolution='c',ax=ax)    


    for i,f in enumerate(ifiles):
        name = f.split("/")[-1]
        f = open(f, 'r') 
        lines = f.read().splitlines()
        lines = lines[1::]
        for l in lines:
            l = l.split()
            if int(l[2]) == 1:
                x, y = m(float(l[0]),float(l[1]))
                if name == "All.yes.grd.txt":
                    ax.scatter(x,y,color="darkred",alpha=0.75,s=0.1,zorder=500)
                elif name == "All.may.grd.txt":
                    ax.scatter(x,y,color='r',alpha=0.65,s=0.1,zorder=300) 
                elif name == "All.no.grd.txt":
                    ax.scatter(x,y,color='gray',alpha=0.65,s=0.1,zorder=200)               
    sf.plot_map(
                ax=ax,
                fig=fig,
                smax=smax[1],
    #            smax=12,
                # R=-0.2,
    #             kind="dst",
    #             show_title=False,
                # legend_show=False, 
                )
    #
    #fig.savefig('cst',dpi=400,
    #              bbox_inches='tight',
    #              pad_inches=0.,)
    plt.show()