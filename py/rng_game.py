#!/usr/bin/python3
import random

while True:
	num = int(input("Pick a number between 0 and 9: "))
	if num == random.randint(0,9):
		print("you got it")
	else:
		print("try again")