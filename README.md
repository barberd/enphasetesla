# enphasetesla

Python script to match Tesla charging with Enphase solar array electricity production

This is a quick and dirty script to read power production from an enphase solar array and then adjust the charging of a tesla to match.

This is useful when net metering is not available, or when the cost of electricty sent back to the grid is less than the cost of electricity consumed from the grid. The idea is that when extra solar power is available, the tesla battery is charged.

Requires the requests, json, and teslapy python modules.

The first time it runs, the teslapy module will prompt for API key capture.
You'll need to generate enphase API keys at https://developer.enphase.com/.

Edit the config.json file to put in your tesla account email address, home latitude and longitude (make sure to use negative longitude for western hemisphere), and the systemid and number of reporting devices (panels) in your enphase array. Then run match.py. It will fetch current status, set the Tesla charging appropriately, and then sleep for 15 minutes to repeat.

# License

     This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
    This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
    You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>. 

