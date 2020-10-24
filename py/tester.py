#!/usr/bin/python3
import json
import re
from asterisk.agi import *
import subprocess
import threading
import fcntl
import os


def setNonBlocking(fd):
    """
    Set the file description of the given file descriptor to non-blocking.
    """
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    flags = flags | os.O_NONBLOCK
    fcntl.fcntl(fd, fcntl.F_SETFL, flags)


parsed = {}

#Open and parse the input json file
with open("rng_game.json", "r") as file:
	data = file.read()
	parsed = json.loads(data)

def execute_action(action):
	if action == "num":
		return input("Fake AGI asking for number: ")


#Launch the target
#redirect stderr to agi_verbose
#thread will exit when we get an empty bytestring which we get after the child exits
def stderr_redir(proc):
	for line in iter(proc.stderr.readline, b''):
		#agi.verbose("[PY AGI CHILD STDERR] " + line)
		print("[CHILD STDERR] " + str(line))


#Helper output reader that will run on another thread
def output_reader(proc):
	#got line from program - check if it matches anything we are looking for
	#if it does, do the appropriate command and get the result back
	for line in iter(proc.stdout.readline, b''):
		print("[CHILD STDOUT] " + str(line))
		for reader in parsed["readers"]:
			if(re.search(reader["regex"], str(line)) != None):
				#found the match we were looking for
				#execute the specified action and pipe the result back into the process
				result = execute_action(reader["toRead"])
				#agi.verbose("got action result" + str(result))
				print("got action result" + str(result))
				proc.stdin.write(str(result) + "\n")
				proc.stdin.flush()
				break #done going over the readers for this line of program output, wait for the next line



def main():
	print("launch target " + str(parsed["target"]))
	proc = subprocess.Popen(parsed["target"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1)

	setNonBlocking(proc.stdout)
	setNonBlocking(proc.stderr)

	while True:
		try:
			out = proc.stdout.readline()
			if(out != b''):
				print("GOT DATA " + str(out))
				out_str = str(out)
				line = out_str
				for reader in parsed["readers"]:
					if(re.search(reader["regex"], str(line)) != None):
						#found the match we were looking for
						#execute the specified action and pipe the result back into the process
						result = execute_action(reader["toRead"])
						#agi.verbose("got action result" + str(result))
						print("got action result" + str(result))
						proc.stdin.write(bytearray(str(result) + "\n", "utf-8"))
						proc.stdin.flush()
						break #done going over the readers for this line of program output, wait for the next line
		except IOError:
			continue




main()
