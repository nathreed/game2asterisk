#!/usr/bin/python3
import json
import re
from asterisk.agi import *
import subprocess
import threading
import fcntl
import os
import time

agi = AGI()

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

def agi_get_multi_digit():
	#we play a silence because we have to play something i think
	result = agi.get_data("silence/1", timeout=-1)
	return int(result)

def setNonBlocking(fd):
    """
    Set the file description of the given file descriptor to non-blocking.
    """
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    flags = flags | os.O_NONBLOCK
    fcntl.fcntl(fd, fcntl.F_SETFL, flags)


parsed = {}

#Open and parse the input json file
with open("/var/lib/asterisk/agi-bin/game2asterisk/rng_game.json", "r") as file:
	data = file.read()
	parsed = json.loads(data)

def execute_action(action):
	if action == "num":
		return agi.wait_for_digit(-1)
		#return input("Fake AGI asking for number: ")
	elif action == "multinum":
		return agi_get_multi_digit()
	else:
		#no idea
		agi_say("I don't know what kind of input you should enter. Guessing a number.")
		return agi.wait_for_digit(-1)

def main():
	agi.verbose("launch target " + str(parsed["target"]))
	proc = subprocess.Popen(parsed["target"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1)

	setNonBlocking(proc.stdout)
	setNonBlocking(proc.stderr)

	while True:
		try:
			out = proc.stdout.readline()
			if(out != b''):
				agi.verbose("GOT DATA " + str(out))
				agi_say(out.decode("utf-8").strip("\n"))
				out_str = str(out)
				line = out_str
				for reader in parsed["readers"]:
					if(re.search(reader["regex"], str(line)) != None):
						#found the match we were looking for
						#Read the input hint if it exists
						try:
							agi_say(reader["inputHint"])
						except KeyError:
							pass
						#execute the specified action and pipe the result back into the process
						result = execute_action(reader["toRead"])
						#agi.verbose("got action result" + str(result))
						agi.verbose("got action result" + str(result))
						proc.stdin.write(bytearray(str(result) + "\n", "utf-8"))
						proc.stdin.flush()
						break #done going over the readers for this line of program output, wait for the next line
		except IOError:
			continue



time.sleep(0.5)
main()
