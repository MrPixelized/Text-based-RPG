import os
import time
import sys
import re

def separateBrackets(fileArray):
	stack = [[]]
	for element in fileArray:

		if element == '(':
			stack[-1].append([])
			stack.append(stack[-1][-1])

		elif element == ')':
			stack.pop()
			if not stack:
				raise RuntimeError('opening bracket is missing')

		else:
			stack[-1].append(element)
    
	if len(stack) > 1:
		raise RuntimeError('closing bracket is missing')

	return stack.pop()

def executeScript(code,main=False,previousOutput=None):
	global flags, variables
	if main and not previousOutput == ".script":
		flags = []
	if main and not previousOutput == ".script":
		variables = {}

	inputs = ["DEFAULT_INPUT"]

	i = -1

	while i < len(code)-1:
		i += 1

		variables["$RECENT_INPUT"] = inputs[-1]
		variables["$CURRENT_DIR"] = os.getcwd()

		# handling of request of previous nesting level

		if not previousOutput == None:
			if previousOutput.split(" ")[0] == ".label":
				if not main:
					return previousOutput
				else:
					destination = previousOutput
					if destination in code:
						i = code.index(destination) - 1
					else:
						raise RuntimeError("no destination found in main nesting level")
					previousOutput = None
					del destination
					continue

			if previousOutput == ".script":
				previousOutput = None

			if previousOutput == ".exit":
				return previousOutput

		# variables

		if isinstance(code[i], str):
			codeLine = code[i]
			for key in variables.keys():
		 		codeLine = codeLine.replace(key,str(variables[key]))

		# executing commands

		if isinstance(code[i], str):
			codeOriginal = code[i]
			if codeLine == "":
				continue

			if codeLine[0] == "#":
				continue

			# commands involving programmer interaction

			# help command

			if codeLine.split(" ")[0] == ".help":
				if codeLine == ".help":
					print("""
					Available commands are:        
					    .ask            question          
					    .case           [flag/value],[not], case, [*case]
					    .clear                    
					    .clearflags
					    .clearstorage
					    [.display]      text
					    .exit                     
					    .flag           flag, [true/false]
					    .label          labelname
					    .script         filename
					    .sleep          seconds
					    .store          key, value
					    .to             labelname/eol/eof

					Available global variables are:
					    $RECENT_INPUT   The last thing the user answered to a question
					    $CURRENT_DIR    The directory the script is in
					""".replace("\t",""))
				continue

			# commands involving code flow

			# store variable that is not boolean

			if codeLine.split(" ")[0] == ".store":
				if len(codeLine.split(" ",2)) == 3:
					if codeOriginal.split(" ")[1][0] == "$":
						try:
							variables[codeOriginal.split(" ")[1]] = eval(codeLine.split(" ",2)[2])
						except:
							variables[codeOriginal.split(" ")[1]] = str(codeLine.split(" ",2)[2])
						continue
					else:
						raise ValueError("variable name must start with $")
				else:
					raise SyntaxError(".store requires more arguments")

			# execute another script

			if codeLine.split(" ")[0] == ".script":
				executeScript(fileToCode(codeLine.split(" ",1)[1]),main=True,previousOutput=".script")

			# set boolean value

			if codeLine.split(" ")[0] == ".flag":
				if len(codeLine.split(" ")) == 2:
					if not codeLine.split(" ")[1] in flags:
						flags.append(codeLine.split(" ")[1])
					else:
						flags.remove(codeLine.split(" ")[1])

				if len(codeLine.split(" ")) == 3:
					if codeLine.split(" ")[2].lower() == "false":
						flags.remove(codeLine.split(" ")[1])
					elif codeLine.split(" ")[2].lower() == "true":
						if not codeLine.split(" ")[1] in flags:
							flags.append(codeLine.split(" ")[1])
				continue							

			# clear all saved flags

			if codeLine == ".clearflags":
				flags = []
				continue

			# clear all stored variables

			if codeLine == ".clearstorage":
				variables = {}
				continue

			# test for most recent input or any flag or any value

			if codeLine.split(" ")[0] == ".case":
				caseResult = False
				if codeOriginal.split(" ")[1] == "input":
					codeOriginal = codeOriginal.replace(".case input ",".case value $RECENT_INPUT ",1)
				elif not codeOriginal.split(" ")[1] in ["value","flag"]:
					codeOriginal = codeOriginal.replace(".case ",".case value $RECENT_INPUT ",1)

				if codeOriginal.split(" ")[2] == "not":
					inverseCheck = True
					codeOriginal = codeOriginal.replace(" not","",1)
				else:
					inverseCheck = False
				
				if codeOriginal.split(" ")[1] == "value":
					basevalue = codeOriginal.split(" ")[2]

					for key in variables.keys():
	 					basevalue = basevalue.replace(key,str(variables[key]))

					try:
						basevalue = int(basevalue)
					except:
						basevalue = str(basevalue)

					for testvalue in codeOriginal.split(" ",3)[3].split(","):
						testvalue = testvalue.strip()
						for key in variables.keys():
		 						testvalue = testvalue.replace(key,str(variables[key]))
						testtype = ""
						if testvalue[0] == "<" or testvalue[0] == ">":
							testtype = testvalue[0]
							testvalue = testvalue[1:]
						try:
							testvalue = int(testvalue)
						except:
							testvalue = str(testtype)+str(testvalue)
							testtype = ""

						if testtype == "":
							if basevalue == testvalue:
								caseResult = True
								break
							continue

						if testtype == ">" and basevalue > testvalue or testtype == "<" and basevalue < testvalue:
							caseResult = True
						else:
							caseResult = False
							break
				
				if codeOriginal.split(" ")[1] == "flag":
					for flag in codeOriginal.split(" ",2)[2].split(","):
						if flag.strip() in flags:
							caseResult = True
							break
						else:
							caseResult = False
				
				if inverseCheck:
					caseResult = not caseResult

				if not caseResult:
					i += 1
				else:
					if isinstance(code[i+1], list):
						previousOutput = executeScript(code[i+1])
				continue

			# acknowledge the existence of a label

			if codeLine.split(" ")[0] == ".label":
				continue

			# jump to end of level (nesting level), end of file (is the same as exit), or a specified label

			if codeLine.split(" ")[0] == ".to":
				if codeLine.split(" ")[1].lower() == "eol":
					break

				if codeLine.split(" ")[1].lower() == "eof":
					exit()

				previousOutput = codeLine.replace(".to",".label",1)
				if main == True:
					if i == len(code) -1:
						i -= 1
					continue
				else:
					return previousOutput

			# jumps to end of file

			if codeLine.lower() == ".exit":
				exit()

			# commands involving output flow

			# sleep for specified amount of milliseconds

			if codeLine.split(" ")[0] == ".sleep":
				time.sleep(float(codeLine.split(" ",1)[1]))
				continue

			# clear screen

			if codeLine == ".clear":
				os.system("cls")
				continue

			# commands involving printing

			lineToPrint = codeLine
			lineToPrint = lineToPrint.replace("\\n","\n")
			lineToPrint = lineToPrint.replace("\\t","\t")
			lineToPrint = lineToPrint.replace("\\s"," ")
			lineToPrint = lineToPrint.replace("\color:grey","\033[1;30m")
			lineToPrint = lineToPrint.replace("\color:red","\033[1;31m")
			lineToPrint = lineToPrint.replace("\color:green","\033[1;32m")
			lineToPrint = lineToPrint.replace("\color:yellow","\033[1;33m")
			lineToPrint = lineToPrint.replace("\color:blue","\033[1;34m")
			lineToPrint = lineToPrint.replace("\color:magenta","\033[1;35m")
			lineToPrint = lineToPrint.replace("\color:cyan","\033[1;36m")
			lineToPrint = lineToPrint.replace("\color:white","\033[1;37m")
			lineToPrint = lineToPrint.replace("\\ansi:","\033[")
			lineToPrint = lineToPrint.replace("\color","\033[0m")

			if codeLine.split(" ")[0] == ".ask":
				inputs.append(input(lineToPrint.replace(".ask ","",1)))
				continue
			
			if not codeLine[0] == "." or codeLine.split(" ")[0] == ".display":
				if not codeLine.split(" ")[0] == ".display":
					print(lineToPrint)
				else:
					if len(lineToPrint.split(" ")) > 1:
						print(lineToPrint.split(" ",1)[1])
					else:
						print("")
				continue
			
			del lineToPrint

			# if the command is not recognised, throw an error

			if codeLine[0] == ".":
				raise NameError("command not recognised")

	return None

def fileToCode(fileName):
	fileArray = open(fileName).readlines()
	fileArray = [item.strip().replace("$CURRENT_DIR",os.getcwd()) for item in fileArray]
	codeFile = separateBrackets(fileArray)
	return codeFile

fileName = sys.argv[1]

os.system("echo&cls")

executeScript(fileToCode(fileName),main=True)
