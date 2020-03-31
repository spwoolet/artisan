#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ABOUT
# GIESEN CSV Roast Profile importer

import time as libtime
import os
import io
import csv
import re
            
from PyQt5.QtCore import QDateTime,Qt
from PyQt5.QtWidgets import QApplication

from artisanlib.util import encodeLocal

# returns a dict containing all profile information contained in the given IKAWA CSV file
def extractProfileGiesenCSV(file):
    res = {} # the interpreted data set

    res["samplinginterval"] = 1.0

    csvFile = io.open(file, 'r', newline="",encoding='utf-8')
    data = csv.reader(csvFile,delimiter=',')
    #read file header
    header = next(data)
    
    speed = None # holds last processed drum event value
    speed_last = None # holds the drum event value before the last one
    power = None # holds last processed heater event value
    power_last = None # holds the heater event value before the last one
    speed_event = False # set to True if a drum event exists
    power_event = False # set to True if a heater event exists
    specialevents = []
    specialeventstype = []
    specialeventsvalue = []
    specialeventsStrings = []
    timex = []
    temp1 = []
    temp2 = []
    extra1 = [] # ror
    extra2 = [] # power
    extra3 = [] # speed
    extra4 = [] # pressure
    timeindex = [-1,0,0,0,0,0,0,0] #CHARGE index init set to -1 as 0 could be an actal index used
    i = 0
    for row in data:
        i = i + 1
        items = list(zip(header, row))
        item = {}
        for (name, value) in items:
            item[name] = value.strip()
        # take i as time in seconds
        timex.append(i)
        if 'air' in item:
            temp1.append(float(item['air']))
        else:
            temp1.append(-1)
        # we map IKAWA Exhaust to BT as main events like CHARGE and DROP are marked on BT in Artisan
        if 'beans' in item:
            temp2.append(float(item['beans']))
        else:
            temp2.append(-1)
        # mark CHARGE
        if not timeindex[0] > -1:
            timeindex[0] = i
        # add ror, power, speed and pressure
        if 'ror' in item:
            extra1.append(float(item['ror']))
        else:
            extra1.append(-1)
        if 'power' in item:
            extra2.append(float(item['power']))
        else:
            extra2.append(-1)
        if 'speed' in item:
            extra3.append(float(item['speed']))
        else:
            extra3.append(-1)
        if 'pressure' in item:
            extra4.append(float(item['pressure']))
        else:
            extra4.append(-1)
        
        if "speed" in item:
            try:
                v = float(item["speed"])
                if v != speed:
                    # speed value changed
                    if v == speed_last:
                        # just a fluctuation, we remove the last added speed value again
                        speed_last_idx = next(i for i in reversed(range(len(specialeventstype))) if specialeventstype[i] == 1)
                        del specialeventsvalue[speed_last_idx]
                        del specialevents[speed_last_idx]
                        del specialeventstype[speed_last_idx]
                        del specialeventsStrings[speed_last_idx]
                        speed = speed_last
                        speed_last = None
                    else:
                        speed_last = speed
                        speed = v
                        speed_event = True
                        v = v/10. + 1
                        specialeventsvalue.append(v)
                        specialevents.append(i)
                        specialeventstype.append(1)
                        specialeventsStrings.append(item["speed"] + "%")
                else:
                    speed_last = None
            except Exception as e:
                pass
        if "power" in item:
            try:
                v = float(item["power"])
                if v != power:
                    # power value changed
                    if v == power_last:
                        # just a fluctuation, we remove the last added power value again
                        power_last_idx = next(i for i in reversed(range(len(specialeventstype))) if specialeventstype[i] == 3)
                        del specialeventsvalue[power_last_idx]
                        del specialevents[power_last_idx]
                        del specialeventstype[power_last_idx]
                        del specialeventsStrings[power_last_idx]
                        power = power_last
                        power_last = None
                    else:
                        power_last = power
                        power = v
                        power_event = True
                        v = v/10. + 1
                        specialeventsvalue.append(v)
                        specialevents.append(i)
                        specialeventstype.append(3)
                        specialeventsStrings.append(item["power"] + "%")
                else:
                    power_last = None
            except:
                pass

    csvFile.close()
            
    res["timex"] = timex
    res["temp1"] = temp1
    res["temp2"] = temp2
    res["timeindex"] = timeindex
    
    res["extradevices"] = [25,25]
    res["extratimex"] = [timex[:],timex[:]]
    
    res["extraname1"] = ["ror","speed"]
    res["extratemp1"] = [extra1,extra3]
    res["extramathexpression1"] = ["",""]
    
    res["extraname2"] = ["power","pressure"]
    res["extratemp2"] = [extra2,extra4]
    res["extramathexpression2"] = ["",""]
    
    if len(specialevents) > 0:
        res["specialevents"] = specialevents
        res["specialeventstype"] = specialeventstype
        res["specialeventsvalue"] = specialeventsvalue
        res["specialeventsStrings"] = specialeventsStrings
        if power_event or speed_event:
            # first set etypes to defaults
            res["etypes"] = [QApplication.translate("ComboBox", "Air",None),
                             QApplication.translate("ComboBox", "Drum",None),
                             QApplication.translate("ComboBox", "Damper",None),
                             QApplication.translate("ComboBox", "Burner",None),
                             "--"]
            # update
            if speed_event:
               res["etypes"][0] = "Speed"
            if power_event:
               res["etypes"][3] = "Power"
    return res
                