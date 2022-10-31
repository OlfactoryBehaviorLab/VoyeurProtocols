'''
Modified 2/
/2019
Dewan Lab
This function trains the animal to lick from either the left, right, or both lick tubes for a water reward.
The trial time and inter-trial intervals are fixed. 
An LED signals the start of the trial
Option to use the final valve or no final valve
'''

## STILL TO DO
## 2. Fix the spacing of GUI so it looks better
## 4. convert h5 file
## 5. code in right or left stimuli

import voyeur.db as db
from olfactometry import Olfactometer
from olfactometry.main import Olfactometers
from numpy import append, arange, hstack, nan, isnan, copy, negative
from voyeur.monitor import Monitor
from voyeur.protocol import Protocol, TrialParameters, time_stamp
from voyeur.exceptions import SerialException, ProtocolException
from traits.trait_types import Button
from traits.api import Int, Str, Array, Instance, HasTraits, Float, Enum, Bool, Range
from traitsui.api import View, Group, HGroup, VGroup, Item, spring
from chaco.api import ArrayPlotData, Plot, VPlotContainer, DataRange1D
from enable.component_editor import ComponentEditor
from enable.component import Component
from traitsui.editors import ButtonEditor, DefaultOverride
from pyface.timer.api import Timer, do_after
from pyface.api import FileDialog, OK
from chaco.tools.api import PanTool
from chaco.axis import PlotAxis
from chaco.scales.api import TimeScale
from chaco.scales_tick_generator import ScalesTickGenerator
from chaco.scales.api import CalendarScaleSystem
from datetime import datetime
from configobj import ConfigObj
from copy import deepcopy
import random, time, os
from numpy.random import permutation  # # need numpy 1.7 or higher for choice function
from random import choice, randint
from OlfactometerUtilities.range_selections_overlay import RangeSelectionsOverlay
from OlfactometerUtilities import Voyeur_utilities

#-------------------------------------------------------------------------------
class Lick2Afc(Protocol):
    """Protocol for 2AFC or Go-NoGo task on a lick-based choice"""

    STREAMSIZE = 20000
    BLOCKSIZE = 24
    SLIDINGWINDOW = 10
    ARDUINO = 1
    nitrogen = 100
    air = 900
    sniff_scale = 1 #Tang added
    flows=(air,nitrogen)

#-----------------------------------------------------------------------------
#Potential Responses
    stimuli = {
               "Right" : [],
               "Left": [],
               "RightorLeft": []
               }
#-----------------------------------------------------------------------------
    # protocol parameters (session parameters for Voyeur)
    mouse = Int(0, label='mouse') #Default is in 
    rig = Str("", label='rig') 
    stamp = Str(label='stamp')
    session = Int(0, label='session')
    protocol_name = Str(label='protocol')
    enable_blocks = Enum("Blocks", "No Blocks")
    rewards = Int(0, label="Total rewards")
    response_type ='lick'
    protocol_type = Enum('Please Select',
                         'Single port',
                         'Alternate',
                         'Blocks',
                         )
    trial_structure = Enum('Please Select', "Blocks", "Random", "deBias")
    blocksize = Int(10, label="Block size")
    trialNumber = Int(1, label='Trial')
    trialtype = Enum(("Right", "Left", "RightorLeft"), label="Trial type")
    waterdur = Int(0, label="Water valve 1 duration")
    waterdur2 = Int(0, label="Water valve 2 duration")
    wateramt = Float(0, label="Water valve 1 amount")
    wateramt2 = Float(0, label="Water valve 2 amount")
    fvdur = Int(0, label="Final valve (On=1)")
    trialdur = Int(0, label="Trial duration")
    interTrialIntervalSeconds = Int(0, label='ITI seconds')
    lickgraceperiod = Int(0, label="Lick grace period")
    
    # event
    tick = Array
    result = Array
    trialstart = Int(0, label="Trial start time stamp")
    trialend = Int(0, label="Trial end time stamp")
    paramsgottime = Int(0, label="Time parameters received time stamp")
    no_sniff = Bool(False, label="Lost sniffing in last trial")
    fvOnTime = Int(0, label="Time of final valve open")
    three_missed = Bool(False, label="Finished 1000 Trials")
    right_performance = Float(100.0, label="Right (LC2) Performance")
    left_performance = Float(100.0, label="Left (LC1) Performance")
    total_performance = Float(100.0, label="Total Performance")
    nolick_performance = Float(0.0, label="Missed Trial %")
    total_water = Float(0.0, label="Total Water (ul)")
    
    # Timers
    elapsed_time_sec = Int(0, label = 'sec:')
    elapsed_time_min = Int(0, label = 'Time since session start - min:')
    trial_time = Int(0, label = 'Time since last response (sec)')

    # streaming data
    iteration = Array
    sniff = Array
    lick1 = Array
    lick2 = Array


    # internal (recalculated for each trial)
    _next_trialNumber = Int(0, label='trialNumber')
    _next_trialtype = Enum(("Right", "Left", "RightorLeft"), label="Trial type")
    _last_trialtype = Enum(("Right", "Left", "RightorLeft"), label="Last trial type")
    _equalBlock = True
    _next_odorconc = Float(0, label="Odor concentration")
    _next_odor = Str("Next odor", label="Odor")  # addition of odor concentration
    _next_trial_start = 0
    _wv = Str('1')
    _windowResults = []  # bias correction
    _windowRightResults = []  # bias correction
    _windowSameResults = []
    _righttrials = Array
    _lefttrials = Array
    _corrights = 0
    _corlefts = 0
    _cortotal = 0
    _totalRightTrials = 0
    _totalLeftTrials = 0
    _blockRightMoves = 0
    _blockLeftMoves = 0
    _falserights = 0
    _falselefts = 0
    _nomoves = 0
    _bilicks = 0
    _paramsenttime = float()
    _resultstime = float()
    _laststreamtick = Float(0)
    _lastlickstamp = 0
    _previousendtick = 0
    _inblockcorrect = 0
    _stimindex = int(0)

    _unsyncedtrials = 0
    _first_trial_block = []  # deBias
    _leftstimblock = []
    _rightstimblock = []

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # GUI
    
    _olfactometer = Instance(Olfactometer)          #Initial olfactometer
    monitor = Instance(object)
    stream_plots = Instance(Component)
#    stream_plot = Instance(Plot, label="Sniff") #ADD BACK IF YOU WANT SNIFF TO BE PLOTTED
    stream_event_plot = Instance(Plot, label="Events")
    start_button = Button()
    start_label = Str('Start')
    pause_button = Button()
    pause_label = Str('Pause')
    save_as_button = Button("Save as")
    olfactory_button = Button()
    olfactory_label = Str('Olfactometer')
    fv_button = Button("Final Valve")
    fv_label = Str("Final Valve (OFF)")
    cal_button1 = Button("Cal Water 1")
    cal_button2 = Button("Cal Water 2")
    water_button1 = Button(label="Water Valve 1")
    water_button2 = Button(label="Water Valve 2")


    session_group = Group(
                        Item('mouse', enabled_when='not monitor.running'),
                        Item('session', enabled_when='not monitor.running'),
                        Item('rig', enabled_when='not monitor.running'),
                        Item('fvdur', enabled_when='not monitor.running'),
                        Item('protocol_type', enabled_when='not monitor.running'),
                        
                        HGroup(Item('trial_structure', enabled_when='not (protocol_type=="Single port")'),
                                spring,
                                Item('blocksize', visible_when='trial_structure == "Blocks"',
                                      width=-100, tooltip="Block Size", show_label=False, full_size=False, springy=False, resizable=False)),
                        Item('three_missed',style = 'readonly'),
                        label='Session',
                        show_border=True
                    )


    arduino = VGroup(
        HGroup(
            VGroup( Item('olfactory_button',
                         editor=ButtonEditor(label_value='olfactory_label'),
                         show_label=False),
                    Item('fv_button',
                         editor=ButtonEditor(style="button", label_value='fv_label'),
                         show_label=False),
                    ),
            VGroup(    Item('water_button1',
                         editor=ButtonEditor(style="button"),
                         show_label=False),
                    Item('water_button2',
                         editor=ButtonEditor(style="button"),
                         show_label=False),
                    ),
            VGroup(Item('cal_button1',
                        editor=ButtonEditor(style="button"),
                        enabled_when='not monitor.recording',
                        show_label=False),
                   Item('cal_button2',
                        editor=ButtonEditor(style="button"),
                        enabled_when='not monitor.recording',
                        show_label=False)
                   ),
            VGroup(Item('waterdur', enabled_when='not monitor.recording'),
                   Item('wateramt', enabled_when='not monitor.recording')
                   ),
            VGroup(Item('waterdur2', enabled_when='not monitor.recording'),
                   Item('wateramt2', enabled_when='not monitor.recording')
                  )
        ),
        label="Arduino Control",
        show_border=True
    )


    control = VGroup(
            HGroup(
                VGroup(Item('start_button',
                          editor=ButtonEditor(label_value='start_label'),
                          show_label=False),
                       Item('pause_button',
                          editor=ButtonEditor(label_value='pause_label'),
                          show_label=False,
                          enabled_when='monitor.running'),
                        )
                            ),
                    label='Control',
                    show_border=True,
                    )

    current = Group(
                        HGroup(Item('elapsed_time_min',style='readonly'),Item('elapsed_time_sec',style = 'readonly'),show_border = False), 
                        Item('trialNumber', style='readonly'),
                        Item('interTrialIntervalSeconds'),
                        Item('trialtype'),
                        Item('trialdur'),
                        Item('lickgraceperiod'),


                        label='Current Trial',
                        show_border=True
                    )

    next = Group(
                    Item('_next_trialtype'),
                    Item('total_performance',style = 'readonly'),
                    Item('left_performance',style = 'readonly'),
                    Item('right_performance',style = 'readonly'),
                    Item('nolick_performance',style = 'readonly'),
                    Item('total_water',style = 'readonly'),
                    label='Next Trial',
                    show_border=True
                )

    event = Group(
                    Item('event_plot', editor=ComponentEditor(), height=150, padding=-15),
                    label='Event', padding=2,
                    show_border=True
                  )
   
    
    stream = Group (
                        Item('stream_plots', editor=ComponentEditor(), show_label=False, height=200,
                             padding=2),
                        label='Streaming', padding=2,
                        show_border=True,
                    )

    main = View(
                    VGroup(
                            HGroup(control, arduino),
                            HGroup(session_group,
                                    current,
                                    next),
                            stream,
                            show_labels=True,
                    ),
                    title='Dewan Lab 2AFC Training Paradigm',
                    width=730,
                    height=700,
                    x=10,       #X position on the screen that the GUI opens
                    y=30,       #Y position on the screen that the GUI opens
                    resizable=True
                )
#----------------------------------------------------------------------------------------------------------------------------'''

#--------GUI FUNCTIONS--------GUI FUNCTIONS--------GUI FUNCTIONS--------GUI FUNCTIONS---------GUI FUNCTIONS---------GUI FUNCTIONS---------
#This section handles all the choices possible in the GUI       

#PROTOCOL TYPE CHANGED IN GUI                               
        
    def _protocol_type_changed(self):
        if self.protocol_type == 'Single Port':
            self.trialtype = 'Left'
        elif self.protocol_type == 'Alternate':
            pass
        elif self.protocol_type == 'Blocks':
            pass
        return

#MOUSE NUMBER CHANGED GUI     
    def _mouse_changed(self):
        new_stamp = time_stamp()
        db = 'mouse' + str(self.mouse) + '_' + 'sess' + str(self.session) \
                    + '_' + new_stamp
        if self.db != db:
            self.db = db
        return

#SESSION NUMBER CHANGED GUI  
    def _session_changed(self):
        new_stamp = time_stamp()
        self.db = 'mouse' + str(self.mouse) + '_' + 'sess' + str(self.session) \
            + '_' + new_stamp

#WATER SOLENOID VALVE OPEN TIME CHANGED IN THE GUI            
    def _waterdur_changed(self):
        pass
#        self.save_water_params()
        return
    
    def _waterdur2_changed(self):
        pass
#        self.save_water_params()
        return


#--------------------------------------------------------------------------------------------------------------------------'''

#--------GUI BUTTONS--------GUI BUTTONS--------GUI BUTTONS--------GUI BUTTONS---------GUI BUTTONS---------GUI BUTTONS---------
#This section handles all the buttons that can be clicked in the GUI

#START BUTTON. 
    def _start_button_fired(self):
        #If the program is already running.
        if self.monitor.running:
            self.start_label = 'Start'
            if self.fv_label == "Final Valve (ON)":
                self._fv_button_fired()
            self.session_timer.Stop()
            self.monitor.stop_acquisition()
            self.monitor.send_command('threemissed off');
            self.monitor.send_command("fv off");
            print "Unsynced trials: ", self._unsyncedtrials
            self.session += 1
        
        #If the program is not running
        else:
            if self.protocol_type == 'Please Select':
                print 'ERROR: Please select a protocol type to begin.'
                return
            if self.protocol_type == 'Conditioning' and self.trial_structure == 'Please Select':
                print 'ERROR: Please select a protocol type to begin.'
                return
            if self.protocol_type == 'Training' and self.trial_structure == 'Please Select':
                print 'ERROR: Please select a protocol type to begin.'
                return
            if self.monitor.protocol_name != self.protocol_name:
                print "WARNING, ARDUINO PROTOCOL IS NOT: " + self.protocol_name
                print 'Please exit and upload correct sketch to arduino before starting.'
                return
            
            self.start_label = 'Stop'
            self._restart()
            new_stamp = time_stamp()
            self.elapsed_time_min = 0
            self.elapsed_time_sec = 0
            self.trial_time = 0
            self.session_timer = Timer(1000,self.timer_update_task)
            self.db = 'mouse' + str(self.mouse) + '_' + 'sess' + str(self.session) \
                + '_' + new_stamp
            self.monitor.database_file = 'C:/VoyeurData/' + self.db
            self.monitor.start_acquisition()
        return

#PAUSE BUTTON
    def _pause_button_fired(self):
        if self.monitor.recording:
            self.monitor.pause_acquisition()
            self.pause_label = 'Unpause'
        else:
            self.pause_label = 'Pause'
            self.trialNumber += 1
            self.monitor.unpause_acquisition()
        return

#SAVE AS BUTTON
    def _save_as_button_fired(self):
        dialog = FileDialog(action="save as")
        dialog.open()
        if dialog.return_code == OK:
            self.db = os.path.join(dialog.directory, dialog.filename)
        return

#FINAL VALVE BUTTON
    def _fv_button_fired(self):
        if self.monitor.recording:
            self._pause_button_fired()
        if self.fv_label == "Final Valve (OFF)":
            self.monitor.send_command("fv on")
            self.fv_label = "Final Valve (ON)"
        elif self.fv_label == "Final Valve (ON)":
            self.monitor.send_command("fv off")
            self.fv_label = "Final Valve (OFF)"
        return

#OLFACTOMETER BUTTON    
    def _olfactory_button_fired(self):
        self.olfacto.show()
        if (self.olfacto is not None):
            self.olfacto.show()
        return
#WATER SOLENOID BUTTONS - 1 TIME    
    def _water_button1_fired(self):
        command = "wv 1 " + str(self.waterdur)
        self.monitor.send_command(command)
        return

    def _water_button2_fired(self):
        command = "wv 2 " + str(self.waterdur2)
        self.monitor.send_command(command)
        return

#WATER SOLENOID CALIBRATION BUTTONS - 100 TIMES
    def _cal_button1_fired(self):
        if self.monitor.recording:
            self._pause_button_fired()
        command = 'callibrate 1 ' + str(self.waterdur)
        self.monitor.send_command(command)
        return

    def _cal_button2_fired(self):
        if self.monitor.recording:
            self._pause_button_fired()
        command = 'callibrate 2 ' + str(self.waterdur2)
        self.monitor.send_command(command)
        return





#--------GUI PLOTS--------GUI PLOTS--------GUI PLOTS--------GUI PLOTS---------GUI PLOTS---------GUI PLOTS---------
#This section plots the licks and sniff data along with the blue mask that signals the trials. Sniff and lick streaming plots
#are intertwined so the plotting is just turned off and the size of the plot is minizied so it is not visible. 

#PLOTS EVENT DATA
    def _stream_event_plot_default(self):
        pass

    # needs to be removed
    def _stream_plots_default(self):

        container = VPlotContainer(bgcolor="transparent", fill_padding=False, padding=0)
        self.stream_plot_data = ArrayPlotData(iteration=self.iteration, sniff=self.sniff)
        y_range = DataRange1D(low=-2500, high=2500)
        plot = Plot(self.stream_plot_data, padding=25, padding_top=0, padding_left=60)
        plot.fixed_preferred_size = (0, 2)
        plot.value_range = y_range
        range_in_sec = self.STREAMSIZE / 1000.0
        self.iteration = arange(0.001, range_in_sec + 0.001, 0.001)
        self.sniff = [nan] * len(self.iteration)
        plot.plot(('iteration', 'sniff'), type='line', color='white', name="Sniff")
        self.stream_plot_data.set_data("iteration", self.iteration)
        self.stream_plot_data.set_data("sniff", self.sniff)
        bottom_axis = PlotAxis(plot, orientation="bottom", tick_generator=ScalesTickGenerator(scale=TimeScale(seconds=1)))
        plot.x_axis = bottom_axis
        plot.x_axis.title = "Time"
        self.stream_plot = plot
        plot.legend.visible = False
        plot.legend.bgcolor = "transparent"

        if 'Sniff' in self.stream_plot.plots.keys():
            sniff = self.stream_plot.plots['Sniff'][0]
            rangeselector = (RangeSelectionsOverlay(component=sniff, metadata_name='trials_mask'))
            sniff.overlays.append(rangeselector)
            datasource = getattr(sniff, "index", None)
            datasource.metadata.setdefault("trials_mask", [])

        self.stream_events_data = ArrayPlotData(iteration=self.iteration, lick1=self.lick1, lick2=self.lick2)  # , lick2 = self.lick2)
        plot = Plot(self.stream_events_data, padding=25, padding_bottom=0, padding_left=60,
                    index_mapper=self.stream_plot.index_mapper)
        plot.fixed_preferred_size = (100, 100)
        y_range = DataRange1D(low=0, high=3)
        plot.value_range = y_range
        plot.x_axis.orientation = "top"
        plot.x_axis.title_spacing = 5
        plot.x_axis.tick_generator = self.stream_plot.x_axis.tick_generator
        self.lick1 = [nan] * len(self.iteration)  # the last value is not nan so that the first incoming streaming value would be nan
        self.lick1[-1] = 0
        self.lick2 = [nan] * len(self.iteration)
        self.lick2[-1] = 0
        event_plot = plot.plot(("iteration", "lick1"), name="Left Licks (LC1)", color="red", line_width=5, render_style="hold")[0]
        plot.plot(("iteration", "lick2"), name="Right Licks (LC2)", color="blue", line_width=7, render_style="hold")
        event_plot.overlays.append(rangeselector)
        plot.legend.visible = True
        plot.legend.bgcolor = "transparent"
        plot.legend.align = 'ul'
        self.stream_events_data.set_data("lick1", self.lick1)
        self.stream_events_data.set_data("lick2", self.lick2)
        self.stream_event_plot = plot

        container.add(self.stream_plot)
        container.add(self.stream_event_plot)

        return container


    
    
#BLUE TRIAL MASK ON GUI PLOT    
    def _addtrialmask(self):
        if 'Sniff' in self.stream_plot.plots.keys():
            sniff = self.stream_plot.plots['Sniff'][0]
            datasource = getattr(sniff, "index", None)
            data = self.iteration
            if self._laststreamtick - self.trialend >= self.STREAMSIZE:
                return
            elif self._laststreamtick - self.trialstart >= self.STREAMSIZE:
                start = data[0]
            else:
#                print "trialstart =",self.trialstart
#                print "laststreamtick=",self._laststreamtick
#                print "index=",-self._laststreamtick + self.trialstart - 1
#                print "trialend =",self.trialend
                start = data[-self._laststreamtick + self.trialstart - 1]
            end = data[-self._laststreamtick + self.trialend - 1]
            datasource.metadata['trials_mask'] += (start, end)
        return

#UPDATES TICKS FOR STREAMING DATA
    def __laststreamtick_changed(self):

        shift = self._laststreamtick - self._previousendtick
        self._previousendtick = self._laststreamtick

        streams = self.stream_definition()
        if streams == None:
            return
        if 'sniff' in streams.keys():
            # get the sniff plot and add update the selection overlay
            if 'Sniff' in self.stream_plot.plots.keys():
                sniff = self.stream_plot.plots['Sniff'][0]
                datasource = getattr(sniff, "index", None)
                mask = datasource.metadata['trials_mask']
                new_mask = []
                for index in range(len(mask)):
                    mask_point = mask[index] - shift / 1000.0
                    if mask_point < 0.001:
                        if index % 2 == 0:
                            new_mask.append(0.001)
                        else:
                            del new_mask[-1]
                    else:
                        new_mask.append(mask_point)
                datasource.metadata['trials_mask'] = new_mask
        return

#--------SAVED DATA--------ARDUINO COMMUNICATION---------SAVED DATA---------ARDUINO COMMUNICATION---------SAVED DATA---------SAVED DATA---------
#This section includes all the variables that will be saved in the database. They are organized alphabetically in the eventual datafile
#Returns a dictionary of {name => db.type} defining Voyeur (protocol) and Behavioral controller (Controller) parameters
#The number associated with the controller dictionary needs to match arduino sketch. This is how the info is sent and parsed.
#The type also needs to be declared for each variable. This needs to be completed in the parameter definition section.    
#This is not called until the monitor is started and the stream is requested. It does not setup the monitor before start.


#TRIAL TYPE FOR THE NEXT TRIAL THAT WILL BE SENT TO ARDUINO
#PYTHON (PROTOCOL) AND BEHAVIORAL CONTROLLER (CONTROLLER) PARAMETERS THAT WILL BE SAVED IN THE DATABASE FILE (VOYEUR/OLFACTOMETER)     
    def trial_parameters(self):
        """Returns a class of TrialParameters for the next trial"""
        

        if self.trialtype == "Right":
            trial_type = 1
        elif self.trialtype == "Left":
            trial_type = 0
        elif self.trialtype == "RightorLeft":
            trial_type = 2


        protocol_params = {
                        "mouse"         : self.mouse,
                        "rig"           : self.rig,
                        "session"       : self.session,
                        'response_type' : self.response_type
                        }

       

        controller_dict = {
                           
                            "trialNumber"   : (1, db.Int, self.trialNumber),
                            "trialtype"     : (2, db.Int, trial_type),
                            "waterdur"      : (3, db.Int, self.waterdur),
                            "waterdur2"     : (4, db.Int, self.waterdur2),
                            "fvdur"         : (5, db.Int, self.fvdur),
                            "trialdur"      : (6, db.Int, self.trialdur),
                            "iti"           : (7, db.Int, self.interTrialIntervalSeconds * 1000),
                            'grace_period' : (8,db.Int, self.lickgraceperiod),
                            'rewards'       :(9,db.Int, self.rewards)
                            }

        # print controller_dict

        return TrialParameters(
                    protocolParams=protocol_params,
                    controllerParams=controller_dict
                )

    def protocol_parameters_definition(self):
        """Returns a dictionary of {name => db.type} defining protocol parameters"""

        params_def = {
            "mouse"         : db.Int,
            "rig"           : db.String32,
            "session"       : db.Int,
            'response_type' : db.String32,
        }


        return params_def

    def controller_parameters_definition(self):
        """Returns a dictionary of {name => db.type} defining controller parameters"""

        params_def = {
            "trialNumber"    : db.Int,
            "trialtype"      : db.Int,
            "waterdur"       : db.Int,
            "waterdur2"      : db.Int,
            "fvdur"          : db.Int,
            "trialdur"       : db.Int,
            "iti"            : db.Int,
            "fvtrig_on_exh"  : db.Int,
            'treadmill_response' :db.Int,
            'grace_period'  : db.Int,
            'rewards'       : db.Int
        }

        return params_def

    def event_definition(self):
        """Returns a dictionary of {name => (index,db.Type} of event parameters for this protocol"""

        return {
            "result"         : (1, db.Int),
            "paramsgottime"  : (2, db.Int),
            "starttrial"     : (3, db.Int),
            "endtrial"       : (4, db.Int),
            "no_sniff"       : (5, db.Int),
            "fvOnTime"       : (6, db.Int)
        }

    def stream_definition(self):
        """Returns a dictionary of {name => (index,db.Type,Arduino type)} of streaming data parameters for this protocol
        This is not called until the monitor is started and the stream is requested. It does not setup the monitor before start."""
        
        if self.response_type == 'treadmill':
            stream_def = {
                          "packet_sent_time" : (1, 'unsigned long', db.Int),
                          "sniff_samples"    : (2, 'unsigned int', db.Int),
                          "sniff"            : (3, 'int', db.FloatArray,),
    #                     "sniff_ttl"        : (4, db.FloatArray,'unsigned long'),
                          "lick1"            : (4, 'unsigned long', db.FloatArray),
                          "lick2"            : (5, 'unsigned long', db.FloatArray),
                          "treadmill"        : (6, 'int', db.FloatArray,)
                          }
        
        else:
            stream_def = {
                          "packet_sent_time" : (1, 'unsigned long', db.Int),
                          "sniff_samples"    : (2, 'unsigned int', db.Int),
                          "sniff"            : (3, 'int', db.FloatArray,),
#                         "sniff_ttl"        : (4, db.FloatArray,'unsigned long'),
                          "lick1"            : (4, 'unsigned long', db.FloatArray),
                          "lick2"            : (5, 'unsigned long', db.FloatArray)
                          }
        
        return stream_def

#-------------------------------------------------------------------------------------------------------------------------------------------


#--------PROCESS EVENT AND STREAM--------PROCESS EVENT AND STREAM---------PROCESS EVENT AND STREAM---------PROCESS EVENT AND STREAM---------
#This section....
        
#PROCESS EVENTS FROM BEHAVIORAL CONTROLLER
    def process_event_request(self, event):
        self.timestamp("end")
        self.paramsgottime = int(event['paramsgottime'])
        self.trialstart = int(event['starttrial'])
        self.trialend = int(event['endtrial'])
        result = int(event['result'])  # 1 is right, 2 is left, 3 left 4 right
        self.result = append(self.result, int(event['result']))
        
        if self.trialend > self._laststreamtick:
            self._shiftlicks(self.trialend - self._laststreamtick)
            self._laststreamtick = self.trialend
        self._addtrialmask()
        
         
        return

#PROCESS STREAMS FROM BEHAVIORAL CONTROLLER
    def process_stream_request(self, stream):
    
        if stream:
            num_sniffs = stream['sniff_samples']
            packet_sent_time = stream['packet_sent_time']

            # TODO: Decouple sniff and treadmill
            if packet_sent_time > self._laststreamtick + num_sniffs:
                lostsniffsamples = packet_sent_time - self._laststreamtick - num_sniffs
                print "lost sniff:", lostsniffsamples
                if lostsniffsamples > self.STREAMSIZE:
                    lostsniffsamples = self.STREAMSIZE
                lostsniffsamples = int(lostsniffsamples)
                # pad sniff signal with last value for the lost samples first then append received sniff signal
                new_sniff = hstack((self.sniff[-self.STREAMSIZE + lostsniffsamples:], [self.sniff[-1]] * lostsniffsamples))
                if stream['sniff'] is not None:
                    self.sniff = hstack((new_sniff[-self.STREAMSIZE + num_sniffs:],
                                         negative(stream['sniff'] * (2.44140625*self.sniff_scale))))
            else:
                if stream['sniff'] is not None:
                    new_sniff = hstack((self.sniff[-self.STREAMSIZE + num_sniffs:],
                                        negative(stream['sniff'] * (2.44140625*self.sniff_scale))))
                    self.sniff = new_sniff
            self.stream_plot_data.set_data("sniff", self.sniff)

            
            if 'treadmill' in stream.keys() and stream['treadmill'] is not None: # and is short circuit here and shouldn't error if no 'treadmill' key in dict.
                if packet_sent_time > self._laststreamtick + num_sniffs:
                    new_treadmill = hstack((self.treadmill[-self.STREAMSIZE+lostsniffsamples:], [self.treadmill[-1]]*lostsniffsamples))
                    self.treadmill = hstack((new_treadmill[-self.STREAMSIZE+num_sniffs:], stream['treadmill']-1000))
                else:
                    new_treadmill = hstack((self.treadmill[-self.STREAMSIZE+num_sniffs:], stream['treadmill']-1000))
                    self.treadmill = new_treadmill
                self.stream_plot_data.set_data("treadmill", self.treadmill)
            
            if stream['lick1'] is not None or (self._laststreamtick - self._lastlickstamp < self.STREAMSIZE) or stream['lick2'] is not None:
                [self.lick1, self.lick2] = self._process_licks(stream, ('lick1', 'lick2'), [self.lick1, self.lick2])
                # [self.lick1] = self._process_licks(stream, ('lick1',), [self.lick1])

            if "laserontime" in self.event_definition().keys():
                lasershift = int(packet_sent_time - self._laststreamtick)
                if lasershift > self.STREAMSIZE:
                    lasershift = self.STREAMSIZE
                new_laser = hstack((self.laser[-self.STREAMSIZE + lasershift:], [0] * lasershift))
                self.laser = new_laser
                self.stream_plot_data.set_data('laser', self.laser)

            self._laststreamtick = packet_sent_time
        return

    def _process_licks(self, stream, licksignals, lickarrays):

        packet_sent_time = stream['packet_sent_time']

        # TODO: find max shift first, apply it to all licks
        maxtimestamp = int(packet_sent_time)
        for i in range(len(lickarrays)):
            licksignal = licksignals[i]
            if licksignal in stream.keys():
                streamsignal = stream[licksignal]
                if streamsignal is not None and streamsignal[-1] > maxtimestamp:
                        maxtimestamp = streamsignal[-1]
                        print "**************************************************************"
                        print "WARNING! Lick timestamp exceeds timestamp of received packet: "
                        print "Packet sent timestamp: ", packet_sent_time, "Lick timestamp: ", streamsignal[-1]
                        print "**************************************************************"
        maxshift = int(packet_sent_time - self._laststreamtick)
        if maxshift > self.STREAMSIZE:
            maxshift = self.STREAMSIZE - 1

        for i in range(len(lickarrays)):

            licksignal = licksignals[i]
            lickarray = lickarrays[i]

            if licksignal in stream.keys():
                if stream[licksignal] is None:
                    lickarray = hstack((lickarray[-self.STREAMSIZE + maxshift:], [lickarray[-1]] * maxshift))
                else:
                    # print "licks: ", stream['lick'], "\tnum sniffs: ", currentshift
                    last_state = lickarray[-1]
                    last_lick_tick = self._laststreamtick
                    for lick in stream[licksignal]:
                        # print "last lick tick: ", last_lick_tick, "\tlast state: ", last_state
#                        if lick == 0:
#                            continue
                        shift = int(lick - last_lick_tick)
                        if shift <= 0:
                            if shift < self.STREAMSIZE * -1:
                                shift = -self.STREAMSIZE + 1
                            if isnan(last_state):
                                lickarray[shift - 1:] = [i + 1] * (-shift + 1)
                            else:
                                lickarray[shift - 1:] = [nan] * (-shift + 1)
                        # Lick timestamp exceeds packet sent time. Just change the signal state but don't shift
                        elif lick > packet_sent_time:
                            if isnan(last_state):
                                lickarray[-1] = i + 1
                            else:
                                lickarray[-1] = nan
                        else:
                            if shift > self.STREAMSIZE:
                                shift = self.STREAMSIZE - 1
                            lickarray = hstack((lickarray[-self.STREAMSIZE + shift:], [lickarray[-1]] * shift))
                            if isnan(last_state):
                                lickarray = hstack((lickarray[-self.STREAMSIZE + 1:], [i + 1]))
                            else:
                                lickarray = hstack((lickarray[-self.STREAMSIZE + 1:], [nan]))
                            last_lick_tick = lick
                        last_state = lickarray[-1]
                        # last timestamp of lick signal change
                        self._lastlickstamp = lick
                    lastshift = int(packet_sent_time - last_lick_tick)
                    if lastshift >= self.STREAMSIZE:
                        lastshift = self.STREAMSIZE
                        lickarray = [lickarray[-1]] * lastshift
                    elif lastshift > 0 and len(lickarray) > 0:
                        lickarray = hstack((lickarray[-self.STREAMSIZE + lastshift:], [lickarray[-1]] * lastshift))
                if len(lickarray) > 0:
                    self.stream_events_data.set_data(licksignal, lickarray)
                    # self.stream_event_plot.request_redraw()
                    lickarrays[i] = lickarray

        return lickarrays

    def _shiftlicks(self, shift):

        if shift > self.STREAMSIZE:
            shift = self.STREAMSIZE - 1

        streamdef = self.stream_definition()
        if 'lick1' in streamdef.keys():
            self.lick1 = hstack((self.lick1[-self.STREAMSIZE + shift:], self.lick1[-1] * shift))
            self.stream_events_data.set_data('lick1', self.lick1)
        if 'lick2' in streamdef.keys():
            self.lick2 = hstack((self.lick2[-self.STREAMSIZE + shift:], self.lick2[-1] * shift))
            self.stream_events_data.set_data('lick2', self.lick2)
        return
#------------------------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------------------------------
#--------------------------Initialization------------------------------------------------------------------------------------
    def __init__(self, trialNumber,
                        mouse,
                        session,
                        stamp,
                        interTrialInterval,
                        trialtype,
                        max_rewards,
                        fvdur,
                        trialdur,
                        lickgraceperiod,
                        protocol_type,
                        laseramp,
                        lasergolatency,
                        laserTrigPhase,
                        stimindex=0,
                        **kwtraits):
        super(Lick2Afc, self).__init__(**kwtraits)
        self.laser_multi_sniff = 0 # when this is set to 1, trigtrain will look for the next inhale and retrigger itself.
        self.trialNumber = trialNumber
        self.stamp = stamp
        self.config = Voyeur_utilities.parse_rig_config() #get a configuration object with the default settings.
        self.rig = self.config['rigName']
        self.waterdur = self.config['waterValveDurations']['valve_1_left']['valvedur']
        self.wateramt = self.config['waterValveDurations']['valve_1_left']['wateramt']
        self.waterdur2 = self.config['waterValveDurations']['valve_2_right']['valvedur']
        self.wateramt2 = self.config['waterValveDurations']['valve_2_right']['wateramt']
        self.olfas = self.config['olfas']
        
        self.db = 'mouse' + str(mouse) + '_' + 'sess' + str(session) \
                    + '_' + self.stamp
        
        self.mouse = mouse
        self.session = session
        self.interTrialIntervalSeconds = interTrialInterval
        self.trialtype = trialtype
        self._next_trialtype = self.trialtype
        self.fvdur = fvdur
        self.trialdur = trialdur
        self.lickgraceperiod = lickgraceperiod
        self.blocksize = self.BLOCKSIZE
        self.laser_amp = laseramp
        self.lasergolatency = lasergolatency
        self._stimindex = stimindex
        self.rewards = 0
        self.protocol_type = protocol_type
        self._protocol_type_changed()
        self.protocol_name = 'LickTrainingV1'
        self._max_rewards = max_rewards
        
        config_filename = "C:\\voyeur_rig_config\olfa_config.json"
        self.olfacto=Olfactometers(None, config_filename)
    

        #self.calculate_next_trial_parameters()

        time.clock()


        if self.ARDUINO:
            self.monitor = Monitor()
            print 'initializing monitor'
            self.monitor.protocol = self
            if self.monitor.protocol_name != self.protocol_name:
                print "WARNING, ARDUINO PROTOCOL IS NOT: " + self.protocol_name + 'PLEASE UPLOAD CORRECT SKETCH BEFORE STARTING'
            
        return
    


    def _restart(self):

        self.trialNumber = 1
        self.rewards = 0

        self._righttrials = [1]
        self._lefttrials = [1]
        self.tick = [0]
        self.result = [0]
        # self.iteration = [0]
        # self.lick1 = [0]
        self._slwleftvals = []
        self._slwrightvals = []
        self._falselefts = 0
        self._falserights = 0
        self._corrights = 0
        self._corlefts = 0
        self._cortotal = 0
        self._totalRightTrials = 0
        self._totalLeftTrials = 0
        self._nomoves = 0
        self._bilicks = 0
        self._slwcrr = 0
        self._slwcrl = 0
        self._sameSideResponses = 0
        self._opposite_SideResponses = 0
        self._leftResponses = 0
        self._rightResponses = 0
        self._protocol_type_changed()
        self.calculate_next_trial_parameters()
        self._windowResults = []

        time.clock()

        return

#UPDATE TIMER    
    def timer_update_task(self):
        
        if self.elapsed_time_sec >= 59:
            self.elapsed_time_min += 1
            self.elapsed_time_sec = 0
        else:
            self.elapsed_time_sec += 1
        self.trial_time += 1


#--------BEHAVIORAL TASK--------BEHAVIORAL TASK--------BEHAVIORAL TASK--------BEHAVIORAL TASK--------BEHAVIORAL TASK--------
#This section.....    

#START TRIAL FUNCTION   
    def start_of_trial(self):

        self.timestamp("start")
        print "*************************","\n Trial: ", self.trialNumber, 
    
    
    def calculate_next_trial_parameters(self):

        if self.protocol_type == 'Blocks':
            if not hasattr(self, 'block_count'):
                self.block_count = 0;
            self.block_count += 1
            if self.block_count > self.blocksize:
                self.block_count = 0
                if self.trialtype == 'Left':
                    self._next_trialtype = 'Right'
                    
                else:
                    self._next_trialtype = 'Left'
        
        elif self.protocol_type == 'Alternate':
            if self.trialtype == 'Right':
                self._next_trialtype = 'Left'
            else:
                self._next_trialtype = 'Right'
                


        return

#UPDATE PYTHON VARIABLES AFTER EACH PROCESS EVENT
    def _result_changed(self):
#Results [ 1-correct right; 2-correct left; 3-False Alarm left; 4- false alarm right; 5 - no response; 7- RightorLeft Correct]

        if len(self.result) == 1:
            return

        self.tick = arange(0, len(self.result))
        lastelement = self.result[-1]
        
     #Calculates whether the animal has finished 1000 trials
        if self.three_missed == False:    
             if self.trialNumber > 1000:
                 self.three_missed = True
                 self.monitor.send_command("threemissed on");
        
        if(lastelement == 1):  # Left (LC1) correct
            self._corlefts += 1
            self._totalLeftTrials +=1
            self._cortotal +=1
            self._missedGo = 0
            self.left_performance = (self._corlefts * 100) / self._totalLeftTrials

        elif(lastelement == 2):  # Right (LC2) Correct
            self._corrights += 1
            self._cortotal +=1
            self._totalRightTrials +=1
            self._missedGo = 0
            self.right_performance = (self._corrights * 100) / self._totalRightTrials

        elif (lastelement == 3): #Wrong right (suppose to lick left)
            self._falserights += 1
            self._totalLeftTrials +=1
            self._missedGo = 0
            self.left_performance = (self._corlefts * 100) / self._totalLeftTrials
        
        elif (lastelement == 4): # Wrong left (supposed to lick right)
            self._falselefts += 1
            self._totalRightTrials +=1
            self._missedGo = 0
            self.right_performance = (self._corrights * 100) / self._totalRightTrials
            
        elif (lastelement == 5): #No response
            self._nomoves +=1
            self._missedGo +=1
            if self.trialtype == 'Left': 
                self._totalLeftTrials +=1
                self.left_performance = (self._corlefts * 100) / self._totalLeftTrials                
            elif self.trialtype == 'Right':
                self._totalRightTrials +=1
                self.right_performance = (self._corrights * 100) / self._totalRightTrials
        
        self.total_performance = (self._cortotal * 100) / self.trialNumber 
        self.nolick_performance = (self._nomoves * 100) / self.trialNumber 
        self.trialNumber +=1  
 
#Print out mouse's performance       
        print "\nResult: " + str(lastelement) + "\tCorrect Rights: " + str(self._corrights) + \
              "\tCorrrect Lefts: " + str(self._corlefts) + "\tFalse Rights: " + str(self._falserights) + \
              "\tFalse Lefts: " + str(self._falselefts) + "\tNo Licks: " + str(self._nomoves) 


    def trial_iti_milliseconds(self):
        return 0

    def timestamp(self, when):
        """ Used to timestamp events """
        if(when == "start"):
            self._paramsenttime = time.clock()
            # print "start timestamp ", self._paramsenttime
        elif(when == "end"):
            self._resultstime = time.clock()
            
            
    def end_of_trial(self):

        self.trialNumber +=1 
        self.total_performance = (self._cortotal * 100) / self.trialNumber 
        self.nolick_performance = (self._nomoves * 100) / self.trialNumber 
        
        if self.trialtype == 'Left':
            self._totalLeftTrials +=1
            self.left_performance = (self._corlefts * 100) / self._totalLeftTrials 
        else:
            self._totalRightTrials +=1
            self.right_performance = (self._corrights * 100) / self._totalRightTrials
        
        self.total_water = (self._corlefts * self.wateramt) + (self._corrights * self.wateramt2)
        self.trialtype = self._next_trialtype
        self.calculate_next_trial_parameters()
        self.trial_time = 0
#--------------------------------------------------------------------------------------------------------------------




if __name__ == '__main__':

    # arduino parameter defaults


    trialNumber = 1
    trialtype = "Left"
    fvdur = 1
    trialdur = 2000
    lickgraceperiod = 0
    stimindex = 0
    laseramp = 1500
    lasergolatency = 100
    laserTrigPhase = "Inhalation"
    protocol_type = "Please Select"  # "LaserTraining"
    max_rewards = 4000


    # protocol parameter defaults
    mouse = 1  # can I make this an illegal value so that it forces me to change it????

    session = 1
    stamp = time_stamp()
    interTrialInterval = 2
    stimindex = 0

    # protocol
    protocol = Lick2Afc(trialNumber,
                    mouse,
                    session,
                    stamp,
                    interTrialInterval,
                    trialtype,
                    max_rewards,
                    fvdur,
                    trialdur,
                    lickgraceperiod,
                    protocol_type,
                    laseramp,
                    lasergolatency,
                    laserTrigPhase,
                    stimindex,
                    )

    # GUI
    protocol.configure_traits()



