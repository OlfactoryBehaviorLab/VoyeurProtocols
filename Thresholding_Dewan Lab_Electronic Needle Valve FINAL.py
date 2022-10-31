'''
Modified 2/2019
Dewan Lab

'''


import voyeur.db as db
import random
import olfactometry
#from olfactometer_arduino import Olfactometers
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
from pyface.timer.api import Timer, do_after, do_later
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
from OlfactometerUtilities.Voyeur_utilities import save_data_file, parse_rig_config, find_odor_vial
from myEmail import sendEmail
from PyQt4.QtCore import QThread, QTimer

from OlfactometerUtilities.Stimulus import LaserStimulus, LaserTrainStimulus  # OdorStimulus
from OlfactometerUtilities.range_selections_overlay import RangeSelectionsOverlay
from OlfactometerUtilities import Voyeur_utilities


#-------------------------------------------------------------------------------
class Thresholding(Protocol):
    """Protocol for Go-NoGo task on a lick-based choice"""

    STREAMSIZE = 20000
    BLOCKSIZE = 24

    SLIDINGWINDOW = 10
    VALVETIMEDELAY = 1500  # amount of time in milliseconds for odor valve to stay on before trial start
    ADAPTINGODORDELAY = 3000
    NITROGEN_1 = 100
    MAXTRIALDURATION = 500  # Maximum trial duration to wait for in seconds
    ARDUINO = 1
    MAXCLEANTIME = 2000
    MAXSNIFFCLEANRUNS = 20
    INITIALGOTRIALS = 10
    nitrogen = 100
    air = 900
    EOTairpressure = 0.0
    EOTnitrogenpressure = 0.0
    baselineairpressure = 0.0
    baselinenitrogenpressure = 0.0
    outofrange = 0.0

    
    sniff_scale = 1 #Tang added
    flows=(air,nitrogen)
    
#-----------------------------------------------------------------------------
        #PRESSURE DATA TO MATCH VIALS
        #positive numbers = opening and negative numbers are closing
#    pressure_target = 16.74 
#    vialpressureopen = [127, 68, 25, 0, 74, 25, 0] 
#    vialpressureclose =  [-145, -90, -61, 0, -117, -56, 0]
#    vialpressurefluctuationhigh = [-100, -40, -20, 0, -70, -30, -10]
 #   vialpressurefluctuationlow = [0, 75, 90, 50, 0, 50, 60]
    
    pressure_target = 16.55
    #number of steps for each vial to match vial 8 N
    vialpressureopen = [90, 70, 25, 0, 22, 16, 0] 
    #number of steps for each vial to return from matched vial 8 N to original vial pressure
    vialpressureclose =  [-140, -118, -70, 0, -82, -73, 0]
    #number of steps for each vial to match the highest and lowest AIR pressure
    vialpressurefluctuationhigh = [0, 0, 0, 0, 0, 0, 0]
    vialpressurefluctuationlow = [0, 0, 0, 0, 0, 0, 0]

    pressuredifference = 0
    driftstep = 0
    driftup = [0, 2, 5, 7, 9, 12, 13, 14, 16, 18, 20, 22, 24, 26, 28, 30, 31, 33, 35, 36, 39, 40, 42, 44, 45, 47, 48, 50, 52, 53, 55, 57, 58, 59, 60, 62, 63, 64, 66, 67, 69, 71, 72, 73, 74, 75, 77, 79, 81, 82, 83, 84, 86, 87, 88, 90, 91, 92, 94, 95, 96, 97, 98, 100, 101, 102, 103, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 120, 121, 122, 123]
    #[0, 4, 6, 8, 10, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35, 38, 40, 41, 43, 45, 47, 49, 51, 52, 53, 56, 57, 58, 59, 60, 61, 63, 65, 66, 68, 69, 70, 74, 75, 76, 77] #Pressure is above target
    driftdown = [0, -2, -5, -7, -10, -12, -14, -17, -19, -22, -24, -26, -28, -33, -34, -36, -37, -40, -42, -46, -49, -51, -55, -58, -62, -67, -69, -74, -78, -81, -85, -88, -92, -102, -105, -110, -114, -120, -125, -127, -132, -137, -146, -150, -152, -158, -162, -169, -175, -180, -185, -188, -195, -203, -206, -214, -218, -225, -228, -234, -242, -245]
    #[0, -4, -6, -8, -11, -14, -16, -19, -23, -26, -29, -33, -36, -39, -43, -47, -50, -54, -57, -61, -65, -67, -72, -76, -80, -83, -87, -92, -96, -102, -107, -110, -114, -120, -126, -132, -137, -143, -148, -157, -165, -169, -172] #pressure is below target
     
    homestepsize = 5
#-----------------------------------------------------------------------------
    # protocol parameters (session parameters for Voyeur)
    mouse = Int(0, label='mouse') #Default is in 
    rig = Str("", label='rig') 
    stamp = Str(label='stamp')
    session = Int(0, label='session')
    protocol_name = Str(label='protocol')
    rewards = Int(0, label="Total rewards")
    response_type ='lick'
    protocol_type = Enum('Please Select',
                         'Stage 2 Training',
                         'Thresholding',
                         )
#    trial_structure = Enum("Blocks", "Random", "deBias")  
#    blocksize = Int(10, label="Block size")
    trialNumber = Int(1, label='Trial')
    ENVdirection = Int(-1, label='ENV direction') #-1 = closing and +1 = opening
    MaxtrialNumber = Int(300, label='Max # of Trials')
    InitialGoNumber = Int(10, label='Initial Go Trial')
    trialtype = Enum(("InitialGo", "Go", "NoGo"), label="Trial type")
    waterdur = Int(0, label="Water valve 1 duration")
    waterdur2 = Int(0, label="Water valve 2 duration")
    step_num = Int(0, label="# of steps")
    wateramt = Float(0, label="Water valve 1 amount")
    odorvial = Int(0, label="Odor Vial #")
    fvdur = Int(0, label="Final valve duration")
    trialdur = Int(0, label="Trial duration")
    step_num = Int(10, label="steps")
    datarangehigh = Int(2000, label="Data Range High")    #CHANGE SNIFFING Y AXIS VALUES!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!  
    datarangelow = Int(0, label="Data Range Low")
    interTrialIntervalSeconds = Int(0, label='ITI seconds')
    lickgraceperiod = Int(0, label="Lick grace period")
    sniffmaxdelay = Int(1200, label="Sniff max delay")  # delay for sniff Trigger change
    lasergolatency = Int(0, label="Laser Go Latency")
    fvTrigPhase = Enum("Exhalation onset", "During exhalation", label="FV triggered phase")
    fvTrigPhaseVal = Int(1, label="FV triggered phase")
    laserTrigPhase = Enum("Inhalation", "Exhalation", label="Laser triggered sniff phase")
    laserTrigPhaseVal = Int(0, label="Laser triggered sniff phase")
    itiBounds  = [5000,7000] # (ms) upper and lower bounds for random iti when animal correct response
    itiBoundsFA = [10000,15000] #(ms) upper and lower bounds for random iti when animal DID false alarm
    GoVials=[]
    NoGoVials=[]
    CheatingVial=[]
    InitialGoVial=[]
    InitialNoGoVial=[]
    vialnum = ['5','6','7','8','9','10','11']
    

    
    # other trial parameters
    odorconc = Float(0, label="Odor concentration")
    odor = Str("Current odor", label='Odor')

    # ==== trial-by-trial event variables ===
    # some may be directly duplicated from event variables sent by controller, to be manipulated
    tick = Array
    result = Array
    trialstart = Int(0, label="Trial start time stamp")
    trialend = Int(0, label="Trial end time stamp")
    firstlick = Int(0, label="Time of first lick")
    firstrewardlick = Int(0, label="Time of first reward lick")
    paramsgottime = Int(0, label="Time parameters received time stamp")
    no_sniff = Bool(False, label="Lost sniffing in last trial")
    fvOnTime = Int(0, label="Time of final valve open")
    three_missed = Bool(False, label="Missed three trials in a row")
    total_performance = Float(100.0, label="Total Performance")
    go_performance = Float(100.0, label="Go Trial Performance")
    nogo_performance = Float(100.0, label="NoGo Trial Performance")
    final_performance = Float(0.0, label="Final Performance")
    finalgo_performance = Float(0.0, label="Final Go Performance")
    finalnogo_performance = Float(0.0, label="Final NoGo Performance")
    cheating_performance = Float(0.0, label="Cheating %")
    total_water = Float(0.0, label="Total Water (ul)")
    
    # Timers
    elapsed_time_sec = Int(0, label = 'sec:')
    elapsed_time_min = Int(0, label = 'Time since session start - min:')
    trial_time = Int(0, label = 'Time since last response (sec)')

    # streaming data
    iteration = Array
    sniff = Array
    treadmill = Array
    lick1 = Array
    lick2 = Array
    laser = Array


    # internal (recalculated for each trial)
    _mask_timing = 'normal'
#    _olfactometer = Instance(Olfactometer) #olfactometry.olfactometer.Olfactometer
    _next_trialNumber = Int(0, label='trialNumber')
    _next_trialtype = Enum(("InitialGo", "Go", "NoGo"), label="Trial type")
    _last_trialtype = Enum(("InitialGo", "Go", "NoGo"), label="Last trial type")
    _next_odorvial = 0
    _equalBlock = True
    _next_odorconc = Float(0, label="Odor concentration")
    _next_odor = Str("Next odor", label="Odor")  # addition of odor concentration
    _next_trial_start = 0
    _wv = Str('1')
    _corGos = 0
    _corNoGos = 0
    _cortotal = 0
    _falseAlarm = 0
    _cheating = 0
    _totalGoTrials = 0
    _totalNoGoTrials = 0
    _totalCheatingTrials = 0
    _nomoves = 0
    _next_odorconc = Float(0)
    _max_rewards = 0
    _paramsenttime = float()
    _resultstime = float()
    _laststreamtick = Float(0)
    _lastlickstamp = 0
    _previousendtick = 0
    _inblockcorrect = 0
    _stimindex = int(0)
    _missedGo = 0

    _unsyncedtrials = 0
    _first_trial_block = []  # deBias
    _leftstimblock = []
    _rightstimblock = []
    pressuretimerObj = Instance(QTimer)
    hometimerObj = Instance(QTimer)
    
    #-----------------------------------------------------------
    #Change to send email
    email = Int(0, label="1 = email / 0 = no email")
    trialmax = Int(0, label="1 = trial stop / 0 = no stop")
    receiver_email = Str ("", label = 'email')
    

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # GUI
    monitor = Instance(object)
    event_plot = Instance(Plot, label="Success Rate")
    stream_plots = Instance(Component)
    stream_plot = Instance(Plot, label="Sniff") #ADD BACK IF YOU WANT SNIFF TO BE PLOTTED
    stream_event_plot = Instance(Plot, label="Events")
    start_button = Button()
    cal_olfa_button = Button()
    start_label = Str('Start')
    cal_olfa_label = Str('Cal Olfa (OFF)')
    pause_button = Button()
    pause_label = Str('Pause')
    save_as_button = Button("Save as")
    olfactory_button = Button()
    olfactory_label = Str('Olfactometer')
    fv_button = Button("Final Valve")
    fv_label = Str("Final Valve (OFF)")
    env_button = Button("HOME")
    env_label = Str("HOME ENV")
    step_button = Button("step")
    step_label = Str("Step")
    fv2_button = Button("Final Valve 2")
    fv2_label = Str("Final Valve 2 (OFF)")
    cal_button1 = Button("Cal Water 1")
    water_button1 = Button(label="Water Valve 1")
    clean_button = Button("Clean Valve")
    clean_label = Str("Clean (OFF)")


    session_group = Group(
                        Item('mouse', enabled_when='not monitor.running'),
                        Item('session', enabled_when='not monitor.running'),
                        Item('stamp', style='readonly'),
                        Item('protocol_name', style='readonly'), #Just the word protocol
                        Item('protocol_type', enabled_when='not monitor.running'), #stage 2 training or thresholding
#                        Item('trial_structure', enabled_when='not monitor.running'),
#                                spring,
#                                Item('blocksize', visible_when='trial_structure == "Blocks"',
#                                      width=-100, tooltip="Block Size", show_label=False, full_size=False, springy=False, resizable=False)),
             
                        Item('rig', enabled_when='not monitor.running'),
                        Item('rewards', style='readonly'),
                        HGroup(Item('elapsed_time_min',style='readonly'),Item('elapsed_time_sec',style = 'readonly'),show_border = False),
                      
                        #Changed to missed trials in a row
                        Item('three_missed',style = 'readonly'),
                                       
                        label='Session',
                        show_border=True
                    )


    arduino = VGroup(
        HGroup(
            VGroup(Item('fv_button',
                 editor=ButtonEditor(
                     style="button", label_value='fv_label'),
                 show_label=False),
                    Item('env_button',
                                    editor=ButtonEditor(label_value='env_label'),
                                    show_label=False,
                                    enabled_when='not monitor.running'),
                         ),
            VGroup(Item('ENVdirection'),
                    HGroup(Item('step_button',
                         editor=ButtonEditor(style="button"),
                         show_label=False),
                         Item('step_num', enabled_when='not monitor.recording'),
                         ),
                    ),
                         
            VGroup(    Item('water_button1',
                         editor=ButtonEditor(style="button"),
                         show_label=False),
                    Item('cal_button1',
                         editor=ButtonEditor(style="button"),
                         show_label=False),
                    ),
            VGroup(Item('waterdur', enabled_when='not monitor.recording'),
                   Item('wateramt', enabled_when='not monitor.recording'),
            )
                   
        ),

        label="Arduino Control",
        show_border=True
    )

    control = VGroup(
                    HGroup(
                            Item('start_button',
                                    editor=ButtonEditor(label_value='start_label'),
                                    show_label=False),
                            Item('pause_button',
                                    editor=ButtonEditor(label_value='pause_label'),
                                    show_label=False,
                                    enabled_when='monitor.running'),
                            Item('olfactory_button',
                                    editor=ButtonEditor(label_value='olfactory_label'),
                                    show_label=False),
                            show_border=False
                            ),
                    label='Control',
                    show_border=True,
                    )

    current = Group(
                        Item('trialNumber', style='readonly'),
                        Item('InitialGoNumber'),
                        Item('interTrialIntervalSeconds'),
                        Item('trialtype'),
                        Item('trialdur'),
                        Item('odor'),
                        Item('odorconc'),
                        Item('total_performance',style = 'readonly'),
                        Item('go_performance',style = 'readonly'),
                        Item('nogo_performance',style = 'readonly'),
                        Item('cheating_performance',style = 'readonly'),
                        label='Current Trial',
                        show_border=True
                    )

    next = Group(
                    Item('_next_trialtype'),
                    Item('_next_odor'),
                    Item('_next_odorconc'),  # addition
                    Item('final_performance',style = 'readonly'),
                    Item('finalgo_performance',style = 'readonly'),
                    Item('finalnogo_performance',style = 'readonly'),
                    Item ('total_water',style = 'readonly'),
                    Item('trialmax'),
                    Item('MaxtrialNumber'),  # addition       
                    Item('email'),
                    Item('receiver_email'),  # addition                    
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
                    title='Dewan Lab Go-NoGo Thresholding',
                    width=730,
                    height=700,
                    x=10,
                    y=30,
                    resizable=True
                )
                            
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#PLOTS EVENT DATA
    def _stream_event_plot_default(self):
        pass

#PLOTS SNIFF AND LICK DATA WITH BLUE TRIAL MASK
    def _stream_plots_default(self):

        container = VPlotContainer(bgcolor="green", fill_padding=False, padding=0)
        self.stream_plot_data = ArrayPlotData(iteration=self.iteration, sniff=self.sniff,laser=self.laser)
        y_range = DataRange1D(low=self.datarangelow, high=self.datarangehigh) # CHANGE FOR SNIFFING AMPLIFICATION
        plot = Plot(self.stream_plot_data, padding=25, padding_top=0, padding_left=60)
        plot.fixed_preferred_size = (100, 100)
        plot.value_range = y_range
        y_axis = plot.y_axis
        y_axis.title = "Sniff (mV)"
        range_in_sec = self.STREAMSIZE / 1000.0
        self.iteration = arange(0.001, range_in_sec + 0.001, 0.001)
        self.sniff = [nan] * len(self.iteration)
        plot.plot(('iteration', 'sniff'), type='line', color='black', name="Sniff")
        self.stream_plot_data.set_data("iteration", self.iteration)
        self.stream_plot_data.set_data("sniff", self.sniff)
        print 'len iteration = ', len(self.iteration)
        print 'len sniff = ', len(self.sniff)
        bottom_axis = PlotAxis(plot, orientation="bottom", tick_generator=ScalesTickGenerator(scale=TimeScale(seconds=1)))
        plot.x_axis = bottom_axis
        plot.x_axis.title = "Time"
        self.stream_plot = plot
        laser_plot = plot.plot(("iteration", "laser"), name="Laser", color="blue", line_width=2)[0]
        plot.legend.visible = True
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
        plot.fixed_preferred_size = (100, 50)
        y_range = DataRange1D(low=0, high=3)
        plot.value_range = y_range
        plot.x_axis.orientation = "top"
        plot.x_axis.title = "Events"
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

    def _restart(self):

        self.trialNumber = 1
        self.rewards = 0

        self._righttrials = [1]
        self._lefttrials = [1]
        self.tick = [0]
        self.result = [0]
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

    def _mouse_changed(self):
        new_stamp = time_stamp()
        db = 'mouse' + str(self.mouse) + '_' + 'sess' + str(self.session) \
                    + '_' + new_stamp
        if self.db != db:
            self.db = db
        return

    def _fvTrigPhase_changed(self):
        if self.fvTrigPhase == "Exhalation onset":
            self.fvTrigPhaseVal = 1
        elif self.fvTrigPhase == "During exhalation":
            self.fvTrigPhaseVal = 0
        return

    def _protocol_type_changed(self):
        
        if self.protocol_type == 'Stage 2 Training':
            
            self.lickgraceperiod = 600 # grace period after inh onset where responses are recorded but not scored.
            self.itiBounds = [8000,10000] # ITI in ms for all responses other than FA.
            self.itiBoundsFA = [12000,15000] #ITI in ms for false alarm responses (punishment).
      
        if self.protocol_type == 'Thresholding':
            self.lickgraceperiod = 600 # grace period after inh onset where responses are recorded but not scored.
            self.itiBounds = [8000,10000] # ITI in ms for all responses other than FA.
            self.itiBoundsFA = [12000,15000] #ITI in ms for false alarm responses (punishment).
        
               
        self.interTrialIntervalSeconds = 5
#        self.stimuli['Go'].append(GoStim)
#        self.stimuli['NoGo'].append(NoGoStim)
        self.fvdur = 0

        return

    def _session_changed(self):
        new_stamp = time_stamp()
        self.db = 'mouse' + str(self.mouse) + '_' + 'sess' + str(self.session) \
            + '_' + new_stamp


    def _result_changed(self):
        #Results [ 1-correct Go; 2-correct NoGo; 3-False Alarm left; 5- no response]
        if len(self.result) == 1:
            return
        lastelement = self.result[-1]
        
 #Calculates whether the animal missed  (did not lick) three trials in a row   
        if self.three_missed == False:
            if self._missedGo == 3:
                self.three_missed = True
                self.monitor.send_command("threemissed on");
                self.final_performance = (self._cortotal * 100) / (self.trialNumber-1)
                self.finalgo_performance = (self._corGos * 100) / self._totalGoTrials
                if self.email == 1:
                    emailSubject = "Check on Mouse {}".format(self.mouse)
                    sendEmail(self.receiver_email, emailSubject)
               
                if self.trialmax == 1:
                    self.monitor.pause_acquisition()
                    
                if self._totalNoGoTrials > 1:
                    self.finalnogo_performance = (self._corNoGos * 100) / self._totalNoGoTrials
#                    self.monitor.pause_acquisition()
#                    self.pause_label = 'Unpause'
#                    print "REACHED END "
        
 #Checks the results and updates mouse's performance
        if(lastelement == 1):  # Correct response
            self._corGos += 1
            self._cortotal +=1
            self._totalGoTrials +=1
            self._missedGo = 0
            self.go_performance = (self._corGos * 100) / self._totalGoTrials
            
        elif(lastelement == 2):  # Left (LC1) Correct
            self._corNoGos += 1
            self._cortotal +=1
            self._totalNoGoTrials +=1
            self.nogo_performance = (self._corNoGos * 100) / self._totalNoGoTrials
            if self._lastvial == 1:
                self._cheating +=1
                self._totalCheatingTrials +=1
                self.cheating_performance = (self._cheating * 100) / self._totalCheatingTrials 

        elif (lastelement == 3): 
            self._falseAlarm += 1
            self._totalNoGoTrials +=1
            self._missedGo = 0
            self.nogo_performance = (self._corNoGos * 100) / self._totalNoGoTrials
            if self._lastvial == 1:
                self._totalCheatingTrials +=1
                self.cheating_performance = (self._cheating * 100) / self._totalCheatingTrials 
            
        elif (lastelement == 5): 
            self._nomoves +=1 
            self._totalGoTrials +=1
            self._missedGo +=1
            self.go_performance = (self._corGos * 100) / self._totalGoTrials

            
        self.trialNumber +=1 
        self.total_performance = (self._cortotal * 100) / (self.trialNumber-1)
        self.total_water = (self._corGos * self.wateramt)
        self._lastvial = 0 #vials are updated before results so quick fix to determine if last vial was a cheating check


 
#Print out mouse's performance       
        print "\nResult: " + str(lastelement) + "\tCorrect Gos: " + str(self._corGos) + \
              "\tCorrrect NoGos: " + str(self._corNoGos) + "\tFalse Alarms: " + str(self._falseAlarm) + \
              "\tNo Licks: " + str(self._nomoves) + "\tWATER (ul): " + str(self.total_water) 
#-------------------------END OF _RESULT_CHANGED FUNCTION-------------------------------------------------------------------

    def _callibrate(self):
        if self.start_label == "Start" and  self.cal_olfa_label == "Cal Olfa (ON)":
            do_after(2500, self._callibrate)

        self._fv_button_fired()

        return

#---------------------------------------------------------------------------------------------------------------------------
#--------------------------Button events------------------------------------------------------------------------------------
    def _start_button_fired(self):
        if self.monitor.running:
            self.start_label = 'Start'
            
            if self.fv_label == "Final Valve (ON)":
                self._fv_button_fired()
            self.session_timer.Stop()
            self.monitor.stop_acquisition()
            print "Unsynced trials: ", self._unsyncedtrials
            self.session += 1
        else:
            # self.session = self.session + 1
            if self.protocol_type == 'Please Select':
                print 'ERROR: Please select a protocol type to begin.'
                return
            if self.monitor.protocol_name != self.protocol_name:
                print "WARNING, ARDUINO PROTOCOL IS NOT: " + self.protocol_name
                print 'Please exit and upload correct sketch to arduino before starting.'
                return
            self.start_label = 'Stop'
            self._restart()
            # self._callibrate()
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
    
    def timer_update_task(self):
        
        if self.elapsed_time_sec >= 59:
            self.elapsed_time_min += 1
            self.elapsed_time_sec = 0
        else:
            self.elapsed_time_sec += 1
        self.trial_time += 1


    def _pause_button_fired(self):
        if self.monitor.recording:
            self.monitor.pause_acquisition()
            self.pause_label = 'Unpause'
        else:
            self.pause_label = 'Pause'
            self.trialNumber += 1
            self.monitor.unpause_acquisition()
        return

    def _save_as_button_fired(self):
        dialog = FileDialog(action="save as")
        dialog.open()
        if dialog.return_code == OK:
            self.db = os.path.join(dialog.directory, dialog.filename)
        return
    
    def _waterdur_changed(self):
        self.save_water_params()
        return
    
    def _waterdur2_changed(self):
        self.save_water_params()
        return
    
    def save_water_params(self):
        
        configuration_obj = ConfigObj(self.config['configFilename'])
        
        if not hasattr(self, 'water_volume'):
            self.water_volume = 0.25
        water_vol_str = str(self.water_volume)+'ul'
        
        configuration_obj['rig_params']['water_durations']['valve_1_left'][water_vol_str] = self.waterdur
        configuration_obj['rig_params']['water_durations']['valve_2_right'][water_vol_str] = self.waterdur2
        configuration_obj.write()
                
        return

 
    def _step_button_fired(self):
        if self.monitor.recording:
            self._pause_button_fired()
        if self.ENVdirection == 1:
             self.monitor.send_command("ENV open")
             command = "step " + str(self.step_num)
             self.monitor.send_command(command)
        if self.ENVdirection == -1:
             self.monitor.send_command("ENV close")
             command = "step " + str(self.step_num)
             self.monitor.send_command(command) 
        return
    
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
    
    def _env_button_fired(self):
        print "home button"
        self.baselineairpressure = self.olfacto.olfas[0].mfcs[0].pressure
        self.baselinenitrogenpressure = self.olfacto.olfas[0].mfcs[1].pressure
        self.driftdifference = (self.baselinenitrogenpressure - self.pressure_target)*100
        print "driftdifference", self.driftdifference

        
        if self.driftdifference == 0:
            command = "close_step " + str(self.homestepsize)
            self.monitor.send_command(command)
            self.ENVdirection = -1
        
            if self.hometimerObj:
                self.hometimerObj.stop()
                self.hometimerObj.deleteLater()
            self.hometimerObj = QTimer()
            self.hometimerObj.timeout.connect(self.HomeZero)
            self.hometimerObj.setSingleShot(False)
            self.hometimerObj.start(3000)
        
        if self.driftdifference > 0:
            command = "open_step " + str(self.homestepsize)
            self.monitor.send_command(command)
            self.ENVdirection = 1
        
            if self.hometimerObj:
                self.hometimerObj.stop()
                self.hometimerObj.deleteLater()
            self.hometimerObj = QTimer()
            self.hometimerObj.timeout.connect(self.HomePositive)
            self.hometimerObj.setSingleShot(False)
            self.hometimerObj.start(3000)
        
    
        if self.driftdifference < 0:
            print "drift negative"
            command = "close_step " + str(self.homestepsize)
            self.monitor.send_command(command)
            self.ENVdirection = -1
        
            if self.hometimerObj:
                self.hometimerObj.stop()
                self.hometimerObj.deleteLater()
            self.hometimerObj = QTimer()
            self.hometimerObj.timeout.connect(self.HomeNegative)
            self.hometimerObj.setSingleShot(False)
            self.hometimerObj.start(3000)
        
    
    def HomeZero(self):
            print "in HomeZero"
            self.baselineairpressure = self.olfacto.olfas[0].mfcs[0].pressure
            self.baselinenitrogenpressure = self.olfacto.olfas[0].mfcs[1].pressure
            self.driftdifference = (self.baselinenitrogenpressure - self.pressure_target)*100
            self.driftdifference = round(self.driftdifference,1)
            self.driftdifference = int(self.driftdifference)
            
            if self.driftdifference == 0:
                print "driftdifference = 0 in HomeZero"
                self.ENVdirection = -1
                command = "close_step " + str(self.homestepsize)
                self.monitor.send_command(command)
            else:
                print "driftdifference NOT 0 in HomeZero, kill hometimer"
                self.hometimerObj.stop()
                #self.hometimerObj.deleteLater()
            
    def HomePositive(self):
            print "in Homepositive"
            self.baselineairpressure = self.olfacto.olfas[0].mfcs[0].pressure
            self.baselinenitrogenpressure = self.olfacto.olfas[0].mfcs[1].pressure
            self.driftdifference = (self.baselinenitrogenpressure - self.pressure_target)*100
            self.driftdifference = round(self.driftdifference,1)
            self.driftdifference = int(self.driftdifference)
            
            if self.driftdifference > 0:
                print "driftdifference = 0 in Homepositive"
                self.ENVdirection = 1
                command = "open_step " + str(self.homestepsize)
                self.monitor.send_command(command)
            else:
                print "driftdifference NOT 0 in Homepostive, kill hometimer"
                self.hometimerObj.stop()
                if self.outofrange == 1:
                    self.pause_label = 'Pause'
                    self.trialNumber += 1
                    self.outofrange = 0
                    self.monitor.unpause_acquisition()
                    
                #self.hometimerObj.deleteLater()
                
    def HomeNegative(self):
            print "in Homenegative"
            self.baselineairpressure = self.olfacto.olfas[0].mfcs[0].pressure
            self.baselinenitrogenpressure = self.olfacto.olfas[0].mfcs[1].pressure
            self.driftdifference = (self.baselinenitrogenpressure - self.pressure_target)*100
            self.driftdifference = round(self.driftdifference,1)
            self.driftdifference = int(self.driftdifference)
            
            if self.driftdifference < 0:
                print "driftdifference = 0 in Homenegative"
                self.ENVdirection = -1
                command = "close_step " + str(self.homestepsize)
                self.monitor.send_command(command)
            else:
                print "driftdifference NOT 0 in Homenegative, kill hometimer"
                self.hometimerObj.stop()
                if self.outofrange == 1:
                    self.pause_label = 'Pause'
                    self.trialNumber += 1
                    self.outofrange = 0
                    self.monitor.unpause_acquisition()
                #self.hometimerObj.deleteLater()
            
        
    def _olfactory_button_fired(self):
        self.olfacto.show()
        if (self.olfacto is not None):
            self.olfacto.show()
        return
    
    def _water_button1_fired(self):
        command = "wv 1 " + str(self.waterdur)
        self.monitor.send_command(command)
        return

    def _water_button2_fired(self):
        command = "wv 2 " + str(self.waterdur2)
        self.monitor.send_command(command)
        return


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

    def _clean_button_fired(self):
#         if self.monitor.recording:
#             self._pause_button_fired()
        if self.clean_label == "Clean (OFF)":
            self.monitor.send_command("clean on")
            self.clean_label = "Clean (ON)"
        elif self.clean_label == "Clean (ON)":
            self.monitor.send_command("clean off")
            self.clean_label = "Clean (OFF)"
        return
    
    def _laser_button_fired(self, new):
        laser = self.laser_select
        command = laser + " trigger " + \
            str(self.laser_amp) + " " + str(self.laser_dur)
        self.monitor.send_command(command)
        # self._protocol_type_changed()
        return


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
        super(Thresholding, self).__init__(**kwtraits)
        self.laser_multi_sniff = 0 # when this is set to 1, trigtrain will look for the next inhale and retrigger itself.
        self.trialNumber = trialNumber
        self.stamp = stamp
        self.config = Voyeur_utilities.parse_rig_config() #get a configuration object with the default settings.
        self.rig = self.config['rigName']
        self.waterdur = self.config['waterValveDurations']['valve_1_left']['valvedur']
        self.wateramt = self.config['waterValveDurations']['valve_1_left']['wateramt']
        
               
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
        self.protocol_name = 'ThresholdingENV'
        self._max_rewards = max_rewards

        config_filename = "C:\\voyeur_rig_config\olfa_config.json"
        self.olfacto=Olfactometers(None, config_filename)
        self.olfacto.olfas[0].set_flows(self.flows)
               
# parses the olfactometer dictionary into different arrays corresonding to the correct vial locations
        for i in self.vialnum:
            if self.olfacto.olfa_specs[0]['Vials'][i]['type'] == 'GO' or self.olfacto.olfa_specs[0]['Vials'][i]['type'] == 'Go' or self.olfacto.olfa_specs[0]['Vials'][i]['type'] == 'go':
                self.GoVials.append(int(i))
                if self.olfacto.olfa_specs[0]['Vials'][i]['initial'] == 'GO' or self.olfacto.olfa_specs[0]['Vials'][i]['initial'] == 'Go' or self.olfacto.olfa_specs[0]['Vials'][i]['initial'] == 'go':
                    self.InitialGoVial.append(int(i))
            if self.olfacto.olfa_specs[0]['Vials'][i]['type'] == 'NOGO' or self.olfacto.olfa_specs[0]['Vials'][i]['type'] == 'NoGo' or self.olfacto.olfa_specs[0]['Vials'][i]['type'] == 'nogo':
                self.NoGoVials.append(int(i))
                if self.olfacto.olfa_specs[0]['Vials'][i]['odor'] == 'BLANK'or self.olfacto.olfa_specs[0]['Vials'][i]['odor'] == 'Blank' or self.olfacto.olfa_specs[0]['Vials'][i]['odor'] == 'blank':
                    self.CheatingVial.append(int(i))
                if self.olfacto.olfa_specs[0]['Vials'][i]['initial'] == 'NOGO' or self.olfacto.olfa_specs[0]['Vials'][i]['initial'] == 'NoGo' or self.olfacto.olfa_specs[0]['Vials'][i]['initial'] == 'nogo':
                    self.InitialNoGoVial.append(int(i))

        #Print out vials       
        print "\nGoVials: " + str(self.GoVials) + "\tNoGo Vialss: " + str(self.NoGoVials) + \
              "\tCheatingVials: " + str(self.CheatingVial) + "\tInitialGoVial: " + str(self.InitialGoVial)+ "\tInitialNoGoVial: " + str(self.InitialNoGoVial)  
        self.odorvial = random.choice(self.InitialGoVial)       
        time.clock()


        if self.ARDUINO:
            self.monitor = Monitor()
            print 'initializing monitor'
            self.monitor.protocol = self
            if self.monitor.protocol_name != self.protocol_name:
                print "WARNING, ARDUINO PROTOCOL IS NOT: " + self.protocol_name + 'PLEASE UPLOAD CORRECT SKETCH BEFORE STARTING'
            
        return
    
    def trial_parameters(self):
        """Returns a class of TrialParameters for the next trial"""
        

        if self.trialtype == "InitialGo":
            trial_type = 0
        elif self.trialtype == "Go":
            trial_type = 1
        elif self.trialtype == "NoGo":
            trial_type = 2

        protocol_params = {
                        "mouse"         : self.mouse,
                        "rig"           : self.rig,
                        "session"       : self.session,
                        'response_type' : self.response_type,
                        'Odor'          : self.odor,
                        'mfc1_flowrate' : self.olfacto.olfas[0].mfcs[0].flow,
                        'mfc2_flowrate' : self.olfacto.olfas[0].mfcs[1].flow,
                        'mfc1_pressure' : self.EOTairpressure,
                        'mfc2_pressure' : self.EOTnitrogenpressure,
                        'baselinemfc1_pressure' : self.baselineairpressure,
                        'baselinemfc2_pressure' : self.baselinenitrogenpressure,
                        'Odorconc'      : self.odorconc,
                        'Odorvial'      : self.odorvial,
                        '_threemissed'    : self.three_missed
                        }


        if self.response_type == 'treadmill': 
            treadmill = 1    
        else: 
            treadmill = 0
        

        controller_dict = {
                           
                            "trialNumber"   : (1, db.Int, self.trialNumber),
                            "Trialtype"     : (2, db.Int, trial_type),
                            "waterdur"      : (3, db.Int, self.waterdur),
                            "waterdur2"     : (4, db.Int, self.waterdur2),
                            "fvdur"         : (5, db.Int, self.fvdur),
                            "trialdur"      : (6, db.Int, self.trialdur),
                            "iti"           : (7, db.Int, self.interTrialIntervalSeconds * 1000),
                            "fvtrig_on_exh" : (8, db.Int, self.fvTrigPhaseVal),
                            "treadmill_response":(9, db.Int, treadmill),
                            'grace_period' : (10,db.Int, self.lickgraceperiod),
                            'rewards'       :(11,db.Int, self.rewards)
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
            'Odor'          : db.String32,
            'mfc1_flowrate' : db.Float,
            'mfc2_flowrate' : db.Float,
            'mfc1_pressure' : db.Float,
            'mfc2_pressure' : db.Float,
            'baselinemfc1_pressure' : db.Float,
            'baselinemfc2_pressure' : db.Float,
            'Odorconc'      : db.Float,
            'Odorvial'      : db.Int,
            '_threemissed'   : db.Bool
        }


        return params_def

    def controller_parameters_definition(self):
        """Returns a dictionary of {name => db.type} defining controller parameters"""

        params_def = {
            "trialNumber"    : db.Int,
            "Trialtype"      : db.Int,
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
            "_result"         : (1, db.Int),
            "paramsgottime"  : (2, db.Int),
            "starttrial"     : (3, db.Int),
            "endtrial"       : (4, db.Int),
            "no_sniff"       : (5, db.Int),
            "fvOnTime"       : (6, db.Int),

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

    def process_event_request(self, event):
        """
        Process event requested from controller.
        """
        self.timestamp("end")
        self.paramsgottime = int(event['paramsgottime'])
        self.trialstart = int(event['starttrial'])
        self.trialend = int(event['endtrial'])
        result = int(event['_result'])  # 1 is right, 2 is left, 3 left 4 right
        # update trials mask
        if self.trialend > self._laststreamtick:
            self._shiftlicks(self.trialend - self._laststreamtick)
            self._laststreamtick = self.trialend

        self._addtrialmask()
        

        if self.result[-1] == 1 or self.result[-1] == 2:
            self.rewards += 1
        if self.rewards >= self._max_rewards and self.start_label == 'Stop':
                self._start_button_fired()

        self.result = append(self.result, int(event['_result']))
        
        #Define ITI
        lastelement = self.result[-1]
        if (lastelement == 1 or lastelement == 2):  # Correct response
            self.interTrialIntervalSeconds = 10 + random.randint(1,3)
        else:
            self.interTrialIntervalSeconds = 16 + random.randint(1,3)
        
        return






    def process_stream_request(self, stream):
        """
        Process stream requested from controller.
        """
        
        if stream:
            # newtime = time.clock()
            num_sniffs = stream['sniff_samples']
            packet_sent_time = stream['packet_sent_time']

            # print "Num sniffs:", num_sniffs

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

    def start_of_trial(self):

        self.timestamp("start")
        print "*************************","\n Trial: ", self.trialNumber, 
          
        
        self.olfacto.olfas[0].set_vial(self.odorvial, 1);
        #do_later(1400,self.timestamp("start"))
               
        if self.protocol_type == 'Thresholding':
            if self.odorvial == self.CheatingVial[0]:
                self._lastvial = 1
            
    def end_of_trial(self):
        self.olfacto.olfas[0].mfcs[0].poll()
        self.EOTairpressure = self.olfacto.olfas[0].mfcs[0].pressure
        self.olfacto.olfas[0].mfcs[1].poll()
        self.EOTnitrogenpressure = self.olfacto.olfas[0].mfcs[1].pressure
        self.monitor.push_pressure(self.EOTairpressure, self.EOTnitrogenpressure)
        
        print "nitrogen pressure: ",self.EOTnitrogenpressure 
        self.olfacto.olfas[0].set_vial(self.odorvial, 0);
     
        
        #return electronic needle valve to baseline
        if self.trialNumber > 2:
            nitrogenbounds = random.choice([98, 99, 100])
            airbounds = (nitrogenbounds*10)-nitrogenbounds
            self.flows=(airbounds,nitrogenbounds)
            self.olfacto.olfas[0].set_flows(self.flows)
            self.pressuredifference = self.vialpressureclose[self.odorvial-5] - self.fluctuation
            if self.pressuredifference > 0:
                command = "open_step " + str(self.pressuredifference)
                self.monitor.send_command(command)
                print "*************************","open: ", self.pressuredifference 
                self.ENVdirection = 1
            if self.pressuredifference < 0:
                command = "close_step " + str(self.pressuredifference*-1)
                self.monitor.send_command(command)
                print "*************************","close: ", self.pressuredifference
                self.ENVdirection = -1
        #----------------------------------------------------------------------------
        self.pressuretimer(self.electronicneedlevalve) #timer to measure baseline and move needle valve to next vial position
        
        

        self.trialtype = self._next_trialtype
        self.odorvial = self._next_odorvial

        self.odor = self._next_odor
        self.odorconc = self._next_odorconc
        self.calculate_next_trial_parameters()
        self.trial_time = 0
        if self.trialNumber == self.MaxtrialNumber:
            if self.trialmax == 1:
                self.monitor.pause_acquisition()
            if self.email == 1:
                emailSubject = "Check on Mouse {}".format(self.mouse)
                sendEmail(self.receiver_email, emailSubject)


    def pressuretimer(self,continuation):        
        pressure_ms = 4000
        if self.pressuretimerObj:
            self.pressuretimerObj.stop()
            self.pressuretimerObj.deleteLater()
        self.pressuretimerObj = QTimer()
        self.pressuretimerObj.timeout.connect(continuation)
        self.pressuretimerObj.setSingleShot(True)
        self.pressuretimerObj.start(pressure_ms)
        return

    def electronicneedlevalve(self):
        self.baselineairpressure = self.olfacto.olfas[0].mfcs[0].pressure
        self.baselinenitrogenpressure = self.olfacto.olfas[0].mfcs[1].pressure
#        self.monitor.push_pressure(self.baselineairpressure, self.baselinenitrogenpressure)
        print "baseline nitrogen pressure: ", self.baselinenitrogenpressure
        
        ##-----------out of range----------------------------------------------------------------
        if self.baselinenitrogenpressure > self.pressure_target + 0.84:
            print "out of range"
            self.monitor.pause_acquisition()
            self.pause_label = 'Unpause'
            self.driftdifference = (self.baselinenitrogenpressure - self.pressure_target)*100
            print "driftdifference", self.driftdifference
            command = "open_step " + str(self.homestepsize)
            self.monitor.send_command(command)
            self.ENVdirection = 1
            self.outofrange = 1
        
            if self.hometimerObj:
                self.hometimerObj.stop()
                self.hometimerObj.deleteLater()
            self.hometimerObj = QTimer()
            self.hometimerObj.timeout.connect(self.HomePositive)
            self.hometimerObj.setSingleShot(False)
            self.hometimerObj.start(3000)

        if self.baselinenitrogenpressure < self.pressure_target - 0.61:
            print "out of range"
            self.monitor.pause_acquisition()
            self.pause_label = 'Unpause'
            self.driftdifference = (self.baselinenitrogenpressure - self.pressure_target)*100
            print "driftdifference", self.driftdifference
            command = "close_step " + str(self.homestepsize)
            self.monitor.send_command(command)
            self.ENVdirection = -1
            self.outofrange = 1
        
            if self.hometimerObj:
                self.hometimerObj.stop()
                self.hometimerObj.deleteLater()
            self.hometimerObj = QTimer()
            self.hometimerObj.timeout.connect(self.HomeNegative)
            self.hometimerObj.setSingleShot(False)
            self.hometimerObj.start(3000)
        ##----------------------------------------------------------------------------------------------------------------
            
        self.driftdifference = (self.baselinenitrogenpressure - self.pressure_target)*100
        
        # determine number of steps to fix drift
        self.driftdifference = round(self.driftdifference,1)
        self.driftdifference = int(self.driftdifference)
            #drift down need to close
        if self.driftdifference < 0:
                #number of close steps needed to return to baseline
            self.driftstep = (self.driftdown[-self.driftdifference])
            #drift up need to open   
        if self.driftdifference > 0:
            self.driftstep = (self.driftup[self.driftdifference])
            
         #move electronic needlevale to the position for the next vial   
        self.fluctuation = random.randint(self.vialpressurefluctuationhigh[self.odorvial-5],self.vialpressurefluctuationlow[self.odorvial-5])
        
        self.pressuredifference = self.vialpressureopen[self.odorvial-5] + self.fluctuation
         
         #combine number of steps to fix drift and move electronic needle valve to the correct position
        self.pressuredifference = self.pressuredifference + self.driftstep
        print self.pressuredifference

        if self.pressuredifference > 0:
            if self.ENVdirection == 1:
                command = "open_step " + str(self.pressuredifference)
                self.monitor.send_command(command)
                print "*************************","open: ", self.pressuredifference
            else:
#                command = "open_step " + str(self.pressuredifference+20)
                command = "open_step " + str(self.pressuredifference+30)
                self.monitor.send_command(command)
                print "*************************","open: ", self.pressuredifference
            self.ENVdirection = 1
        
        if self.pressuredifference < 0:
            if self.ENVdirection == -1:
                command = "close_step " + str(self.pressuredifference*-1)
                self.monitor.send_command(command)
                print "*************************","close: ", self.pressuredifference
            else:
#                command = "close_step " + str(-self.pressuredifference+20)
                command = "close_step " + str(-self.pressuredifference+30)
                self.monitor.send_command(command)
                print "*************************","close: ", self.pressuredifference
            self.ENVdirection = -1
        nitrogenbounds = random.choice([98, 99, 100])
        airbounds = (nitrogenbounds*10)-nitrogenbounds
        self.flows=(airbounds,nitrogenbounds)
        self.olfacto.olfas[0].set_flows(self.flows)


        

    def calculate_next_trial_parameters(self):
        if self.protocol_type == 'Stage 2 Training':
            if self.trialNumber < self.InitialGoNumber:
                self._next_trialtype = 'InitialGo'
                self._next_odorvial = random.choice(self.InitialGoVial) 
               
            else:
                self._next_trialtype = random.choice(['Go', 'NoGo'])
                if self._next_trialtype == "NoGo":
                     self._next_odorvial = random.choice(self.InitialNoGoVial)     
                if self._next_trialtype == 'Go':
                    self._next_odorvial = random.choice(self.InitialGoVial)
        
        elif self.protocol_type == 'Thresholding':
            if self.trialNumber < self.InitialGoNumber:
                self._next_trialtype = 'InitialGo'
                self._next_odorvial = random.choice(self.InitialGoVial)
            else:
                self._next_trialtype = random.choice(['Go', 'NoGo'])
                if self._next_trialtype == "NoGo":
                    self._next_odorvial = random.choice(self.NoGoVials)
                if self._next_trialtype == 'Go':
                    self._next_odorvial = random.choice(self.GoVials)
        
        self._next_odor = self.olfacto.olfa_specs[0]['Vials'][str(self._next_odorvial)]['odor']
        self._next_odorconc = self.olfacto.olfa_specs[0]['Vials'][str(self._next_odorvial)]['conc'] * 1.0 * self.nitrogen / (self.air + self.nitrogen)        
        return
    
    def trial_iti_milliseconds(self): #ITI is defined in process event
        
        #return self.interTrialIntervalSeconds*1000
        return (self.interTrialIntervalSeconds)*1000

    def timestamp(self, when):
        """ Used to timestamp events """
        if(when == "start"):
            self._paramsenttime = time.clock()
            # print "start timestamp ", self._paramsenttime
        elif(when == "end"):
            self._resultstime = time.clock()




if __name__ == '__main__':

    # arduino parameter defaults


    trialNumber = 1
    trialtype = "InitialGo"
    fvdur = 0
    trialdur = 2000
    lickgraceperiod = 0
    stimindex = 0
    laseramp = 1500
    lasergolatency = 100
    laserTrigPhase = "Inhalation"
    protocol_type = "Please Select"
    max_rewards = 4000


    # protocol parameter defaults
    mouse = 1  # can I make this an illegal value so that it forces me to change it????

    session = 1
    stamp = time_stamp()
    interTrialInterval = 8 #inter-trial interval in python is used. Function below. 
    stimindex = 0

    # protocol
    protocol = Thresholding(trialNumber,
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



