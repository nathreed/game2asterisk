#!/usr/bin/python3
from asterisk.agi import *
import subprocess
import time

agi = AGI()
agi.verbose("py agi init")


#function to say AGI stuff over the line
def agi_say(string):
	#construct the command to render the speech and another command to resample it
	#will name the file with the callerid of the caller
	filename = "nr_game2asterisk/" + agi.env["agi_callerid"]
	filepath = "/var/lib/asterisk/sounds/en/nr_game2asterisk/" + agi.env["agi_callerid"] + ".wav"
	#use filename.wav.i for "incomplete"
	espeak_cmd = "espeak -w " + filepath + ".i \"" + string + "\""
	sox_cmd = "sox " + filepath + ".i" + "-r 8000 " + filepath

	#execute the processes
	subprocess.call(["espeak", "-w " + filepath + ".i", "\"" + string + "\""])
	subprocess.call(["sox", filepath + ".i", "-r", "8000", filepath])
	#remove the intermediate one
	subprocess.call(["rm", "-f", filepath + ".i"])

	#send the file over the connection
	agi.stream_file(filename)

	#remove the final file too
	subprocess.call(["rm", "-f", filepath])



time.sleep(0.5)

agi_say("Thank you for calling the game hotline")

time.sleep(2)

agi.hangup()

