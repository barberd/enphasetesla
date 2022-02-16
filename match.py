#!/usr/bin/env python3

# By Don Barber don@dgb3.net Copyright 2022

# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.


# Reads from Enphase Solar Panel controller via Enphase API
# to get current electricity production
# and then sets the charging amperage of the Tesla via the Tesla API
# to match the production.
# The code attempts to accomodate current household usage, but rounds up
# so a little bit of electricity is taken off the grid, maximizing the usage
# of solar and minimizing the amount fed back to the grid.
# As the resolution of enphase seems to be every 15 minutes, with a 5 minute
# delay, its not perfect, but gets pretty close.

import requests
import math
import teslapy
import time
import datetime
import json

with open("config.json") as infile:
    config = json.load(infile)

homelate = config["homelat"]
homelong = config["homelong"]
teslaemail = config["teslaemail"]
apikey = config["apikey"]
userid = config["userid"]
systemid = config["systemid"]
devicenum = config["devicenum"]
auth="key=%s&user_id=%s"%(apikey,userid)

def setcar(vehicle):
        global sparewatts,lastvehiclechange,lastoutts,lastin
        vehicle.sync_wake_up()
        try:
          vd=vehicle.get_vehicle_data()
        except:
          return
        name=vd["display_name"]
        if vd["charge_state"]["charge_port_door_open"]!=True:
            print("%s: Ignoring as not plugged in"%(name))
            return
        if ((vd["drive_state"]["latitude"]-homelat) > .01) or ((vd["drive_state"]["longitude"]-homelong) > .01):
          print("%s: Ignoring as not at home"%(name))
          return
        battery_level = vd["charge_state"]["battery_level"]
        current = vd["charge_state"]["charger_actual_current"]
        voltage = vd["charge_state"]["charger_voltage"]
        print("%s: Currently using %i amps"%(name,current))
        freewatts=sparewatts+current*voltage
        if freewatts>lastin:
            freewatts=lastin
        print("Spare Watts backing this out:",freewatts)
        if battery_level < vd["charge_state"]["charge_limit_soc"] and freewatts>0:
          amptarget=max(min(math.ceil(freewatts/240),32),5) # keep between 5 and 32 amps)
          print("%s: Setting charging amps to %i"%(name,amptarget))
          vehicle.command('CHARGING_AMPS',charging_amps=amptarget)
          sparewatts=freewatts-(amptarget*240)
          lastvehiclechange=lastoutts
          if vd["charge_state"]["charging_state"]!="Charging":
            print("%s: Start charging"%name)
            vehicle.command('START_CHARGE')
        elif vd["charge_state"]["charging_state"] not in ("Stopped","Complete"):
            sparewatts=freewatts
            print("%s: Stop charging"%name)
            vehicle.command('STOP_CHARGE')
            vehicle.command('CHARGING_AMPS',charging_amps=32)
            lastvehiclechange=lastoutts

lastints=0
lastin=0
lastout=1000000
lastoutts=0
newdata=False
lastvehiclechange=0

def processmatch():
    global sparewatts,lastin,lastints,lastout,lastoutts,newdata,lastvehiclechange
    now=time.time()

    url="https://api.enphaseenergy.com/api/v2/systems/%s/consumption_stats?%s"%(systemid,auth)
    r=requests.get(url).json()
    r['intervals'].sort(key=lambda item: item.get("end_at"))
    if r['intervals'][-1]["end_at"] > lastoutts or r['intervals'][-1]['enwh']*4 != lastout:
        lastout=r['intervals'][-1]['enwh']*4
        lastoutts=r['intervals'][-1]["end_at"]
        newdata=True

    url="https://api.enphaseenergy.com/api/v2/systems/%s/stats?%s"%(systemid,auth)
    r=requests.get(url).json()
    try:
        r['intervals'].sort(key=lambda item: item.get("end_at"))
        if r['intervals'][-1]['devices_reporting']==devicenum and (r['intervals'][-1]["end_at"] > lastints or r['intervals'][-1]['powr']!=lastin):
            lastin=r['intervals'][-1]['powr']
            lastints=r['intervals'][-1]["end_at"]
            newdata=True
    except:
        pass

    if newdata:
        print("Consumed: %i watts collected %i seconds ago."%(lastout,time.time()-lastoutts))
        print("Produced: %i watts collected %i seconds ago."%(lastin,time.time()-lastints))

        sparewatts=lastin-lastout
        print("Spare Watts:",sparewatts)
        if lastoutts>lastvehiclechange:
            with teslapy.Tesla(teslaemail) as tesla:
                    vehicles = tesla.vehicle_list()
                    for vehicle in vehicles:
                        setcar(vehicle)
                        print("Spare Watts:",sparewatts)
            newdata=False
        else:
            print("Ignoring as last consumed data is older than last vehicle charge update.")
    else:
        print("No new data, sleeping...")
    return

while True:
    try:
        starttime=time.time()
        processmatch()
        sleeptime=(lastoutts+1210)-time.time()
        if sleeptime<=0:
            sleeptime=60
        print("Sleeping: ",sleeptime)
        time.sleep(sleeptime)
    except Exception as e:
        print(e)
        time.sleep(120)

