#!/usr/bin/python3
import json
import re
from asterisk.agi import *
import subprocess
import threading

agi = AGI()

agi.verbose("python agi started")

parsed = {}

#Open and parse the input json file
with open("projectile.json", "r") as file:
	data = file.read()
	parsed = json.loads(data)

	def execute_action(action):
	if action == "num":
		return agi.get_data("", timeout=-1, max_digits=10)


#Launch the target
#redirect stderr to agi_verbose
#thread will exit when we get an empty bytestring which we get after the child exits
def stderr_redir(proc):
	for line in iter(proc.stderr.readline, b''):
		agi.verbose("[PY AGI CHILD STDERR] " + line)


#Helper output reader that will run on another thread
def output_reader(proc):
	#got line from program - check if it matches anything we are looking for
	#if it does, do the appropriate command and get the result back
	for line in iter(proc.stdout.readline, b''):
		for reader in parsed["readers"]:
			if(re.search(reader["regex"], line) != None):
				#found the match we were looking for
				#execute the specified action and pipe the result back into the process
				result = execute_action(reader["toRead"])
				agi.verbose("got action result" + str(result))
				proc.stdin.write(str(result) + "\n")
				break #done going over the readers for this line of program output, wait for the next line



def main():
	proc = subprocess.Popen(parsed["target"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

et = threading.Thread(target=stderr_redir, args=(proc,))
ot = threading.Thread(target=output_reader, args=(proc,))

et.start()
ot.start()
