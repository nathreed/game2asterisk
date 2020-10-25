#!/usr/bin/python3
import json
import re
from asterisk.agi import *
import subprocess
import threading
import fcntl
import os

#used so that we can easily copy this testing code into the AGI version
def output(string):
	print(string)

def agi_say(string):
	if string == "\n" or string == "":
		return
	print("FAKE AGI SAY: " + string)


def setNonBlocking(fd):
    """
    Set the file description of the given file descriptor to non-blocking.
    """
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    flags = flags | os.O_NONBLOCK
    fcntl.fcntl(fd, fcntl.F_SETFL, flags)

def agi_get_multi_digit():
	#we play a silence because we have to play something i think
	#result = agi.get_data("silence/1", timeout=-1)
	result = input("Fake AGI asking for a multi digit number: ")
	return int(result)


parsed = {}

#Open and parse the input json file
with open("tty_golf.json", "r") as file:
	data = file.read()
	parsed = json.loads(data)


#a better name for replacement is "line" or "string" but I don't have good automated refactor tools
def process_capture_string(replacement, matchObj):
	new_replacement = ""
	last_replacement_last_index = 0
	for repMatch in re.finditer("\${([0-9]*)}", replacement):
		#we will build up the new replacement little by little
		#start from the end index of the last match and just add the unmatched text until the beginning of this match
		new_replacement += replacement[last_replacement_last_index:repMatch.start()]
		#now add the replacement value that we calculated - the xth match from the original match object
		orig_index = int(repMatch.group(1))
		new_replacement += matchObj.group(orig_index)
		#and store the last index of this match so that we can build it up properly in the next iteration
		last_replacement_last_index = repMatch.end()
	#Need to do one more concatenation to get the rest of the stuff after the last ${x} occurrence
	new_replacement += replacement[last_replacement_last_index:len(replacement)]
	return new_replacement

def execute_action(reader, matchObj):
	action = reader["action"]
	if action == "num":
		return input("Fake AGI asking for number: ")
	elif action == "multinum":
		return agi_get_multi_digit()
	elif action == "noop":
		return None
	elif action == "processedLiteralReturn":
		#Need to process the given string to populate any ${x} syntax and then return it
		processed = process_capture_string(reader["literal"], matchObj)
		return processed
	else:
		#we have no idea what it should be because no regex matched
		output("NO MATCH")
		return input("Fake AGI asking for number: ")


def apply_output_transformer(line, matchObj, transformer):
	if(transformer["type"] == "replace"):
		#this is a simple regex replace
		#it's made a little bit more involved by the fact that we support the ${x} syntax where x is the number of a capture group in the original regex
		#So to effect that, first we will find those and replace them to construct the string
		#Then we will put that string in the appropriate group
		replacement = transformer["replacementValue"]
		new_replacement = process_capture_string(replacement, matchObj)

		output("calculated replacement string: " + new_replacement)

		#Now we just have to replace the specified capture group in the original regex with the replacement string we have calculated
		#Since we have the match object we can't use RE sub operations on it so we will just do the substitution ourselves
		orig_group_index = int(transformer["captureGroup"])

		new_line = line[0:matchObj.start(orig_group_index)] + new_replacement + line[matchObj.end(orig_group_index)+1:len(line)]

		return new_line
	elif transformer["type"] == "replaceEntireString":
		return process_capture_string(transformer["replacementValue"], matchObj)

	else:
		output("UNKNOWN OUTPUT TRANSFORMER TYPE!")
		return line


def apply_input_transformer(line, transformer):
	if transformer["type"] == "digitStrMapping":
		#the line is going to be a string of the digit(s) we got back from the user
		#apply this to the mapping and return the correct string out
		try:
			result = transformer["mappings"][line]
			return result
		except KeyError:
			output("NO SUCH MAPPING FOR INPUT " + line) 
			return line
	else:
		output("UNKNOWN INPUT TRANSFORMER TYPE!")
		return line


def main():
	output("launch target " + str(parsed["target"]))
	proc = subprocess.Popen(parsed["target"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1024)

	setNonBlocking(proc.stdout)
	setNonBlocking(proc.stderr)

	cur_output = b""
	#nasty hack - if the input doesn't change for 25 iterations, then go with it
	remaining_iterations = 25
	while True:
		try:
			#ready_output = proc.stdout.readline()
			#if not b'\n' in ready_output:
				#cur_output += 
			proc.stdout.flush()
			cur_output += proc.stdout.readline()
			if(cur_output != b''):
				output("GOT DATA " + str(cur_output))
				if not b'\n' in cur_output and remaining_iterations > 0:
					#keep reading until we can get an entire line
					#for some reason this is necessary with java
					remaining_iterations -= 1
					continue
				out_str = str(cur_output)
				line = cur_output.decode("utf-8")
				#reset cur_output so that it gets written to properly next time
				cur_output = b""
				remaining_iterations = 20
				found = False
				for reader in parsed["readers"]:
					match = re.search(reader["regex"], str(line))
					if(match != None):
						found = True
						#First execute all the output transformers, one after the other, on the string
						try:
							for transformer in reader["outputTransformers"]:
								line = apply_output_transformer(line, match, transformer)

						except KeyError: #no output transformers present
							pass

						#We have finished transforming the line, say it now
						agi_say(line)
						#found the match we were looking for
						#execute the specified action and pipe the result back into the process
						#Read the input hint if it exists
						try:
							#input hints also need to be processed because they support the ${x} syntax as well
							processed = process_capture_string(reader["inputHint"], match)
							agi_say(processed)
						except KeyError:
							pass

						result = execute_action(reader, match)

						if result == None: #for noops
							break

						#agi.verbose("got action result" + str(result))
						output("got action result " + str(result))
						try:
							#Apply input transformers one after the other on the user input
							for transformer in reader["inputTransformers"]:
								result = apply_input_transformer(str(result), transformer)
						except KeyError:
							pass

						proc.stdin.write(bytearray(str(result) + "\n", "utf-8"))
						proc.stdin.flush()
						break #done going over the readers for this line of program output, wait for the next line
				if not found:
					agi_say(line)
		except IOError:
			continue




main()
