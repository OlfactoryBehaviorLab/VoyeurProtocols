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
from OlfactometerUtilities import Voyeur_utilities
from OlfactometerUtilities.range_selections_overlay import RangeSelectionsOverlay

# GENERAL DESCRIPTION OF DEWAN LAB IMAGING PROTOCOL
#    Modified 5/14/2019
#



class Imaging(Protocol):

#--------VARIABLE DECLARATION--------VARIABLE DECLARATION--------VARIABLE DECLARATION--------VARIABLE DECLARATION----------'''
# This section....
    
#BASIC VARIABLES
    STREAMSIZE = 20000      #Time in miliseconds that visualized on the GUI 
#    sniff_scale = 10         #Needed for visualization of sniff on GUI
    ARDUINO = 1             #Needed ????????????
    nitrogen = 200
    air = 800
    flows=(air,nitrogen)


#RESPONSE TYPE VARIABLES
    stimuli = {
               "Right" : [],        #Lick circuit 2 
               "Left": [],          #Lick circuit 1
               }

#SESSION PARAMATERS FOR EXPERIMENT AND VOYEUR GUI
    mouse = Int(0, label='mouse')       #Mouse ID. This can be set in the GUI and is saved in the data file
    rig = Str("", label='rig')          #Rig. This can be changed in the GUI but the default is Voyeur_Rig_Config file 
    stamp = Str(label='stamp')          #Timestamps. Prevents overwriting of data files
    session = Int(0, label='session')   #Session. This can be changed in the GUI
    rewards = Int(0, label="Total rewards")     #calculates and displays the total rewards
    response_type ='lick'                        
    trialNumber = Int(0, label='Trial')
    odortrialnumber = Int(-1, label='Odor Trial')
    exptrialnumber = Int(0, label='EXP Trial')
    maptrialnumber = Int(0, label='MAP Trial #')
    endtrialnumber = Int(0, label='END Trial')
    inscopixtrialnumber = Int(0, label='inscopix Trial')
    waterdur = Int(0, label="Water valve 1 duration")
    waterdur2 = Int(0, label="Water valve 2 duration")
    wateramt = Float(0, label="Water valve 1 amount")
    wateramt2 = Float(0, label="Water valve 2 amount")
    fvdur = Int(0, label="Final valve (On=1)")
    trialdur = Int(0, label="Trial duration")
    datarangehigh = Int(250, label="Data Range High")    #CHANGE SNIFFING Y AXIS VALUES!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!  
    datarangelow = Int(100, label="Data Range Low")
    
    preodortrialdur = Int(4000, label="Imaging duration before odor")
    odortrialdur = Int(2000, label="Odor duration")
    odoroffdur = Int(4000, label="Imaging duration after odor")
    Laserdur = Int(5, label="Laser pulse duration")
    Laserfreq = Int(20, label="Laser frequency (Hz)")
    Laserpower = Int(20, label="Laser power")
    prelasertrialdur = Int(2000, label="Imaging duration before laser")
    laseroffdur = Int(2000, label="Imaging duration after laser")
    lasertrialdur = Int(0, label="Laser stimulation duration")
    postduration = Int(0, label="postduration")         #variable passed to arduino
    preduration = Int(0, label="preduration")         #Tvariable passed to arduino
    interTrialIntervalSeconds = Int(0, label='ITI seconds')
    lickgraceperiod = Int(0, label="Lick grace period")         #Time after the finalvalve turns on in which the animal can not respond.
    BlankVials=[]
    OdorVials=[]
    vialnum = ['5','6','7','8','9','10','11']
    vial = Int(5, label='Vial #')
    AirMFC = Int(800, label='Air MFC')
    N2MFC  = Int(200, label='N2 MFC')         
    odorconc = Float(0, label="Odor concentration")
    odor = Str("Current odor", label='Odor')
    odorvial = Int(0, label="Odor Vial #")
                   
#TRIAL SPECIFIC PARAMETERS FOR EXPERIMENT AND VOYEUR GUI
    tick = Array      #Array for the X axis plotting intervals
    result = Array     #Array for results from Behaviora Controller
    trialstart = Int(0, label="Trial start time stamp") #Timestamp for the start of the trial
    trialend = Int(0, label="Trial end time stamp")      #timestamp for the end of the trial
    paramsgottime = Int(0, label="Time parameters received time stamp") #time that python received event info from arduino 
    no_sniff = Bool(False, label="Lost sniffing in last trial")         #
    fvOnTime = Int(0, label="Time of final valve open")                 #Time finalvalve turns on
    total_performance = Float(100.0, label="Total Performance")
    right_performance = Float(100.0, label="Go Trial Performance")
    left_performance = Float(100.0, label="NoGo Trial Performance")
    final_performance = Float(0.0, label="Final Performance")
    nolick_performance = Float(0.0, label="Final Go Performance")
    total_water = Float(0.0, label="Total Water (ul)")

    
# TIMERS
    elapsed_time_sec = Int(0, label = 'sec:')
    elapsed_time_min = Int(0, label = 'Time - min:')
    trial_time = Int(0, label = 'Time since last response (sec)')

#ARRAYS TO STORE STREAMING DATA (LICKS AND SNIFFING)
    iteration = Array #Subsampling the streaming sniff data
    sniff = Array      #streaming sniff data
    lick1 = Array       #streaming lick data from LC 1
    lick2 = Array       #streaming lick data from LC 2
    laser = Array

# INTERNAL VARIABLES THAT ARE RECALCULATED FOR EACH TRIAL
    _next_trialNumber = Int(0, label='trialNumber')
    _next_trialtype = Enum(("Wait", "Odor", "Opto"), label="Trial type")
    _last_trialtype = Enum(("Wait", "Odor", "Opto"), label="Last trial type")
    _next_odorvial = 0
    _next_odorconc = Float(0, label="Odor concentration")
    _next_odor = Str("Next odor", label="Odor")  # addition of odor concentration
    _next_trial_start = 0   #?????????????????What does this do?????????????
    _wv = Str('1')          #Used to trigger water valve with button?
    _corrights = 0
    _corlefts = 0
    _cortotal = 0
    _totalRightTrials = 0
    _totalLeftTrials = 0
    _blockRightTrials = 0         #Variable to keep track of number of right trials in a row
    _blockLeftTrials = 0
    _falserights = 0
    _falselefts = 0
    _nomoves = 0
    _paramsenttime = float()
    _resultstime = float()
    _laststreamtick = Float(0)
    _lastlickstamp = 0
    _previousendtick = 0
    _stimindex = int(0)              #???????????????????????????????
    _unsyncedtrials = 0


#--------------------------------------------------------------------------------------------------------------------------'''


    
#--------GUI ORGANIZATION--------GUI ORGANIZATION--------GUI ORGANIZATION--------GUI ORGANIZATION--------GUI ORGANIZATION--------
#This section......

#GUI BUTTON DECLARATIONS
    _olfactometer = Instance(Olfactometer)          #Initial olfactometer
    monitor = Instance(object)                      #Initial Voyeur monitor
    stream_plots = Instance(Component)
    stream_plot = Instance(Plot, label="Sniff")
    stream_event_plot = Instance(Plot, label="Events")
    start_button = Button()
    start_label = Str('Start')
    wait_button = Button()
    wait_label = Str('Give Mouse Water')
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
    opto_button = Button()
    opto_label = Str("Optogenetic Stimulation")
    buzzer_button = Button()
    buzzer_label = Str("BUZZER (OFF)")
    odortrial_button = Button()
    odortrial_label=Str("Odor Imaging Trial")
    database_button = Button()
    database_label=Str("Authenticate Database")
    Inscopix_button = Button("Inscopix")
    Inscopix_label=Str("Inscopix (OFF)")
    Laser_button = Button("Mightex")
    Laser_label=Str("Polygon")
    blank_button = Button("Blank")
    blank_label=Str("TURN BLANK ON")
    map_button = Button("Map")
    map_label=Str("Optogenetic Mapping")

#GUI SETUP
    session_group = Group(
                        Item('database_button',
                         editor=ButtonEditor(label_value='database_label'),
                         enabled_when='not monitor.recording',
                         show_label=False),
                        Item('protocol_name', style='readonly'),
                        Item('stamp', style='readonly'),
                        Item('elapsed_time_min',style='readonly'), 
                        Item('mouse', enabled_when='not monitor.running'),
                        Item('session', enabled_when='not monitor.running'),
                        Item('rig', enabled_when='not monitor.running'),
                        Item('trialNumber', style='readonly'),
                        Item('total_water',style = 'readonly'),
                        label='Session',
                        show_border=True
                    )

#BUTTONS FOR BEHAVIORAL CONTROLLER
    arduino = VGroup(
        HGroup(
            VGroup( Item('olfactory_button',
                         editor=ButtonEditor(label_value='olfactory_label'),
                         show_label=False),
                    Item('fv_button',
                         editor=ButtonEditor(style="button", label_value='fv_label'),
                         show_label=False),
                    ),
            VGroup( Item('Inscopix_button',
                         editor=ButtonEditor(style="button",label_value='Inscopix_label'),
                         show_label=False),
                    Item('Laser_button',
                         editor=ButtonEditor(style="button", label_value='Laser_label'),
                         show_label=False),
                    ),
            VGroup( Item('blank_button',
                         editor=ButtonEditor(style="button",label_value='blank_label'),
                         show_label=False),
                    Item('buzzer_button',
                         editor=ButtonEditor(style="button", label_value='buzzer_label'),
                         show_label=False),
                    ),
            VGroup( Item('water_button1',
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

#BASIC PYTHON BUTTONS AND SESSION PARAMETER FIELDS
    control = VGroup(
            HGroup(
                VGroup(Item('wait_button',
                          editor=ButtonEditor(label_value='wait_label'),
                          show_label=False),
                    Item('pause_button',
                        editor=ButtonEditor(label_value='pause_label'),
                        show_label=False,
                        enabled_when='monitor.running'),
                        ),
                label='User Control',
                show_border=True,
            ),
                            )

    current = Group(
                     Item('odortrial_button',
                         editor=ButtonEditor(label_value='odortrial_label'),
                         enabled_when='not monitor.recording',
                         show_label=False),
                    Item('odortrialnumber', style='readonly'),
                    Item('preodortrialdur'),
                    Item('odortrialdur'),
                    Item('odoroffdur'),
                    Item('AirMFC'),
                    Item('N2MFC'),
                    Item('vial'),
                    Item('odor', style='readonly'),
                    Item('odorconc', style='readonly'), 
                    
                    label='Olfactometer Parameters',
                    show_border=True
                    )

    next = Group(
                    Item('map_button',
                          editor=ButtonEditor(label_value='map_label'),
                          enabled_when='not monitor.recording',
                          show_label=False),
                    Item('maptrialnumber'),
                    Item('opto_button',
                          editor=ButtonEditor(label_value='opto_label'),
                          enabled_when='not monitor.recording',
                          show_label=False),
                    Item('Laserdur'),
                    Item('Laserfreq'),
                    Item('Laserpower'),
                    Item('prelasertrialdur'),
                    Item('lasertrialdur'),
                    Item('laseroffdur'),        

                    label='Laser Control',
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
                    title='Dewan Lab Imaging',
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
        pass
#        if self.protocol_type == 'Conditioning':
#            pass
#        elif self.protocol_type == 'Training':
#            pass
#        elif self.protocol_type == 'Discrimination':
#            pass
        return

#MOUSE NUMBER CHANGED GUI     
    def _mouse_changed(self):
        new_stamp = time_stamp()
        db = 'mouse' + str(self.mouse) + '_' + 'sess' + str(self.session) \
                    + '_' + new_stamp
        if self.db != db:
            self.db = db
        return

#DATA HIGH CHANGED GUI     
    def datarangehigh_changed(self):
        self._stream_plots_default()
        
        return

#DATA HIGH CHANGED GUI     
    def datarangelow_changed(self):
        self._stream_plots_default()
        return
 
#VIAL NUMBER CHANGED GUI     
    def _vial_changed(self):
        self.odorvial = self.vial
        self.odor = self.olfacto.olfa_specs[0]['Vials'][str(self.odorvial)]['odor']
        self.odorconc = self.olfacto.olfa_specs[0]['Vials'][str(self.odorvial)]['conc'] * 1.0 * self.N2MFC / (self.AirMFC + self.N2MFC)
        return
    
#AIR MFC CHANGED GUI     
    def _AirMFC_changed(self):
        self.air = self.AirMFC
        self.nitrogen = self.N2MFC
        self.odorvial = self.vial
        self.odor = self.olfacto.olfa_specs[0]['Vials'][str(self.odorvial)]['odor']
        self.odorconc = self.olfacto.olfa_specs[0]['Vials'][str(self.odorvial)]['conc'] * 1.0 * self.N2MFC / (self.AirMFC + self.N2MFC)
        self.flows=(self.AirMFC,self.N2MFC)
        self.olfacto.olfas[0].set_flows(self.flows) #Set flows based on the GUI
        return
    
#Nitrogen MFC CHANGED GUI     
    def _N2MFC_changed(self):
        self.air = self.AirMFC
        self.nitrogen = self.N2MFC
        self.odorvial = self.vial
        self.odor = self.olfacto.olfa_specs[0]['Vials'][str(self.odorvial)]['odor']
        self.odorconc = self.olfacto.olfa_specs[0]['Vials'][str(self.odorvial)]['conc'] * 1.0 * self.N2MFC / (self.AirMFC + self.N2MFC)
        self.flows=(self.AirMFC,self.N2MFC)
        self.olfacto.olfas[0].set_flows(self.flows) #Set flows based on the GUI
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

#DATABASE BUTTON
    def _database_button_fired(self):
        if self.monitor.recording:
            self.database_label = 'Authenticate Database'
            self.session_timer.Stop()
            self.session += 1
            print "Unsynced trials: ", self._unsyncedtrials
        
        if self.monitor.paused:
            self.monitor.stop_acquisition()
            self.database_label = 'Reset Database'
            
        else:
            self.database_label = 'Stop Recording'
            if self.monitor.protocol_name != self.protocol_name:
                print "WARNING, ARDUINO PROTOCOL IS NOT: " + self.protocol_name
                print 'Please exit and upload correct sketch to arduino before starting.'
                return
            self._restart()
            new_stamp = time_stamp()
            self.elapsed_time_min = 0
            self.elapsed_time_sec = 0
            self.trial_time = 0
            self.session_timer = Timer(1000,self.timer_update_task)
            self.db = 'mouse' + str(self.mouse) + '_' + 'sess' + str(self.session) \
                + '_' + new_stamp
            self.monitor.database_file = 'C:/VoyeurData/' + self.db
          
        return

#WAIT BUTTON. 
    def _wait_button_fired(self):
        #If the program is already running.
        if self.monitor.running:
            if self.monitor.paused:
                self.wait_label = 'Stop Water'
                self.trialtype = 'Wait'
                
                self.interTrialIntervalSeconds = 20 + random.randint(1,8)
                self.odorvial = 0
                self.odor = 'NA'
                self.exptrialnumber = 0
                self.monitor.unpause_acquisition()
                return
         
            if self.monitor.recording:
                self.monitor.pause_acquisition()
                self.wait_label = 'Give Mouse Water'
                self.session_timer.Stop()
                return
      
        else:
            if self.database_label != 'Stop Recording':
                print "WARNING! Need to authenicate database!"
                return
            self.trialtype = 'Wait'
            self.monitor.start_acquisition()
            self.interTrialIntervalSeconds = 20 + random.randint(1,8)
            self.odorvial = 0
            self.odor = 'NA'
            self.exptrialnumber = 0
            self.wait_label = 'Stop Water'
        return

#BLANK ODOR PRESNETATION BUTTON. 
    def _blank_button_fired(self):
        #If the program is already running.
        if self.monitor.running:
            if self.monitor.paused:
                self.blank_label = 'TURN BLANK OFF'
                self.trialtype = 'Blank'
                self.interTrialIntervalSeconds = 8 + random.randint(1,3)
                self.odorvial = 0
                self.odor = 'Blank'
                self.exptrialnumber = 0
                self.monitor.unpause_acquisition()
                return
         
            if self.monitor.recording:
                self.monitor.pause_acquisition()
                self.blank_label = 'TURN BLANK ON'
                self.session_timer.Stop()
                return
      
        else:
            if self.database_label != 'Stop Recording':
                print "WARNING! Need to authenicate database!"
                return
            self.trialtype = 'Blank'
            self.monitor.start_acquisition()
            self.interTrialIntervalSeconds = 8 + random.randint(1,3)
            self.odorvial = 0
            self.odor = 'Blank'
            self.exptrialnumber = 0
            self.blank_label = 'TURN BLANK OFF'
        return


#OPTOGENETIC STIMULATION TRIAL BUTTON. 
    def _opto_button_fired(self):
        if self.monitor.recording:
            self.monitor.unpause_acquisition()
        else:
            if self.database_label != 'Stop Recording':
                print "WARNING! Need to authenicate database!"
                return
            else:      
                self.odortrialnumber +=1
                self.inscopixtrialnumber +=1
                self.exptrialnumber = self.inscopixtrialnumber
                self.trialtype = 'Opto'
                self.preduration = self.prelasertrialdur
                self.trialdur = self.lasertrialdur
                self.postduration = self.laseroffdur
                self.interTrialIntervalSeconds = 4
                
                self.monitor.start_acquisition()
#                print('unpause 3333')
        return
 
    #OPTOGENETIC MAP TRIAL BUTTON. 
    def _map_button_fired(self):
        if self.monitor.recording:
            self.monitor.unpause_acquisition()
        else:
            if self.database_label != 'Stop Recording':
                print "WARNING! Need to authenicate database!"
                return
            else:      
                self.endtrialnumber = self.inscopixtrialnumber + self.maptrialnumber
                self.odortrialnumber +=1
                self.inscopixtrialnumber +=1
                self.exptrialnumber = self.inscopixtrialnumber
                self.trialtype = 'Map'
                self.preduration = self.prelasertrialdur
                self.trialdur = self.lasertrialdur
                self.postduration = self.laseroffdur
                self.interTrialIntervalSeconds = 4
                
                self.monitor.start_acquisition()
#                print('unpause 3333')
        return
    
    
    
    
#ODOR TRIAL BUTTON. 
    def _odortrial_button_fired(self):
        if self.monitor.recording:
            self.monitor.unpause_acquisition()
        else:
            if self.database_label != 'Stop Recording':
                print "WARNING! Need to authenicate database!"
                return
            else:      
                self.odortrialnumber +=1
                self.inscopixtrialnumber +=1
                self.exptrialnumber = self.inscopixtrialnumber
                self.trialtype = 'Odor'
                self.flows=(self.AirMFC,self.N2MFC)
                self.olfacto.olfas[0].set_flows(self.flows) #Set flows based on the GUI
                self.odorvial = self.vial
                self.preduration = self.preodortrialdur
                self.trialdur = self.odortrialdur
                self.postduration = self.odoroffdur             
#                self.olfacto.olfas[0].set_vial(self.odorvial, 1);#Turns on the specified vial
                self.interTrialIntervalSeconds = 4
                
                self.monitor.start_acquisition()
#                print('unpause 3333')
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

#ENDOSCOPE BUTTON
    def _Inscopix_button_fired(self):
        if self.monitor.recording:
            self._pause_button_fired()
        if self.Inscopix_label == "Inscopix (OFF)":
            self.monitor.send_command("Inscopix on")
            self.Inscopix_label = "Inscopix (ON)"
        elif self.Inscopix_label == "Inscopix (ON)":
            self.monitor.send_command("Inscopix off")
            self.Inscopix_label = "Inscopix (OFF)"
        return

#POLYGON BUTTON
    def _Laser_button_fired(self):
        self.monitor.send_command("laser")
        return
    
    
#BUZZERBUTTON
    def _buzzer_button_fired(self):
        if self.monitor.recording:
            self._pause_button_fired()
        if self.buzzer_label == "BUZZER (OFF)":
            self.monitor.send_command("buzzer on")
            self.buzzer_label = "BUZZER (ON)"
        elif self.buzzer_label == "BUZZER (ON)":
            self.monitor.send_command("buzzer off")
            self.buzzer_label = "BUZZER (OFF)"            
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
    
#Pause Button
    def _pause_button_fired(self):
        if self.monitor.recording:
            self.monitor.pause_acquisition()
            self.pause_label = 'Unpause'
        else:
            self.pause_label = 'Pause'
            self.monitor.unpause_acquisition()
        return


#---------------------------------------------------------------------------------------------------------------------------

#--------GUI PLOTS--------GUI PLOTS--------GUI PLOTS--------GUI PLOTS---------GUI PLOTS---------GUI PLOTS---------
#This section plots the licks and sniff data along with the blue mask that signals the trials. Sniff and lick streaming plots
#are intertwined so the plotting is just turned off and the size of the plot is minizied so it is not visible. 

#PLOTS EVENT DATA
    def _stream_event_plot_default(self):
        pass

#PLOTS SNIFF AND LICK DATA WITH BLUE TRIAL MASK
    def _stream_plots_default(self):

        container = VPlotContainer(bgcolor="transparent", fill_padding=False, padding=0)
        self.stream_plot_data = ArrayPlotData(iteration=self.iteration, sniff=self.sniff,laser=self.laser)
        y_range = DataRange1D(low=self.datarangelow, high=self.datarangehigh) # CHANGE FOR SNIFFING AMPLIFICATION
        plot = Plot(self.stream_plot_data, padding=25, padding_top=0, padding_left=60)
        plot.fixed_preferred_size = (100, 100)
        plot.value_range = y_range
        y_axis = plot.y_axis
        y_axis.title = "Signal (mV)"
        range_in_sec = self.STREAMSIZE / 1000.0
        self.iteration = arange(0.001, range_in_sec + 0.001, 0.001)
        self.sniff = [nan] * len(self.iteration)
        plot.plot(('iteration', 'sniff'), type='line', color='black', name="Sniff")
        self.stream_plot_data.set_data("iteration", self.iteration)
        self.stream_plot_data.set_data("sniff", self.sniff)
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
#--------------------------------------------------------------------------------------------------------------------------

#--------SAVED DATA--------ARDUINO COMMUNICATION---------SAVED DATA---------ARDUINO COMMUNICATION---------SAVED DATA---------SAVED DATA---------
#This section includes all the variables that will be saved in the database. They are organized alphabetically in the eventual datafile
#Returns a dictionary of {name => db.type} defining Voyeur (protocol) and Behavioral controller (Controller) parameters
#The number associated with the controller dictionary needs to match arduino sketch. This is how the info is sent and parsed.
#The type also needs to be declared for each variable. This needs to be completed in the parameter definition section.    
#This is not called until the monitor is started and the stream is requested. It does not setup the monitor before start.


#TRIAL TYPE FOR THE NEXT TRIAL THAT WILL BE SENT TO ARDUINO
#PYTHON (PROTOCOL) AND BEHAVIORAL CONTROLLER (CONTROLLER) PARAMETERS THAT WILL BE SAVED IN THE DATABASE FILE (VOYEUR/OLFACTOMETER)     
    def trial_parameters(self): 
        if self.trialtype == "Wait":
            trial_type = 0  #Animal gets water every so many seconds
        elif self.trialtype == "Odor":
            trial_type = 1  #Odor Stimulation trial
        elif self.trialtype == "Opto":
            trial_type = 2  #Optogenetic Stimulation trial
        elif self.trialtype == "Blank":
            trial_type = 4  #Blank Odor Presentation trial
        elif self.trialtype == "Map":
            trial_type = 5  #Optogenetic mapping trial

        protocol_params = {
                        "mouse"             : self.mouse,
                        "rig"               : self.rig,
                        "session"           : self.session,
                        'response_type'     : self.response_type,
                        'odor'              : self.odor,
                        'MFC1_flowrate'     : self.olfacto.olfas[0].mfcs[0].flow,
                        'MFC2_flowrate'     : self.olfacto.olfas[0].mfcs[1].flow,
                        'odorconc'          : self.odorconc,
                        'odorvial'          : self.odorvial,
                        'exptrialnumber'    : self.exptrialnumber,
                        'laserdur'          :self.Laserdur,
                        'laserfreq'         :self.Laserfreq,
                        'laserpower'        :self.Laserpower
#                        'threemissed'    : self.three_missed
                        }
        
        

        controller_dict = {
                            "trialNumber"   : (1, db.Int, self.trialNumber),
                            "trialtype"     : (2, db.Int, trial_type),
                            "waterdur"      : (3, db.Int, self.waterdur),
                            "waterdur2"     : (4, db.Int, self.waterdur2),
                            "fvdur"         : (5, db.Int, self.fvdur),
                            "trialdur"      : (6, db.Int, self.trialdur),
                            "waterdelay"    : (7, db.Int, self.waterdelay),
                            "iti"           : (8, db.Int, self.interTrialIntervalSeconds * 1000),
                            'pre_dur'       : (9,db.Int, self.preduration), #Preduration
                            'post_dur'      : (10,db.Int, self.postduration),   #Post duration
                            'rewards'       : (11,db.Int, self.rewards)
                            }

        return TrialParameters(
                    protocolParams=protocol_params,
                    controllerParams=controller_dict
                )

#VARIABLE DEFINITIONS FOR PYTHON (PROTOCOL) AND BEHAVIORAL CONTROLLER (CONTROLLER) PARAMETERS THAT WILL BE SAVED IN THE DATABASE FILE (VOYEUR/OLFACTOMETER)
    def protocol_parameters_definition(self):
        params_def = {
            "mouse"             : db.Int,
            "rig"               : db.String32,
            "session"           : db.Int,
            'response_type'     : db.String32,
            'odor'              : db.String32,
            'MFC1_flowrate'     : db.Float,
            'MFC2_flowrate'     : db.Float,
            'odorconc'          : db.Float,
            'odorvial'          : db.Int,
            'threemissed'       : db.Bool,
            'exptrialnumber'    : db.Int,
            'laserdur'          : db.Int,
            'laserfreq'         : db.Int,
            'laserpower'        :db.Int
        }
        return params_def

    def controller_parameters_definition(self):
        params_def = {
            "trialNumber"    : db.Int,
            "trialtype"      : db.Int,
            "waterdur"       : db.Int,
            "waterdur2"      : db.Int,
            "fvdur"          : db.Int,
            "trialdur"       : db.Int,
            "waterdelay"     : db.Int,
            "iti"            : db.Int,
            'grace_period'   : db.Int,
            'pre_dur'        : db.Int,
            'post_dur'       : db.Int,
            'rewards'        : db.Int
        }
        return params_def

#VARIABLE DEFINITIONS FOR EVENT AND STREAM DATA SENT FROM BEHAVIROAL CONTROLLER
    def event_definition(self):
        return {
            "result"         : (1, db.Int),
            "paramsgottime"  : (2, db.Int),
            "starttrial"     : (3, db.Int),
            "endtrial"       : (4, db.Int),
            "no_sniff"       : (5, db.Int),
            "fvOnTime"       : (6, db.Int)
        }

    def stream_definition(self):
        stream_def = {
                          "packet_sent_time" : (1, 'unsigned long', db.Int),
                          "sniff_samples"    : (2, 'unsigned int', db.Int),
                          "sniff"            : (3, 'int', db.FloatArray,),
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
                    self.sniff = hstack((new_sniff[-self.STREAMSIZE + num_sniffs:], negative(stream['sniff'] - 400)))
                    

            else:
                if stream['sniff'] is not None:
                    new_sniff = hstack((self.sniff[-self.STREAMSIZE + num_sniffs:], negative(stream['sniff'] - 400)))
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

#--------Initialization--------Initialization--------Initialization--------Initialization---------Initialization-----------
#This section...
    
    def __init__(self, trialNumber,
                        mouse,
                        session,
                        stamp,
                        interTrialInterval,
                        trialtype,
                        fvdur,
                        trialdur,
                        waterdelay,
                        lickgraceperiod,
                        preduration,
                        postduration,
                        protocol_type,
                        stimindex=0,
                        **kwtraits):
        super(Imaging, self).__init__(**kwtraits)
        self.trialNumber = trialNumber
        self.stamp = stamp
        self.config = Voyeur_utilities.parse_rig_config() #get a configuration object with the default settings.
        self.rig = self.config['rigName']
        self.waterdur = self.config['waterValveDurations']['valve_1_left']['valvedur']
        self.wateramt = self.config['waterValveDurations']['valve_1_left']['wateramt']
        self.waterdur2 = self.config['waterValveDurations']['valve_2_right']['valvedur']
        self.wateramt2 = self.config['waterValveDurations']['valve_2_right']['wateramt']
        self.olfas = self.config['olfas']
        self.db = 'mouse' + str(mouse) + '_' + 'sess' + str(session) + '_' + self.stamp
        self.mouse = mouse
        self.session = session
        self.interTrialIntervalSeconds = interTrialInterval
        self.trialtype = trialtype
        self._next_trialtype = self.trialtype
        self.fvdur = fvdur
        self.trialdur = trialdur
        self.waterdelay = waterdelay
        self.lickgraceperiod = lickgraceperiod
        self.preduration = preduration
        self.postduration = postduration
        self._stimindex = stimindex
        self.rewards = 0
        self.protocol_name = 'Imaging V2'

        
        config_filename = "C:\\voyeur_rig_config\olfa_config.json"
        self.olfacto=Olfactometers(None, config_filename)
        self.olfacto.olfas[0].set_flows(self.flows)
        time.clock()

# parses the olfactometer dictionary into different arrays corresonding to the correct vial locations
        
        
        if self.ARDUINO:
            self.monitor = Monitor()
            print 'initializing monitor'
            self.monitor.protocol = self
            if self.monitor.protocol_name != self.protocol_name:
                print "WARNING, ARDUINO PROTOCOL IS NOT: " + self.protocol_name + 'PLEASE UPLOAD CORRECT SKETCH BEFORE STARTING'
            
        return

#RESTART. RESET ALL VARIABLES
    def _restart(self):
        self.trialNumber = 0
        self._righttrials = [1]
        self._lefttrials = [1]
        self.tick = [0]
        self.result = [0]
        self.rewards = 0
        self._protocol_type_changed()
        self.calculate_next_trial_parameters()

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
#--------------------------------------------------------------------------------------------------------------------------'''

#--------BEHAVIORAL TASK--------BEHAVIORAL TASK--------BEHAVIORAL TASK--------BEHAVIORAL TASK--------BEHAVIORAL TASK--------
#This section.....    

#START TRIAL FUNCTION    
    def start_of_trial(self):

        self.timestamp("start")
        print "*************************","\n Trial: ", self.trialNumber, 
        if self.trialtype == "Odor":
            self.olfacto.olfas[0].set_vial(self.odorvial, 1);

#CALCULATE NEXT TRIAL PARAMETERS
    def calculate_next_trial_parameters(self):
    #Conditioning or Training Paradigm   
        pass
      #Determine odor and concentration for the appropriate vials regardless of paradigm
    
        return
 



#UPDATE PYTHON VARIABLES AFTER EACH PROCESS EVENT
    def _result_changed(self):
        #If there is no event return
        if len(self.result) == 1:
            return

        self.tick = arange(0, len(self.result))
        lastelement = self.result[-1]
      
        self.total_water = self.trialNumber * self.wateramt 
        

#ITI [This ITI controls the odor vial turning on. The ITI that is sent to the behavioral controller is in the process event request] 
    def trial_iti_milliseconds(self):
        return (self.interTrialIntervalSeconds-2)*1000

#TIMESTAMP. USED TO TIMESTAMP EVENTS
    def timestamp(self, when):
        if(when == "start"):
            self._paramsenttime = time.clock()
        elif(when == "end"):
            self._resultstime = time.clock()
  
#END OF TRIAL
    def end_of_trial(self):
        mfcs = self.olfacto.olfas[0].mfcs
        self.trial_time = 0
        self.trialNumber +=1 
        if self.trialtype == "Odor":
            self.olfacto.olfas[0].set_vial(self.odorvial, 0);
            self.monitor.pause_acquisition()
        if self.trialtype == "Opto":
            self.monitor.pause_acquisition()
        if self.trialtype == "Map":
            if self.exptrialnumber == self.endtrialnumber:
                self.monitor.pause_acquisition()
            else:
                 self.inscopixtrialnumber +=1
                 self.odortrialnumber +=1 
                 self.exptrialnumber = self.inscopixtrialnumber
#--------------------------------------------------------------------------------------------------------------------




if __name__ == '__main__':

    # arduino parameter defaults


    trialNumber = 1
    trialtype = "Wait"
    fvdur = 1
    trialdur = 2000
    waterdelay = 1000
    lickgraceperiod = 1000
    preduration = 2000
    postduration = 2000


    # protocol parameter defaults
    mouse = 1  # can I make this an illegal value so that it forces me to change it????

    session = 1
    stamp = time_stamp()
    interTrialInterval = 6
    stimindex = 0

    # protocol
    protocol = Imaging(trialNumber,
                    mouse,
                    session,
                    stamp,
                    interTrialInterval,
                    trialtype,
                    fvdur,
                    trialdur,
                    waterdelay,
                    lickgraceperiod,
                    preduration,
                    postduration,
                    stimindex,
                    )

    # GUI
    protocol.configure_traits()


