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
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import pandas as pd

class PlotSeries():
    
    #===========================================================================
    def __init__(self, sync_colors=True):
        
        self.sync_colors = sync_colors
        self._get_default_settings()
        self._setup_figure()
    
    #===========================================================================
    def _setup_figure(self):
        self.fig = Figure()
        self.ax1 = None
        self.p1 = None
        self.ax2 = None
        self.p2 = None
        
    #===========================================================================
    def _get_default_settings(self):
        self.p1_color = 'b'
        self.p1_linestyle = '-'
        self.p1_markerstyle = 'o'
        self.p1_markersize = 8
        self.ax1_label = u''
        
        self.p2_color = 'r'
        self.p2_linestyle = '-'
        self.p2_markerstyle = 'o'
        self.p2_markersize = 8
        self.ax2_label = u''
        
        self.x1_data = []
        self.z1_data = []
        self.x2_data = []
        self.z2_data = []
        
        self.targets = []
        self.event_dict = {}
    
    #===========================================================================
    def add_target(self, target):
        self.targets.append(target)
        
    #==========================================================================
    def add_event(self, event_type, event_function): 
        if event_type in self.event_dict:
            print(u'Event already added')
            return
        self.event_dict[event_type] = {}
        self.event_dict[event_type][u'event_type'] = event_type
        self.event_dict[event_type][u'event_function'] = event_function
        self.event_dict[event_type][u'object'] = self.fig.canvas.mpl_connect(event_type, 
                                                   event_function)
            
    #===========================================================================
    def set_min_range(self):
        rangetype = 'min'
        fig = self.dict_files[self.current_file].parameter_dict_plot[self.current_par]['fig']
        self.minRange_button_movement_event = fig.canvas.mpl_connect('motion_notify_event', lambda event: self.onMovementCanvas(event,rangetype))
        self.minRange_button_press_event = fig.canvas.mpl_connect('button_press_event', lambda event: self.onClickCanvas(rangetype))
        
    #===========================================================================
    def call_targets(self):
        if self.targets:
            for target in self.targets:
                target()
        else:
            self.fig.draw()
      
    #===========================================================================
    def _add_ax1(self):
        if not self.ax1:
            self.ax1 = self.fig.add_subplot(111)
    
    #===========================================================================
    def _add_ax2(self):
        if not self.ax2:
            if not self.ax1:
                self._add_ax1()
            self.ax2 = self.ax1.twiny()

            
    #===========================================================================
    def set_ax1_data(self, x, z):
        self.x1_data = x
        self.z1_data = z
        if not self.ax1: self._add_ax1()
        if not self.p1:
            self.p1, = self.ax1.plot(x, z)
            self.set_ax1_color()
            self.set_ax1_linestyle()
            self.set_ax1_markerstyle()
        else:
            self.p1.set_data(x, z)
        self.call_targets()
            
    #===========================================================================
    def set_ax2_data(self, x, z):
        self.x2_data = x
        self.z2_data = z
        if not self.p2:
            self._add_ax2()
            self.p2, = self.ax2.plot(x, z)
            self.set_ax2_color()
            self.set_ax2_linestyle()
            self.set_ax2_markerstyle()
        else:
            self.p2.set_data(x, z)
        self.call_targets()
            
            
    #===========================================================================
    def set_ax1_linestyle(self, linestyle=None):
        if linestyle:
            self.p1_linestyle = linestyle
        if self.p1:
            self.p1.set_linestyle(self.p1_linestyle)
            self.call_targets()
            
    #===========================================================================
    def set_ax2_linestyle(self, linestyle=None):
        if linestyle:
            self.p2_linestyle = linestyle
        if self.p2:
            self.p2.set_linestyle(self.p2_linestyle)
            self.call_targets()
            
        
    #===========================================================================
    def set_ax1_color(self, color=None):
        if color:
            self.p1_color = color
        if self.p1:
            self.p1.set_color(self.p1_color)
            if self.sync_colors:
                for tl in self.ax1.get_xticklabels():
                    tl.set_color(self.p1_color)
                if self.ax1_label:
                    self.set_ax1_label()
            self.call_targets()
                
    #===========================================================================
    def set_ax2_color(self, color=None):
        if color:
            self.p2_color = color
        if self.ax2 and self.p2:
            self.p2.set_color(self.p2_color)
            if self.sync_colors:
                for tl in self.ax2.get_xticklabels():
                    tl.set_color(self.p2_color)
                if self.ax2_label:
                    self.set_ax2_label()
            self.call_targets()
            
    #===========================================================================
    def set_ax1_markerstyle(self, markerstyle=None):
        if markerstyle:
            self.p1_markerstyle = markerstyle
        if self.p1:
            self.p1.set_marker(self.p1_markerstyle)
            self.call_targets()
            
    #===========================================================================
    def set_ax2_markerstyle(self, markerstyle=None):
        if markerstyle:
            self.p2_markerstyle = markerstyle
        if self.ax2 and self.p2:
            self.p2.set_marker(self.p2_markerstyle)
            self.call_targets()
            
    
    #===========================================================================
    def set_ax1_markersize(self, markersize=None):
        if markersize:
            self.p1_markersize = markersize
        if self.ax1 and self.p1:
            self.p1.set_markersize(self.p1_markersize)
            self.call_targets()
            
    #===========================================================================
    def set_ax2_markersize(self, markersize=None):
        if markersize:
            self.p2_markersize = markersize
        if self.ax2 and self.p2:
            self.p2.set_markersize(self.p2_markersize)
            self.call_targets()
    
    
    #===========================================================================
    def set_z_limits(self, limits=[]):
        z_min = None
        if self.p1 or self.p2:
            if limits:
                z_min, z_max = limits
            else:
                z_data = self.z1_data + self.z2_data
                z_min = np.nanmin(z_data)
                z_max = np.nanmax(z_data)
            if self.ax1:
                self.ax1.set_ylim([z_min, z_max])
            elif self.ax2:
                self.ax2.set_ylim([z_min, z_max])
            self.call_targets()
            
    #===========================================================================
    def set_ax1_limits(self, limits=[]):
        x_min = None
        if self.p1:
            if limits:
                x_min, x_max = limits
            else:
                x_min = np.nanmin(self.x1_data)
                x_max = np.nanmax(self.x1_data)
            self.ax1.set_xlim([x_min, x_max])
            self.call_targets()
            
    #===========================================================================
    def set_ax2_limits(self, limits=[]):
        x_min = None
        if self.p2:
            if limits:
                x_min, x_max = limits
            else:
                x_min = np.nanmin(self.x2_data)
                x_max = np.nanmax(self.x2_data)
            self.ax2.set_xlim([x_min, x_max])
            self.call_targets()
            
    
    #===========================================================================
    def set_ax1_label(self, label=u''):
        if self.ax1:
            if label:
                self.ax1_label = self.ax1.set_xlabel(label)
            if self.sync_colors: 
                self.ax1_label.set_color(self.p1_color)
            self.call_targets()
        
    #===========================================================================
    def set_ax2_label(self, label=u''):
        if self.ax2:
            if label:
                self.ax2_label = self.ax2.set_xlabel(label)
            if self.sync_colors: 
                self.ax2_label.set_color(self.p2_color)
            self.call_targets()
                
    #===========================================================================
    def set_ax1_xgrid(self, grid_on=True):
        if self.ax1: 
            if not grid_on:
                self.ax1.grid(grid_on, axis='x')
            elif self.sync_colors:
                self.ax1.grid(b=grid_on, axis='x', which='major', color=self.p1_color, linestyle=':')
            else:
                self.ax1.grid(grid_on, axis='x', linestyle='--') 
            self.call_targets()

    #===========================================================================
    def set_ax2_xgrid(self, grid_on=True):
        if self.ax2: 
            if not grid_on:
                self.ax2.grid(grid_on, axis='x')
            elif self.sync_colors:
                self.ax2.grid(b=grid_on, axis='x', which='major', color=self.p2_color, linestyle=':')
            else:
                self.ax2.grid(grid_on, axis='x', linestyle='--') 
            self.call_targets()
           
    #===========================================================================
    def set_zgrid(self, grid_on=True):
        if self.ax1: 
            self.ax1.grid(grid_on, axis='y')
            self.call_targets()
            
"""
========================================================================
========================================================================
========================================================================
"""
class Plot():
    
    #===========================================================================
    def __init__(self, sync_colors=True, 
                 allow_two_axis=True,
                 allow_selection=True,
                 orientation='vertical', 
                 time_axis=None,
                 hover_target=None,
                 callback_on_disconnect_events=None,
                 **kwargs):
        
        self.sync_colors = sync_colors
        self.allow_two_axis = allow_two_axis
        self.allow_selection = allow_selection
        
        if orientation in ['v', 'vertical']:
            self.vertical_orientation = True
        else:
            self.vertical_orientation = False
            
        self.time_axis = time_axis
        self.hover_target = hover_target
        self.callback_on_disconnect_events = callback_on_disconnect_events

        self.legend = None

        self.prop_fig = kwargs
        self._get_default_settings()
        self._setup_figure()
        
    #===========================================================================
    def _get_default_settings(self):
        
        self.targets = []
        self.range_targets = []
        self.lasso_targets = []
        self.event_dict = {}
        
        self.clear_all_marked()
    
    #===========================================================================
    def _setup_figure(self):
        self.fig = Figure(**self.prop_fig)
        self.first_ax = None
        self.second_ax = None
        self.mark_line_id = 'default'

    # ==========================================================================
    def delete_data(self, marker_id=None, ax='first'):
        """
        if marker_name: marker with the exact name is removed
        if marker_id: All markers containing the given marker_id are removed
        """
        ax = self._get_ax_object(ax)
        ax.delete_data(marker_id)
        self.call_targets()

    #===========================================================================
    def reset_plot(self):
        if self.first_ax:
            self.first_ax.reset_ax()
        if self.second_ax:
            self.second_ax.reset_ax()
            
    #===========================================================================
    def add_target(self, target):
        if target not in self.targets:
            self.targets.append(target)
            
    #===========================================================================
    def add_range_target(self, target):
        if target not in self.range_targets:
            self.range_targets.append(target)
            
    #===========================================================================
    def add_lasso_target(self, target):
        if target not in self.lasso_targets:
            self.lasso_targets.append(target)

    def add_legend(self):
        self.legend = self.fig.legend()
        self.fig.draw()
        
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
        event_list = list(self.event_dict.keys())
        for event_type in event_list:
            self.disconnect_event(event_type)

        if self.hover_target:
            self._add_event_hover()

        if self.callback_on_disconnect_events:
            self.callback_on_disconnect_events()
    
    #===========================================================================
    def remove_mark_range_target(self, ax='all'):
        if ax == 'all':
            self.mark_ax = []
            return
        
        ax = self._get_ax_object(ax)

        if ax in self.mark_ax:
            self.mark_ax.pop(self.mark_ax.index(ax))
    
    #===========================================================================
    def add_mark_range_target(self, ax, color='m'):
        ax = self._get_ax_object(ax)
            
        if ax not in self.mark_ax:
            ax.set_mark_color(color)
            self.mark_ax.append(ax)
            
    #===========================================================================
    def add_mark_point_target(self, ax, color='m'):
        ax = self._get_ax_object(ax)
            
        if ax not in self.mark_ax:
            ax.set_mark_color(color)
            self.mark_ax.append(ax)
            
    #===========================================================================
    def add_mark_lasso_target(self, ax, color='m'):
        ax = self._get_ax_object(ax)
            
        if ax not in self.mark_ax:
            ax.set_mark_color(color)
            self.mark_ax.append(ax)

    # ===========================================================================
    def _add_event_hover(self):
        ax = self._get_ax_object(1)
        ax.set_mark_color('r')
        # ax = self._get_ax_object(ax)
        self.mark_ax.append(ax)
        try:
            self.disconnect_event('motion_notify_event')
            self.disconnect_event('button_press_event')
            self.rangetype = None
        except:
            pass
        self.add_event('motion_notify_event', self._on_movement_hover)

    #===========================================================================
    def _add_mark_range_events(self):
        if not self.mark_ax:
            return
        try:
            self.disconnect_event('motion_notify_event')
        except:
            pass
        self.add_event('motion_notify_event', self._on_movement)
        self.add_event('button_press_event', self._on_click)
        
    #===========================================================================
    def mark_range_from_bottom(self, line_id='default'):
        """ Marks min range in plot by movement """
        if not self.allow_selection:
            return
        if self.mark_range_orientation == 'horizontal':
            self.clear_all_marked()
        self.mark_line_id = line_id
        self.rangetype = 'bottom'
        self._add_mark_range_events()
        
    #===========================================================================
    def mark_range_from_top(self, line_id='default'):
        """ Marks max range in plot by movement """
        if not self.allow_selection:
            return
        if self.mark_range_orientation == 'horizontal':
            self.clear_all_marked()
        self.mark_line_id = line_id
        self.rangetype = 'top'
        self._add_mark_range_events()
        
    #===========================================================================
    def mark_range_from_left(self, line_id='default'):
        if not self.allow_selection:
            return
        """ Marks min range in plot by movement """
        if self.mark_range_orientation == 'vertical':
            self.clear_all_marked()
        self.mark_line_id = line_id
        self.rangetype = 'left'
        self._add_mark_range_events()
        
    #===========================================================================
    def mark_range_from_right(self, line_id='default'):
        if not self.allow_selection:
            return
        """ Marks max range in plot by movement """
        if self.mark_range_orientation == 'vertical':
            self.clear_all_marked()
        self.mark_line_id = line_id
        self.rangetype = 'right'
        self._add_mark_range_events()
        
    #===========================================================================
    def mark_points(self, line_id='default'):
        if not self.allow_selection:
            return
        if not self.mark_ax:
            return
        # print('mark_ax', self.mark_ax)
#         self.clear_marked()
        self.mark_line_id = line_id
        self.rangetype = 'point'
        self.add_event('button_press_event', self._on_click)
    
    #===========================================================================
    def mark_lasso(self, line_id='default'):
        if not self.allow_selection:
            return
        print('This methods is not yet functional because it is linked to a scatter plot object' )
        
        self.mark_line_id = line_id
        self.range_type = 'lasso'
        
        for ax in self.mark_ax:
            ax.mark_lasso(line_id=self.mark_line_id)

    def save_fig(self, file_path, **kwargs):
        self.fig.savefig(file_path, **kwargs)

    #===========================================================================
    def set_bottom_range(self, bottom_value, diconnect_events=False, ax='first', line_id='default'):
        """ 
        Shows mark_range with the given min_value. 
        Returns the min value ax_object in the given range. 
        """
        if not self.mark_ax:
            return
        self.mark_line_id = line_id
        self.mark_bottom = float(bottom_value)
        ax_object = self._get_ax_object(ax)
        ax_object.mark_range_range(self.mark_bottom, self.mark_top, self.mark_left, self.mark_right, line_id=line_id)
            
        if diconnect_events:
            self.disconnect_all_events()
        
        self.call_targets()
        
   
    #===========================================================================
    def set_top_range(self, top_value, diconnect_events=False, ax='first', line_id='default'):
        """ 
        Shows mark_range with the given max_value. 
        Returns the max value for the first mark axis in the given range. 
        """
        if not self.mark_ax:
            return
        self.mark_line_id = line_id
        self.mark_top = float(top_value)
        ax_object = self._get_ax_object(ax)
        ax_object.mark_range_range(self.mark_bottom, self.mark_top, self.mark_left, self.mark_right, line_id=line_id)
        
        if diconnect_events:
            self.disconnect_all_events()
            
        self.call_targets()
              
    #===========================================================================
    def set_left_range(self, left_value, diconnect_events=False, ax='first', line_id='default'):
        """ 
        Shows mark_range with the given min_value. 
        Returns the min value ax_object in the given range. 
        """
        if not self.mark_ax:
            return
        self.mark_line_id = line_id
        self.mark_left = float(left_value)
        ax_object = self._get_ax_object(ax)
        ax_object.mark_range_range(self.mark_bottom, self.mark_top, self.mark_left, self.mark_right, line_id=line_id)
            
        if diconnect_events:
            self.disconnect_all_events()
        
        self.call_targets()
   
    #===========================================================================
    def set_right_range(self, right_value, diconnect_events=False, ax='first', line_id='default'):
        """ 
        Shows mark_range with the given max_value. 
        Returns the max value for the first mark axis in the given range. 
        """
        if not self.mark_ax:
            return
        self.mark_line_id = line_id
        self.mark_right = float(right_value)
        ax_object = self._get_ax_object(ax)
        ax_object.mark_range_range(self.mark_bottom, self.mark_top, self.mark_left, self.mark_right, line_id=line_id)
        
        if diconnect_events:
            self.disconnect_all_events()
            
        self.call_targets()
   
    #===========================================================================
    def clear_all_marked(self ,color='r'):
        self.clear_marked_range(call_targets=False)
        self.clear_marked_points(call_targets=False)
        # self.clear_marked_lasso(call_targets=False)

        try:
            if self.hover_target:
                self._add_event_hover()
        except:
            pass

        if hasattr(self, 'first_ax') and self.first_ax:
            self.call_targets()
        
    #===========================================================================
    def clear_marked_range(self, call_targets=True):

        self.mark_bottom = None
        self.mark_top = None
        self.mark_left = None
        self.mark_right = None
        self.rangetype = None
        self.mark_ax = []
        self.mark_range_orientation = None
        
        if hasattr(self, 'first_ax') and self.first_ax:
            self.first_ax.reset_marked_range()

        if hasattr(self, 'second_ax') and self.second_ax:
            self.second_ax.reset_marked_range()
        
        if call_targets:
            self.call_targets()

        
    #===========================================================================
    def clear_marked_points(self, call_targets=True):

        self.rangetype = None
        self.mark_ax = []
        
        if hasattr(self, 'first_ax') and self.first_ax:
            self.first_ax.reset_marked_points()
            
        if hasattr(self, 'second_ax') and self.second_ax:
            self.second_ax.reset_marked_points()
        
        if call_targets:
            self.call_targets()
            
    #===========================================================================
    def clear_marked_lasso(self, call_targets=True):

        self.rangetype = None
        self.mark_ax = []
        
        if hasattr(self, 'first_ax') and self.first_ax:
            self.first_ax.reset_marked_lasso()

        if hasattr(self, 'second_ax') and self.second_ax:
            self.second_ax.reset_marked_lasso()
        
        if call_targets:
            self.call_targets()
        
    #===========================================================================
    def _get_ax_object(self, ax):
#         print(ax, type(ax) # Called to many times?
        if isinstance(ax, Ax):
            ax_object = ax
        elif ax in ['first', 'first_ax', '1', 1]:
            ax_object = self.first_ax
        elif ax in ['second', 'second_ax', '2', 2]:
            ax_object = self.second_ax
        else:
            print('Not a valid ax id!')
            ax_object = None
        return ax_object
        
    #===========================================================================
    def get_marked_index(self, ax='first'):
        ax_object = self._get_ax_object(ax)
        return ax_object.get_marked_index()

    def get_marked_x_values(self, ax='first'):
        ax_object = self._get_ax_object(ax)
        return ax_object.get_marked_x_values(self.mark_line_id)

    def get_marked_y_values(self, ax='first'):
        ax_object = self._get_ax_object(ax)
        return ax_object.get_marked_y_values(self.mark_line_id)

        #===========================================================================
    def get_mark_from_value(self, ax='first'):
        ax_object = self._get_ax_object(ax)
        return ax_object.get_mark_from_value()
        
    #===========================================================================
    def get_mark_to_value(self, ax='first'):
        ax_object = self._get_ax_object(ax)
        return ax_object.get_mark_to_value()
    
    #===========================================================================
    def get_xlim(self, ax='first'):
        ax = self._get_ax_object(ax)
        if ax:
            return ax.get_xlim()
            
    #===========================================================================
    def get_ylim(self, ax='first'):
        ax = self._get_ax_object(ax)
        if ax:
            return ax.get_ylim()

    def get_display_coordinates(self, axis_coordinates, ax='first'):
        """
        Transform axis_coordinates to display coordinates.
        :param ax_coordinates:
        :return:
        """
        ax_object = self._get_ax_object(ax)
        return ax_object.transData.transform(axis_coordinates)
        
    #===========================================================================
    def _on_click(self, event):
        if self.rangetype == 'point':
            if event.button == 1:
                x = event.xdata
                y = event.ydata
#                print('-'*10
#                print(x, y
#                print(event.x, event.y
                
                for ax in self.mark_ax:
                    ax.add_mark_point(x, y, self.mark_line_id) # Will also plot
                self.call_targets()
                    
            else:
                # self.disconnect_event('button_press_event')
                self.rangetype = None
                self.disconnect_all_events()
                
        else:
            # self.disconnect_event('motion_notify_event')
            # self.disconnect_event('button_press_event')
            self.rangetype = None
            self.disconnect_all_events()

    def _on_movement_hover(self, event):
        self.hover_x = event.xdata
        self.hover_y = event.ydata
        self.call_target_hover()

    #===========================================================================
    def _on_movement(self, event):
        if self.rangetype == 'bottom':
            self.mark_bottom = event.ydata
            self.mark_range_orientation = 'vertical'
        elif self.rangetype == 'top':
            self.mark_top = event.ydata
            self.mark_range_orientation = 'vertical'
        elif self.rangetype == 'left':
            self.mark_left = event.xdata
            self.mark_range_orientation = 'horizontal'
        elif self.rangetype == 'right':
            self.mark_right = event.xdata
            self.mark_range_orientation = 'horizontal'
        else:
            return

        for ax in self.mark_ax:
            ax.mark_range_range(self.mark_bottom,
                                self.mark_top,
                                self.mark_left,
                                self.mark_right,
                                self.mark_line_id)
        self.call_range_targets()

#    #===========================================================================
#    def call_range_targets(self):
#        if self.range_targets:
#            for target in self.range_targets:
#                target()
#        else:
#            self.fig.draw()
#            self.fig.show()
#            
#    #===========================================================================
#    def call_targets(self):
#        if self.targets:
#            for target in self.targets:
#                target()
#        else:
#            self.fig.draw()
#            self.fig.show()
            
    #===========================================================================
    def call_lasso_targets(self):
        
        if self.lasso_targets:
            for target in self.lasso_targets:
                target()
        
        self.call_targets()
        
    #===========================================================================
    def call_range_targets(self):
        
        if self.range_targets:
            for target in self.range_targets:
                target()
        
        self.call_targets()

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
    def add_first_ax(self, margins=None, **kwargs):
        if not self.first_ax:
            self.first_ax = Ax(self, self.fig.add_subplot(111), time_axis=self.time_axis, **kwargs)
            
            if margins:
                if 'right' in margins:
                    margins['right'] = 1-margins['right']
                
                if 'top' in margins:
                    margins['top'] = 1-margins['top']
                    
                self.fig.subplots_adjust(**margins)
                
            if self.time_axis =='x':
                self.fig.autofmt_xdate()
#             self.first_ax.ax.get_xaxis().set(rotation=45)

            
    #===========================================================================
    def add_second_ax(self, **kwargs):
        if not self.first_ax:
            print('Must add first ax befor second!')
            return
        if not self.allow_two_axis:
            print(u'Only one axis allowed!')
            return
        if not self.second_ax:
            if self.vertical_orientation:
                self.second_ax = Ax(self, self.first_ax.ax.twiny(), time_axis=self.time_axis, **kwargs)
                print('Second y-axis added!')
            else:
                self.second_ax = Ax(self, self.first_ax.ax.twinx(), time_axis=self.time_axis, **kwargs)
                print('Second x-axis added!')
        else:
            print('Second ax already added!')

        
    #===========================================================================
    def flip_y_tick_sign(self):
        sign = '\u22121'
        labels = [item.get_text().replace(sign, u'') for item in self.first_ax.ax.get_yticklabels()]
        self.first_ax.ax.set_yticklabels(labels)
        
#    #===========================================================================
#    def set_x_grid(self, grid_on=True, ax='first', sync_color_with_line_id='default'):
#        ax = self._get_ax_object(ax)
#        if ax:
#            ax.set_x_grid(grid_on=grid_on, sync_color_with_line_id=sync_color_with_line_id)
            
    #===========================================================================
    def set_x_grid(self, ax='first', grid_on=True, sync_color_with_line_id='default'):
        ax = self._get_ax_object(ax)
        if ax:
            ax.set_x_grid(grid_on, sync_color_with_line_id=sync_color_with_line_id)
            self.call_targets()
            
    #===========================================================================
    def set_y_grid(self, ax='first', grid_on=True, sync_color_with_line_id='default'):
        ax = self._get_ax_object(ax)
        if ax:
            ax.set_y_grid(grid_on, sync_color_with_line_id=sync_color_with_line_id)
            self.call_targets()
            
    #===========================================================================
#    def set_y_grid(self, grid_on=True):
#        if self.first_ax.ax: 
#            self.first_ax.ax.grid(grid_on, axis='y')
#            self.call_targets()
            
    #===========================================================================
    def zoom_to_data(self, ax='first', call_targets=True, x_limits=True, y_limits=True):
        ax = self._get_ax_object(ax)
        if ax:
            if x_limits:
                ax.set_x_limits(call_targets=False)
            if y_limits:
                ax.set_y_limits(call_targets=False)
            if call_targets:
                self.call_range_targets()
            
    #===========================================================================
    def set_x_limits(self, ax='first', limits=[], call_targets=True): 
        ax = self._get_ax_object(ax)
        if ax:
            ax.set_x_limits(limits, call_targets=call_targets)
            
    #===========================================================================
    def set_y_limits(self, ax='first', limits=[], call_targets=True): 
        ax = self._get_ax_object(ax)
        if ax:
            ax.set_y_limits(limits, call_targets=call_targets)

    #===========================================================================
    def set_prop(self, line_id='default', ax='first', **kwargs):
        ax = self._get_ax_object(ax)
        if ax:
            ax.set_prop(line_id=line_id, **kwargs)
            
    #===========================================================================
    def set_data(self,
                 x=False,
                 y=False,
                 z=None,
                 c=None,
                 line_id='default',
                 exclude_index=[],
                 ax='first',
                 call_targets=True,
                 colorbar_title='',
                 **kwargs):

        ax = self._get_ax_object(ax)
        if ax:
            if self.time_axis == 'x':
                try:
                    x = [pd.to_datetime(item) for item in x]
                except:
                    pass

            if kwargs.get('contour_plot'):
                x, y = np.meshgrid(x, y)

            ax.set_data(x=x, y=y, z=z, c=c, line_id=line_id, exclude_index=exclude_index,
                        call_targets=call_targets, colorbar_title=colorbar_title, **kwargs)

        if self.hover_target:
            self._add_event_hover()

    #===========================================================================
    def set_label(self, label):
        if self.vertical_orientation:
            self.first_ax.set_y_label(label)
        else:
            self.first_ax.set_x_label(label)

    def set_x_label(self, label):
        self.first_ax.set_x_label(label)

    def set_y_label(self, label):
        self.first_ax.set_y_label(label)

    def set_title(self, title):
        self.first_ax.set_title(title)
        # self.fig.tight_layout()
        self.call_targets()
            
    #===========================================================================
    def set_first_label(self, label):
        if self.vertical_orientation:
            self.first_ax.set_x_label(label)
        else:
            self.first_ax.set_y_label(label)
            
    #===========================================================================
    def set_second_label(self, label):
        if self.second_ax:
            if self.vertical_orientation:
                self.second_ax.set_x_label(label)
            else:
                self.second_ax.set_y_label(label)

"""
========================================================================
========================================================================
========================================================================
"""
class Ax():  
    #===========================================================================
    def __init__(self, parent, axes, mark_at_point=False, time_axis=False, **general_prop):
        self.parent = parent
        self.ax = axes
        self.time_axis = time_axis
        self._load_attributes()
        
        self.reset_ax(**general_prop)
        self.mark_at_point = mark_at_point      
        
        self.mark_from_value = None
        self.mark_to_value = None
        
    #===========================================================================
    def reset_ax(self, **general_prop):
        self.reset_all_marked()
        for k in range(len(self.ax.lines)):
            self.ax.lines.pop(-1)
        self._load_attributes()
        
        self.default_prop = self.get_default_prop()
        self.default_prop.update(general_prop)
        
    
    #===========================================================================
    def _load_attributes(self):
        
        self.x_label = None
        
        self.default_prop = {}
        self.prop = {}

        self.p = {}
        
        self.x_data = {}
        self.y_data = {}
        self.c_data = {}
              
        
        self.mark_index_points = {}
        self.lasso_object = None
        
    #===========================================================================
    def get_default_prop(self):
        
        return {'color': 'b', 
                'linestyle': '-', 
                'marker': 'None', 
                'markersize': 8}
            
    #===========================================================================
    def reset_marked_range(self):
        self.mark_index = []       
          
        # Remove marker lines
        index_to_pop = []
        for k, c in enumerate(self.ax.lines):
            if c.get_label() in ['marked_min', 'marked_max', 'marked_line']:
                index_to_pop.append(k)
        index_to_pop.reverse()
        for i in index_to_pop:
            self.ax.lines.pop(i)
            
        # Remove marked field
        # How to modify this is several polygons are added to the plot
        if self.ax.patches:
            self.ax.patches.pop(0)

    # ===========================================================================
    def delete_data(self, marker_id):
        if marker_id in self.p:
            # self.ax.lines.pop(self.ax.lines.index(marker_id))
            self.p[marker_id].remove()
            self.p.pop(marker_id)
            self.x_data[marker_id] = []
            self.y_data[marker_id] = []
        
    #===========================================================================
    def reset_marked_points(self, reset_list=True):
        if reset_list:
            self.mark_index_points = {}
        # Remove marker lines
        index_to_pop = []
        for k, c in enumerate(self.ax.lines):
            if c.get_label() in ['marked_points']:
                index_to_pop.append(k)
        index_to_pop.reverse()
        for i in index_to_pop:
            self.ax.lines.pop(i)
        
    #===========================================================================
    def reset_all_marked(self):
        self.reset_marked_range()
        self.reset_marked_points()
        # self.reset_marked_lasso()
        
    #===========================================================================
    def get_marked_index(self):
        return self.mark_index

    def get_marked_x_values(self, line_id):
        index = self.get_marked_index()
        return self.x_data[line_id][index]

    def get_marked_y_values(self, line_id):
        index = self.get_marked_index()
        return self.y_data[line_id][index]
    
    #===========================================================================
    def get_marked_points(self, line_id='default'):
        if line_id in self.mark_index_points:
            return self.mark_index_points[line_id]
        else:
            return np.array([])
    
    #===========================================================================
    def get_xlim(self):
        return self.ax.get_xlim()
    
    #===========================================================================
    def get_ylim(self):
        return self.ax.get_ylim()
        
    #===========================================================================
    def get_mark_from_value(self):
        return self.mark_from_value
    
    #===========================================================================
    def get_mark_to_value(self):
        return self.mark_to_value
        
    #===========================================================================
    def add_mark_point(self, x, y, line_id='default'):
        """ Adds closest point to self.mark_points and plots result """ 
        
        # Remove old plot
        self.reset_marked_points(reset_list=False)

        # Find closest point in xdata
        x_data = np.array(self.x_data[line_id])
        z_data = np.array(self.y_data[line_id])
        
        x_diff = (x_data - x)/np.nanmax(np.abs(x_data))
        y_diff = (z_data - y)/np.nanmax(np.abs(z_data))


        diff_list = np.sqrt(x_diff**2 + y_diff**2)

#         diff_list = abs(np.array(self.y_data[line_id]) - y)
        
        if line_id not in self.mark_index_points:
            self.mark_index_points[line_id] = []
        
        index = np.where(diff_list == np.nanmin(diff_list))[0][0]
        if index in self.mark_index_points[line_id]:
            self.mark_index_points[line_id].pop(self.mark_index_points[line_id].index(index))
        else:
            self.mark_index_points[line_id].append(index)
            self.mark_index_points[line_id].sort()
       
        # Plot marked points        
        z = np.array(self.y_data[line_id])
        x = np.array(self.x_data[line_id])
        index = np.array(self.mark_index_points[line_id])
        
        # Plot 
        if index.size:
            self.ax.plot(x[index], z[index], color=self.mark_color, linestyle='None', marker='o', markersize=8, 
                         zorder=20, label='marked_points')
            
    #===========================================================================
    def old_mark_lasso(self, line_id):
        collection = self.p[line_id]
        self.lasso_object = SelectFromCollection(self.ax, collection, alpha_other=0.3, target=self._callback_lasso)
        
    #===========================================================================
    def _callback_lasso(self):
        self.mark_index = self.lasso_object.ind
        
    #===========================================================================
    def reset_marked_lasso(self):
        try:
            self.lasso_object.disconnect()
            self.lasso_object = None
        except:
            print('Could not disconnect lasso select.')
        
    #===========================================================================
    def mark_range_range(self, 
                         mark_bottom=None, 
                         mark_top=None, 
                         mark_left=None, 
                         mark_right=None, 
                         line_id='default'):
#        print('IN: mark_range_range: line_id = %s' % line_id
        #----------------------------------------------------------------------
        # Reset current markers
        self.reset_marked_range()
        # print('mark_left:', mark_left, 'mark_right:', mark_right)
        #----------------------------------------------------------------------
        # Plot range lines
        alpha = 0.2
        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()

        
        #----------------------------------------------------------------------
        # Vertical orientation
        if mark_bottom != None or mark_top != None:
            mark_from_value = mark_bottom
            mark_to_value = mark_top

            if mark_from_value is None:
                mark_from_value = y_min
            if mark_to_value is None:
                mark_to_value = y_max

            ax_span_function = self.ax.axhspan
            bottom_top = True
            
        
        #----------------------------------------------------------------------    
        # Horizontal orientation
        elif mark_left != None or mark_right != None:
            mark_from_value = mark_left
            mark_to_value = mark_right

            if mark_from_value is None:
                mark_from_value = x_min
            if mark_to_value is None:
                mark_to_value = x_max
            ax_span_function = self.ax.axvspan
            bottom_top = False
        
        if self.mark_at_point:
            pass
        else:

            try:
                # Save data
                self.mark_from_value = mark_from_value
                self.mark_to_value = mark_to_value
            except:
                return

            # print('From: {}, To: {}'.format(self.mark_from_value, self.mark_to_value))

            # Plot
            if mark_to_value > mark_from_value:
                if bottom_top:
                    self.ax.plot([x_min, x_max], [mark_from_value, mark_from_value], color=self.mark_color, linestyle='-', zorder=20, label='marked_min')
                    self.ax.plot([x_min, x_max], [mark_to_value, mark_to_value], color=self.mark_color, linestyle='-', zorder=21, label='marked_max')
                    self.span = ax_span_function(mark_from_value, mark_to_value, facecolor=self.mark_color, alpha=alpha, label='marked_span')
        #            self.span = self.ax.axhspan(value_list[top_index], value_list[bottom_index], facecolor=self.mark_color, alpha=alpha, label='marked_span')
                else:
                    self.ax.plot([mark_from_value, mark_from_value], [y_min, y_max], color=self.mark_color, linestyle='-', zorder=20, label='marked_min')
                    self.ax.plot([mark_to_value, mark_to_value], [y_min, y_max], color=self.mark_color, linestyle='-', zorder=21, label='marked_max')
                    self.span = ax_span_function(mark_from_value, mark_to_value, facecolor=self.mark_color, alpha=alpha, label='marked_span')

# #===========================================================================
#     def mark_range_range(self,
#                          mark_bottom=None,
#                          mark_top=None,
#                          mark_left=None,
#                          mark_right=None,
#                          line_id='default'):
# #        print('IN: mark_range_range: line_id = %s' % line_id
#         #----------------------------------------------------------------------
#         # Reset current markers
#         self.reset_marked_range()
#         # print('mark_left:', mark_left, 'mark_right:', mark_right)
#         #----------------------------------------------------------------------
#         # Plot range lines
#         alpha = 0.2
#         x_min, x_max = self.ax.get_xlim()
#         y_min, y_max = self.ax.get_ylim()
#
#         x = np.array(self.x_data[line_id])
#         y = np.array(self.y_data[line_id])
#
#         value_list = []
#
#         #----------------------------------------------------------------------
#         # Vertical orientation
#         if mark_bottom != None or mark_top != None:
#             value_list = y
# #            print(x_min, x_max, x[0]
#             if isinstance(x[0], datetime.datetime):
#                 xt = list(map(dates.date2num, x))
#                 nan_index = np.logical_or(xt > x_max, xt < x_min)
#             else:
#                 nan_index = np.logical_or(x > x_max, x < x_min)
#
# #            print('=', np.where(nan_index)
#             value_list[nan_index] = np.nan
# #            value_list = np.array([value for value in y if not np.isnan(value)])
#             mark_from_value = mark_bottom
#             mark_to_value = mark_top
#             ax_span_function = self.ax.axhspan
#             bottom_top = True
#
#
#         #----------------------------------------------------------------------
#         # Horizontal orientation
#         elif mark_left != None or mark_right != None:
#             # print('=' * 50)
#             # print('=' * 50)
#             # print('Horizontal orientation')
#             # print('y', y)
#             # print('ylim', y_min, y_max)
#             # print('x', x)
#             # print('type(x[0]', type(x[0]))
#
#             value_list = x
#             nan_index = np.logical_and(y > y_max, y < y_min)
#             # print('nan_index', nan_index)
#             # print('np.where(nan_index)', np.where(nan_index))
#             # print('-' * 50)
#             value_list = np.where(nan_index, np.nan, value_list)
#             # value_list[np.where()] = np.nan
#             # value_list[nan_index] = np.nan
# #            value_list = np.array([value for value in x if not np.isnan(value)])
#             mark_from_value = mark_left
#             mark_to_value = mark_right
#             ax_span_function = self.ax.axvspan
#             bottom_top = False
#
#         if not len(value_list):
#             return
#         #----------------------------------------------------------------------
#         # Convert if datetime axis
#         if isinstance(value_list[0], datetime.datetime):
#             value_list = np.array([dates.date2num(val) for val in value_list])
#
#         #----------------------------------------------------------------------
#         # Get info about min and max if they are not given
#         if mark_from_value == None:
# #            print('value_list', value_list
#             mark_from_value = np.nanmin(value_list)
#         if mark_to_value == None:
#             mark_to_value = np.nanmax(value_list)
#
#         if self.mark_at_point:
#             #----------------------------------------------------------------------
#             # Find "from" index
#             from_dist = np.abs(value_list-mark_from_value)
#             from_min_dist = np.nanmin(from_dist)
#             from_index = np.where(from_dist==from_min_dist)[0][0]
#             from_value = value_list[from_index]
#
#             #----------------------------------------------------------------------
#             # Find "to" index
#             to_dist = np.abs(value_list-mark_to_value)
#             to_min_dist = np.nanmin(to_dist)
#             to_index = np.where(to_dist==to_min_dist)[0][0]
#             to_value = value_list[to_index]
#
#             #----------------------------------------------------------------------
#             # Find index between bottom_range and top_range
#             boolean_index = np.logical_and(value_list <= to_value, value_list >= from_value)
#             index = np.where(boolean_index)[0]
#
#             #----------------------------------------------------------------------
#             # Save data
#             self.mark_from_value = mark_from_value
#             self.value_list = value_list
#             self.mark_to_value = mark_to_value
#
#             self.mark_from_index = from_index
#             self.mark_to_index = to_index
#             self.mark_index = index
#
#             #----------------------------------------------------------------------
#             # Plot
#             if mark_to_value > mark_from_value:
#                 if bottom_top:
#                     self.ax.plot([x_min, x_max], [value_list[from_index], value_list[from_index]], color=self.mark_color, linestyle='-', zorder=20, label='marked_min')
#                     self.ax.plot([x_min, x_max], [value_list[to_index], value_list[to_index]], color=self.mark_color, linestyle='-', zorder=21, label='marked_max')
#                     self.span = ax_span_function(value_list[from_index], value_list[to_index], facecolor=self.mark_color, alpha=alpha, label='marked_span')
#         #            self.span = self.ax.axhspan(value_list[top_index], value_list[bottom_index], facecolor=self.mark_color, alpha=alpha, label='marked_span')
#                 else:
#                     self.ax.plot([value_list[from_index], value_list[from_index]], [y_min, y_max], color=self.mark_color, linestyle='-', zorder=20, label='marked_min')
#                     self.ax.plot([value_list[to_index], value_list[to_index]], [y_min, y_max], color=self.mark_color, linestyle='-', zorder=21, label='marked_max')
#                     self.span = ax_span_function(value_list[from_index], value_list[to_index], facecolor=self.mark_color, alpha=alpha, label='marked_span')
#
#
#
#         else:
#             from_value = mark_from_value
#             to_value = mark_to_value
#
#             #----------------------------------------------------------------------
#             # Find index between bottom_range and top_range
# #             print('value_list', from_value, to_value, value_list[:10]
#             boolean_index = np.logical_and(value_list <= to_value, value_list >= from_value)
#             index = np.where(boolean_index)[0]
#
#             #----------------------------------------------------------------------
#             # Save data
# #            self.mark_from_index = from_index
# #            self.mark_to_index = to_index
#             self.mark_index = index
#             self.mark_from_value = mark_from_value
#             self.value_list = value_list
#             self.mark_to_value = mark_to_value
#
#             #----------------------------------------------------------------------
#             # Plot
#             if mark_to_value > mark_from_value:
#                 if bottom_top:
#                     self.ax.plot([x_min, x_max], [from_value, from_value], color=self.mark_color, linestyle='-', zorder=20, label='marked_min')
#                     self.ax.plot([x_min, x_max], [to_value, to_value], color=self.mark_color, linestyle='-', zorder=21, label='marked_max')
#                     self.span = ax_span_function(from_value, to_value, facecolor=self.mark_color, alpha=alpha, label='marked_span')
#         #            self.span = self.ax.axhspan(value_list[top_index], value_list[bottom_index], facecolor=self.mark_color, alpha=alpha, label='marked_span')
#                 else:
#                     self.ax.plot([from_value, from_value], [y_min, y_max], color=self.mark_color, linestyle='-', zorder=20, label='marked_min')
#                     self.ax.plot([to_value, to_value], [y_min, y_max], color=self.mark_color, linestyle='-', zorder=21, label='marked_max')
#                     self.span = ax_span_function(from_value, to_value, facecolor=self.mark_color, alpha=alpha, label='marked_span')


    def delete_all_data(self):
        for line_id in self.x_data:
            self.set_data([], [], line_id)
            
        self.reset_ax()
        
    #===========================================================================
    def set_data(self, x=False, y=False, z=None, c=None, line_id='default', exclude_index=[], call_targets=True, colorbar_title='', **kwargs):

        try:
            self.p['scatter_plot'].remove()
        except:
            pass

        if kwargs.get('contour_plot'):
            cid = 'contour_plot'
            if 'contour_plot' not in self.p:
                self.p[cid] = None
            self.p[cid] = self.ax.contourf(x, y, z, kwargs.get('nr_levels', 50))

        elif c:
            # Scatter data
            self.x_data[line_id] = x
            self.y_data[line_id] = y
            self.c_data[line_id] = c
            # print('type, len')
            # print(type(x), len(x))
            # print(type(y), len(y))
            # print(type(c), len(c))
            cid = 'scatter_plot'
            if 'scatter_plot' not in self.p:
                self.p[cid] = None
            if self.p[cid]:
                self.p[cid].remove()
            self.p[cid] = self.ax.scatter(x, y, c=c, s=100, marker='o', **kwargs)
                                      # cmap=kwargs.get('cmap', None),
                                      # vmin=kwargs.get('vmin', None),
                                      # vmax=kwargs.get('vmax', None))
            if colorbar_title:
                self.cbaxes = inset_axes(self.ax, width="5%", height="30%", loc=4)
                self.cbar = self.parent.fig.colorbar(self.p[cid], cax=self.cbaxes, orientation='vertical')
                self.cbaxes.yaxis.set_ticks_position('left')
                self.cbar.ax.set_title(colorbar_title)
                font = matplotlib.font_manager.FontProperties(family='times new roman', style='italic', size=10)
                text = self.cbaxes.title
                text.set_font_properties(font)

        else:
            # Create new prop dict if not in self.prop
            if line_id not in self.prop:
                self.prop[line_id] = self.default_prop.copy()

            # Update current prop dict
            self.prop[line_id].update(**kwargs)

            if not isinstance(x, bool) and not isinstance(y, bool):
                x = np.array(x)
                y = np.array(y)
                if exclude_index:
                    self.x_data[line_id] = []
                    for k, value in enumerate(x):
                        if k in exclude_index:
                            self.x_data[line_id].append(np.nan)
                        else:
                            self.x_data[line_id].append(value)
                    self.y_data[line_id] = y

                else:
                    self.x_data[line_id] = x
                    self.y_data[line_id] = y
            elif line_id not in self.x_data:
                print('No data to plot!')
                return

            self.reset_all_marked()
            self.visual_index = range(len(self.y_data[line_id]))

            if line_id not in self.p:
                self.p[line_id] = None
            if not self.p[line_id]:
                self.p[line_id], = self.ax.plot(self.x_data[line_id], self.y_data[line_id], **self.prop[line_id])
            else:
                self.p[line_id].set_data(self.x_data[line_id], self.y_data[line_id])
                self.p[line_id].set(**self.prop[line_id])


        if call_targets:
            self.parent.call_targets()

    #===========================================================================
    def set_prop(self, line_id='default', **kwargs):
        if line_id in self.prop: 
            self.prop[line_id].update(**kwargs)
            self.set_data(line_id=line_id)         
    
    #===========================================================================
    def set_mark_color(self, color):
        color_list = ['red', 'magenta', 'cyan', 'green']
        self.item_colors = [self.prop[item]['color'] for item in self.prop]
#         self.item_colors = self.color.items()
        for c in color_list:
            if c not in self.item_colors:
                self.mark_color = c
                return
         
    #===========================================================================
    def zoom_to_data(self, call_targets=True):
        self.set_x_limits(call_targets=False)
        self.set_y_limits(call_targets=False)
        if call_targets:
            self.parent.call_targets()

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
        if self.p:
            if limits:
                x_min, x_max = limits
            else:
                # Find min and max
                # try:
                #     mi_list = [np.nanmin(self.x_data[key]) for key in self.x_data if self.x_data[key].size]
                #     ma_list = [np.nanmax(self.x_data[key]) for key in self.x_data if self.x_data[key].size]
                # except:
                #     # Time series
                #     mi_list = [min(self.x_data[key]) for key in self.x_data if self.x_data[key].size]
                #     ma_list = [max(self.x_data[key]) for key in self.x_data if self.x_data[key].size]

                try:
                    mi_list = [np.nanmin(self.x_data[key]) for key in self.x_data if len(self.x_data[key])]
                    ma_list = [np.nanmax(self.x_data[key]) for key in self.x_data if len(self.x_data[key])]
                except:
                    # Time series
                    mi_list = [min(self.x_data[key]) for key in self.x_data if len(self.x_data[key])]
                    ma_list = [max(self.x_data[key]) for key in self.x_data if len(self.x_data[key])]

                if not mi_list:
                    return
                
                try:
                    mi = np.nanmin(mi_list)
                    ma = np.nanmax(ma_list)
                    
                    margin = abs(ma-mi)*0.1
                    x_min = mi - margin
                    x_max = ma + margin
                    
                    # print('='*30)
                    # print('margin', margin)
                    # print('mi', mi)
                    # print('ma', ma)
                    # print('x_min', x_min)
                    # print('x_max', x_max)
                    
                except:
                    # Time series
                    x_min = min(mi_list)
                    x_max = max(ma_list)

                
                
            self.ax.set_xlim([x_min, x_max])

            if self.time_axis:
                try:
                    self._set_date_ticks()
                except:
                    pass

            if call_targets:
                self.parent.call_targets()


    #===========================================================================
    def set_y_limits(self, limits=[], call_targets=True):
        if self.p:
            if limits:
                y_min, y_max = limits
            else:
                # Find min and max
                # mi_list = [np.nanmin(self.y_data[key]) for key in self.y_data if self.y_data[key].size]
                # ma_list = [np.nanmax(self.y_data[key]) for key in self.y_data if self.y_data[key].size]

                mi_list = [np.nanmin(self.y_data[key]) for key in self.y_data if len(self.y_data[key])]
                ma_list = [np.nanmax(self.y_data[key]) for key in self.y_data if len(self.y_data[key])]
                
                if not mi_list:
                    return
                
                mi = np.nanmin(mi_list)
                ma = np.nanmax(ma_list)
                
                margin = abs(ma-mi)*0.1

                y_min = mi - margin
                y_max = ma + margin
                
                # print('='*30)
                # print('margin', margin)
                # print('mi', mi)
                # print('ma', ma)
                # print('y_min', y_min)
                # print('y_max', y_max)
                
            self.ax.set_ylim([y_min, y_max])
            if call_targets:
                self.parent.call_targets()             
    
    #===========================================================================
    def set_x_label(self, label=u'', sync_color_with_line_id='default'):
        if self.ax:
            self.x_label = self.ax.set_xlabel(label)
            if self.parent.sync_colors in self.prop: 
                self.x_label.set_color(self.prop[sync_color_with_line_id]['color'])
#                 self.label.set_color(self.color[sync_color_to_line_id])
            self.parent.call_targets()
            
    #===========================================================================
    def set_y_label(self, label=u'', sync_color_with_line_id='default'):
        if self.ax:
            self.y_label = self.ax.set_ylabel(label)
            if self.parent.sync_colors in self.prop: 
                self.y_label.set_color(self.prop[sync_color_with_line_id]['color'])
#                 self.label.set_color(self.color[sync_color_to_line_id])
            self.parent.call_targets()
                
    #===========================================================================
    def set_x_grid(self, grid_on=True, sync_color_with_line_id='default'):
        if self.ax: 
            if not grid_on:
                self.ax.grid(grid_on, axis='x')
            elif self.parent.sync_colors in self.prop:
                color = self.prop[sync_color_with_line_id]['color']
                self.ax.grid(b=grid_on, axis='x', which='major', color=color, linestyle=':')
            else:
                self.ax.grid(grid_on, axis='x', linestyle=':') 
            self.parent.call_targets()
            
    #===========================================================================
    def set_y_grid(self, grid_on=True, sync_color_with_line_id='default'):
        if self.ax: 
            if not grid_on:
                self.ax.grid(grid_on, axis='y')
            elif self.parent.sync_colors in self.prop:
                color = self.prop[sync_color_with_line_id]['color']
                self.ax.grid(b=grid_on, axis='y', which='major', color=color, linestyle=':')
            else:
                self.ax.grid(grid_on, axis='y', linestyle=':') 
            self.parent.call_targets()

    def set_title(self, title):
        if self.ax:
            self.ax.set_title(title)

#===========================================================================
#===========================================================================
#===========================================================================         
class App(tk.Tk):
    #===========================================================================
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs) 
        self.nr_points = 50
        self.plot_series = Plot(orientation='h')
        self.fig = self.plot_series.fig
        self._set_start_frame()
        self._set_frame_plot()
        self._set_frame_buttons()
        self.plot_series.add_target(self.update_canvas)
      
    #========================================================================== 
    def _set_start_frame(self):
        self.frame_plot = ttk.Labelframe(self)
        self.frame_plot.grid(row=0, column=0)
        
        self.frame_buttons = ttk.Labelframe(self)
        self.frame_buttons.grid(row=1, column=0)
        
        self.grid_columnconfigure(0, weight=1)
        
          
    #========================================================================== 
    def _set_frame_plot(self):
        frame = self.frame_plot
        frame.grid_columnconfigure(0, weight=1)
        """
        Adds map and toolbar (if selected in constructor) to the given frame. 
        """
        self.frame = tk.Frame(frame)
        self.frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.frame.grid_columnconfigure(0, weight=1)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    #========================================================================== 
    def _set_frame_buttons(self):
        frame = self.frame_buttons
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_columnconfigure(2, weight=1)
        frame.grid_columnconfigure(3, weight=1)
        
        ttk.Button(frame, text=u'Ax1', command=self._set_ax1).grid(row=0, column=0)
        ttk.Button(frame, text=u'Ax2', command=self._set_ax2).grid(row=0, column=1)
        
        ttk.Button(frame, text=u'Set limits', command=self._set_limits).grid(row=1, column=2)
        ttk.Button(frame, text=u'Set labels', command=self._set_labels).grid(row=2, column=2)
        ttk.Button(frame, text=u'Set colors', command=self._set_colors).grid(row=3, column=2)
        
        ttk.Button(frame, text=u'Set markerstyles', command=self._set_markers).grid(row=1, column=3)
        ttk.Button(frame, text=u'Set markersize', command=self._set_markersize).grid(row=2, column=3)
        ttk.Button(frame, text=u'Set linestyle', command=self._set_linestyle).grid(row=3, column=3)
        
        ttk.Button(frame, text=u'Mark min', command=self._mark_min).grid(row=1, column=4)
        ttk.Button(frame, text=u'Mark max', command=self._mark_max).grid(row=2, column=4)
        
        ttk.Button(frame, text=u'Mark point', command=self._mark_point).grid(row=4, column=0)
        

    #========================================================================== 
    def update_canvas(self):
        self.canvas.draw()
    
    #========================================================================== 
    def _mark_min(self):
        self.plot_series.add_mark_range_target('first', color='r')
        self.plot_series.mark_range_from_left()    
        
    #========================================================================== 
    def _mark_max(self):
        self.plot_series.add_mark_range_target('first', color='r')
        self.plot_series.mark_range_from_right()
       
    #========================================================================== 
    def _mark_point(self):
        self.plot_series.mark_points()
        
    #========================================================================== 
    def _set_limits(self):
        self.plot_series.set_x_limits(ax=1, limits=[0,30])
        self.plot_series.set_x_limits(ax=2)
        self.plot_series.set_y_limits()
    
    #========================================================================== 
    def _set_labels(self):
        label = str(random.randint(1000,9999))
        self.plot_series.set_label('test label')
        
        label = str(random.randint(1000,9999))
        self.plot_series.set_first_label(label)
        
        label = str(random.randint(1000,9999))
        self.plot_series.set_second_label(label)
        
    #========================================================================== 
    def _set_colors(self):
        c = ['r','g','b','m', 'c']
        i = random.randint(0,4)
        self.plot_series.set_prop(ax=1, color=c[i])
        i = random.randint(0,4)
        self.plot_series.set_prop(ax=2, color=c[i])
        
    #========================================================================== 
    def _set_markers(self):
        c = ['<','>','s','*','v']
        i = random.randint(0,4)
        self.plot_series.set_prop(ax=1, marker=c[i])
        i = random.randint(0,4)
        self.plot_series.set_prop(ax=2, marker=c[i])
        
    #========================================================================== 
    def _set_markersize(self):
        c = [2,4,6,8,10]
        i = random.randint(0,4)
        self.plot_series.set_prop(ax=1, markersize=c[i])
        i = random.randint(0,4)
        self.plot_series.set_prop(ax=2, markersize=c[i])
        
    #========================================================================== 
    def _set_linestyle(self):
        c = ['-','--','._',':', '']
        i = random.randint(0,4)
        self.plot_series.set_prop(ax=1, linestyle=c[i])
        i = random.randint(0,4)
        self.plot_series.set_prop(ax=2, linestyle=c[i])
       
    #========================================================================== 
    def _set_ax1(self):
        r = random.randint(5, 20)
        y = range(self.nr_points)
        y = map(lambda x: -x, range(self.nr_points))
        x = []
        for r in range(self.nr_points):
            x.append(random.randint(0,r))
        self.plot_series.add_first_ax()
        self.plot_series.first_ax.set_data(x, y)
        
        if not hasattr(self, 'marked1'):
            self.marked1 = self.plot_series.add_mark_range_target('first_ax', color='g')
    
    #========================================================================== 
    def _set_ax2(self):
        r = random.randint(5, 20)
        y = range(self.nr_points)
        y = map(lambda x: -x, range(self.nr_points))
        x = []
        for r in range(self.nr_points):
            x.append(random.randint(0,r))
        self.plot_series.add_second_ax()
        self.plot_series.second_ax.set_data(x, y)
        
        if not hasattr(self, 'marked2'):
            self.marked2 = self.plot_series.add_mark_range_target('second_ax', color='g')
        
#===========================================================================
#===========================================================================
#===========================================================================         
class old_App(tk.Tk):
    #===========================================================================
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs) 
        self.plot_series = Plot()
        self.fig = self.plot_series.fig
        self._set_start_frame()
        self._set_frame_plot()
        self._set_frame_buttons()
        self.plot_series.add_target(self.update_canvas)
      
    #========================================================================== 
    def _set_start_frame(self):
        self.frame_plot = ttk.Labelframe(self)
        self.frame_plot.grid(row=0, column=0)
        
        self.frame_buttons = ttk.Labelframe(self)
        self.frame_buttons.grid(row=1, column=0)
        
        self.grid_columnconfigure(0, weight=1)
        
          
    #========================================================================== 
    def _set_frame_plot(self):
        frame = self.frame_plot
        frame.grid_columnconfigure(0, weight=1)
        """
        Adds map and toolbar (if selected in constructor) to the given frame. 
        """
        self.frame = tk.Frame(frame)
        self.frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.frame.grid_columnconfigure(0, weight=1)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    #========================================================================== 
    def _set_frame_buttons(self):
        frame = self.frame_buttons
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_columnconfigure(2, weight=1)
        frame.grid_columnconfigure(3, weight=1)
        
        ttk.Button(frame, text=u'Ax1', command=self._set_ax1).grid(row=0, column=0)
        ttk.Button(frame, text=u'Ax2', command=self._set_ax2).grid(row=0, column=1)
        
        ttk.Button(frame, text=u'Set limits', command=self._set_limits).grid(row=1, column=2)
        ttk.Button(frame, text=u'Set labels', command=self._set_labels).grid(row=2, column=2)
        ttk.Button(frame, text=u'Set colors', command=self._set_colors).grid(row=3, column=2)
        
        ttk.Button(frame, text=u'Set markerstyles', command=self._set_markers).grid(row=1, column=3)
        ttk.Button(frame, text=u'Set markersize', command=self._set_markersize).grid(row=2, column=3)
        ttk.Button(frame, text=u'Set linestyle', command=self._set_linestyle).grid(row=3, column=3)
        
        ttk.Button(frame, text=u'Mark min', command=self._mark_min).grid(row=1, column=4)
        ttk.Button(frame, text=u'Mark max', command=self._mark_max).grid(row=2, column=4)
        
        ttk.Button(frame, text=u'Mark point', command=self._mark_point).grid(row=4, column=0)
        
     
    #========================================================================== 
    def update_canvas(self):
        self.canvas.draw()
    
    #========================================================================== 
    def _mark_min(self):
        self.plot_series.mark_min_range()    
        
    #========================================================================== 
    def _mark_max(self):
        self.plot_series.mark_max_range() 
       
    #========================================================================== 
    def _mark_point(self):
        self.plot_series.mark_points()
        
    #========================================================================== 
    def _set_limits(self):
        self.plot_series.first_ax.set_limits([0,30])
        self.plot_series.second_ax.set_limits()
        self.plot_series.set_z_limits()
    
    #========================================================================== 
    def _set_labels(self):
        label = str(random.randint(1000,9999))
        self.plot_series.first_ax.set_label(label)
        label = str(random.randint(1000,9999))
        self.plot_series.second_ax.set_label(label)
        
    #========================================================================== 
    def _set_colors(self):
        c = ['r','g','b','m', 'c']
        i = random.randint(0,4)
        self.plot_series.first_ax.set_color(c[i])
        i = random.randint(0,4)
        self.plot_series.second_ax.set_color(c[i])
        
    #========================================================================== 
    def _set_markers(self):
        c = ['<','>','s','*','v']
        i = random.randint(0,4)
        self.plot_series.first_ax.set_markerstyle(c[i])
        i = random.randint(0,4)
        self.plot_series.second_ax.set_markerstyle(c[i])
        
    #========================================================================== 
    def _set_markersize(self):
        c = [2,4,6,8,10]
        i = random.randint(0,4)
        self.plot_series.first_ax.set_markersize(c[i])
        i = random.randint(0,4)
        self.plot_series.second_ax.set_markersize(c[i])
        
    #========================================================================== 
    def _set_linestyle(self):
        c = ['-','--','._',':', None]
        i = random.randint(0,4)
        self.plot_series.first_ax.set_linestyle(c[i])
        i = random.randint(0,4)
        self.plot_series.second_ax.set_linestyle(c[i])
       
    #========================================================================== 
    def _set_ax1(self):
        r = random.randint(5, 20)
        y = range(10)
        x = []
        for r in range(10):
            x.append(random.randint(0,r))
        self.plot_series.add_first_ax()
        self.plot_series.first_ax.set_data(x, y)
        
        if not hasattr(self, 'marked1'):
            self.marked1 = self.plot_series.add_mark_range_target('first_ax', color='g')
    
    #========================================================================== 
    def _set_ax2(self):
        r = random.randint(5, 20)
        y = range(10)
        x = []
        for r in range(10):
            x.append(random.randint(0,r))
        self.plot_series.add_second_ax()
        self.plot_series.second_ax.set_data(x, y)
        
        if not hasattr(self, 'marked2'):
            self.marked2 = self.plot_series.add_mark_range_target('second_ax', color='g')
        
"""
========================================================================
========================================================================
========================================================================
"""
class SelectFromCollection(object):
    """Select indices from a matplotlib collection using `LassoSelector`.

    Selected indices are saved in the `ind` attribute. This tool highlights
    selected points by fading them out (i.e., reducing their alpha values).
    If your collection has alpha < 1, this tool will permanently alter them.

    Note that this tool selects collection objects based on their *origins*
    (i.e., `offsets`).

    Parameters
    ----------
    ax : :class:`~matplotlib.axes.Axes`
        Axes to interact with.

    collection : :class:`matplotlib.collections.Collection` subclass
        Collection you want to select from.

    alpha_other : 0 <= float <= 1
        To highlight a selection, this tool sets all selected points to an
        alpha value of 1 and non-selected points to `alpha_other`.
    ----------
    
    Modified by Magnus W
    
    """

    def __init__(self, ax, collection, alpha_other=0.3, target=None):
        self.canvas = ax.figure.canvas
        self.collection = collection
        self.alpha_other = alpha_other
        self.target = target
        
#        self.xys = collection.get_offsets()
        self.xys = collection
#        self.Npts = len(self.xys)

        # Ensure that we have separate colors for each object
#        self.fc = collection.get_facecolors()
#        if len(self.fc) == 0:
#            raise ValueError('Collection must have a facecolor')
#        elif len(self.fc) == 1:
#            self.fc = np.tile(self.fc, self.Npts).reshape(self.Npts, -1)

        self.lasso = LassoSelector(ax, onselect=self.onselect)
        self.ind = []

    def onselect(self, verts):
        path = Path(verts)
        self.ind = np.nonzero([path.contains_point(xy) for xy in self.xys])[0]
#        self.fc[:, -1] = self.alpha_other
#        self.fc[self.ind, -1] = 1
#        self.collection.set_facecolors(self.fc)
        self.canvas.draw_idle()
        if self.target:
            self.target()

    def disconnect(self):
        self.lasso.disconnect_events()
#        self.fc[:, -1] = 1
#        self.collection.set_facecolors(self.fc)
        self.canvas.draw_idle()

#========================================================================== 
def main():
    app = App()
    app.focus_force()
    app.mainloop()
    
if __name__ == '__main__':
    main()
