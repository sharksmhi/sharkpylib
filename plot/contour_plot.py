# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

#import matplotlib
#import matplotlib.pyplot as plt
# plt.style.use('ggplot')
#matplotlib.use(u'TkAgg')

#from mpl_toolkits.axes_grid1 import host_subplot
#import mpl_toolkits.axisartist as axisartist
import matplotlib
from matplotlib.figure import Figure
#from matplotlib.widgets import Cursor

from matplotlib.widgets import LassoSelector
from matplotlib.path import Path

#from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import tkinter as tk
from tkinter import ttk

import random
import numpy as np
import datetime
import matplotlib.dates as dates
import matplotlib.dates as mdates
import pandas as pd


class PlotContour(object):
    
    #===========================================================================
    def __init__(self,
                 orientation='vertical',
                 hover_target=None,
                 **kwargs):

        
        if orientation in ['v', 'vertical']:
            self.vertical_orientation = True
        else:
            self.vertical_orientation = False

        self.event_dict = {}
        self.targets = []

        self.hover_target = hover_target

        self.legend = None

        self.prop_fig = kwargs
        self._setup_figure()
        # self._add_event_hover()

    #===========================================================================
    def _setup_figure(self):
        self.fig = Figure(**self.prop_fig)
        self.ax = self.fig.add_subplot(111)

    # ===========================================================================
    def _add_event_hover(self):
        try:
            self.disconnect_event('motion_notify_event')
            self.disconnect_event('button_press_event')
        except:
            pass
        self.add_event('motion_notify_event', self._on_movement_hover)

    #===========================================================================
    def reset_plot(self):
        self.fig.delaxes(self.ax)

    #===========================================================================
    def add_target(self, target):
        if target not in self.targets:
            self.targets.append(target)

    def add_legend(self):
        self.legend = self.fig.legend()
        self.call_targets()

    #==========================================================================
    def add_event(self, event_type, event_function):
        if event_type in self.event_dict:
            print('Event already added')
            return
        self.event_dict[event_type] = {}
        self.event_dict[event_type]['event_type'] = event_type
        self.event_dict[event_type]['event_function'] = event_function
        self.event_dict[event_type]['object'] = self.fig.canvas.mpl_connect(event_type,
                                                                            event_function)

    #==========================================================================
    def disconnect_event(self, event_type):
        if event_type in self.event_dict:
            self.fig.canvas.mpl_disconnect(self.event_dict[event_type]['object'])
            self.event_dict.pop(event_type)

    #==========================================================================
    def disconnect_all_events(self):
        event_list = self.event_dict.keys()
        for event_type in event_list:
            self.disconnect_event(event_type)
    
    #===========================================================================
    def get_xlim(self):
        return self.ax.get_xlim()
            
    #===========================================================================
    def get_ylim(self):
        return self.ax.get_ylim()
        
    #===========================================================================
    def _on_click(self, event):
        pass

    def _on_movement_hover(self, event):
        self.hover_x = event.xdata
        self.hover_y = event.ydata
        self.call_target_hover()


    def call_target_hover(self):
        if self.hover_target:
            self.hover_target()
            
    #===========================================================================
    def call_targets(self):
        """
        Target is the mostly connected to updating a tk canvas.
        """
        if self.targets:
            for target in self.targets:
                target()
        else:
            self.fig.draw()
            self.fig.show()        

            
    #===========================================================================
    def set_x_grid(self, grid_on=True, sync_color_with_line_id='default'):
        self.ax.grid(grid_on, axis='x', linestyle=':')

        #===========================================================================
    def set_y_grid(self, grid_on=True, sync_color_with_line_id='default'):
        self.ax.grid(grid_on, axis='y', linestyle=':')

        #===========================================================================
    def zoom_to_data(self, call_targets=True):
        ax = self._get_ax_object(ax)
        if ax:
            ax.set_x_limits(call_targets=False)
            ax.set_y_limits(call_targets=False)
            if call_targets:
                self.call_range_targets()

    def _set_date_ticks(self):
        start_date, end_date = self.get_xlim()
        start_date = datetime.datetime.fromordinal(int(start_date))
        end_date = datetime.datetime.fromordinal(int(end_date))
        dt = end_date - start_date
        nr_days = dt.days

        if nr_days <= 30:
            loc = mdates.DayLocator()
            fmt = mdates.DateFormatter('%Y-%m-%d')
        elif nr_days <= 100:
            loc = mdates.DayLocator(bymonthday=[1, 15])
            fmt = mdates.DateFormatter('%Y-%m-%d')
        elif nr_days <= 365:
            loc = mdates.MonthLocator()
            fmt = mdates.DateFormatter('%Y-%m-%d')
        else:
            loc = mdates.MonthLocator(bymonthday=2)
            fmt = mdates.DateFormatter('%Y-%m-%d')

        self.ax.xaxis.set_major_locator(loc)
        self.ax.xaxis.set_major_formatter(fmt)

    #===========================================================================
    def set_x_limits(self, limits=[], call_targets=True):
        x_min, x_max = limits
        self.ax.set_xlim([x_min, x_max])

        # self._set_date_ticks()
        try:
            self._set_date_ticks()
        except:
            pass

        if call_targets:
            self.call_targets()
            
    #===========================================================================
    def set_y_limits(self, limits=[], call_targets=True):
        y_min, y_max = limits
        self.ax.set_xlim([y_min, y_max])

        if call_targets:
            self.call_targets()

            
    #===========================================================================
    def set_data(self, x=False, y=False, z=None, line_id='default', exclude_index=[], ax='first', call_targets=True, **kwargs):
        try:
            x = [pd.to_datetime(item) for item in x]
        except:
            pass

        X, Y = np.meshgrid(x, y)

        self.data = dict()
        self.data['x'] = x
        self.data['y'] = y
        self.data['X'] = X
        self.data['Y'] = Y
        self.data['Z'] = z


        self.ax.contourf(X, Y, z, kwargs.get('nr_levels', 50))

        if self.hover_target:
            self._add_event_hover()

        self.call_targets()

    #===========================================================================
    def set_label(self, label):
        if self.vertical_orientation:
            self.ax.set_y_label(label)
        else:
            self.ax.set_x_label(label)



