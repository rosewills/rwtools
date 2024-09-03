#!/usr/bin/env python
'''
Meta Utils

Version: 0.0.0
Created: 2023-07-20 (by Rose Wills)
Status: not finished

Various functions to manipulate YAML and system-level metadata.

'''

import os
import sys
from datetime import datetime
import re
import git
import shutil



# Pretty Colors for Terminal Output (Bash-specific)
class colors:
	red = '\033[91m'
	green = '\033[92m'
	yellow = '\033[93m'
	blue = '\033[94m'
	purple = '\033[95m'
	cyan = '\033[96m'
	bold = '\033[1m'
	underline = '\033[4m'
	endc = '\033[0m'

endline = "_________________________________________________________"


def getts(fileName, style="git", mode="mod"):
	# styles:
	# g = %Y-%m-%d %H:%M:%S.%f %z     "Git style"
	# o = %Y-%m-%dT%H:%M:%S           "Obsidian style"
	# h = %a %b %d, %I:%M:%S %p       "Human style"

	# Get last-modified time of file
	statFile = os.stat(fileName)
	if mode == "mod":
		tsTime = statFile.st_mtime
		tsTime = datetime.fromtimestamp(tsTime)
	elif mode == "cre":
		tsTime = statFile.st_ctime
		tsTime = datetime.fromtimestamp(tsTime)
	else:
		print(colors.red+"(getts1)", fileName, "ERROR: unknown mode \""+mode+"\" - please choose \"mod\" (default) or \"cre\""+colors.endc())

	if style == "git" or style == "g":
		modString = tsTime.strftime('%Y-%m-%d %H:%M:%S.%f %z')
	elif style == "obs" or style == "o" or style == "obsidian":
		modString = tsTime.strftime('%Y-%m-%dT%H:%M:%S')
	elif style == "hum" or style == "h" or style == "human":
		modString = tsTime.strftime('%d %b %Y %I:%M:%S %p %a')
	else:
		print(colors.red+"(getts2)", fileName, "ERROR: unknown style \""+style+"\" - please choose one of the following:"+colors.endc)
		print("\"g\" (%Y-%m-%d %H:%M:%S.%f %z) Git style")
		print("\"o\" (%Y-%m-%dT%H:%M:%S)       Obsidian style")
		print("\"h\" (%a %b %d, %I:%M:%S %p)   Human style")
		modString = ""

	# sys.stdout.write(modString)
	return modString

# git commit --date="$(metautils.py gettsp utility/metautils.py g)"
def gettsp(fileName, style="git"):
	print(getts(fileName, style))


# change system metatada to match YAML metadata
def fixmeta(fileName, v=False):
	statEpochTS = os.stat(fileName).st_mtime
	statDate = datetime.fromtimestamp(statEpochTS)
	statEpoch = (statDate - datetime(1969, 12, 31, 20)).total_seconds()
	statStr = statDate.strftime("%Y-%m-%dT%H:%M:%S")
	ignore = False

	with open(fileName, "r", encoding='utf-8') as file:
		lines = file.readlines()
		
	metaBlock = 0
	firstline = lines[0].strip()
	if firstline == "---":
		for line in lines:
			sline = line.strip()
			if metaBlock < 2:
				if sline == "---":
					metaBlock += 1
				else:
					try:
						match = re.match('^(.*?): (.*)', sline)
						field = match.group(1)
						value = match.group(2)
						# print("FIELD:", "["+field+"]\t"+"VALUE:", "["+value+"]")
						try:
							if field == "modified":
								yamlStr = value
								yamlDate = datetime.strptime(yamlStr, "%Y-%m-%dT%H:%M:%S")
								yamlEpoch = (yamlDate - datetime(1969, 12, 31, 20)).total_seconds() +3600
								if yamlStr == statStr:
									ignore = True
									print("\tmetadata already correct!")
									if v == True:
										print("\tyamlStr:", yamlStr)
										print("\tstatStr:", statStr)
									# print("\tyamlEpoch:", yamlEpoch)
									# print("\tstatEpoch:", statEpoch)
								else:
									print("\tupdating system metadata for",fileName)
									print("\tfrom ["+str(statStr)+"] to ["+str(yamlStr)+"]...")
									if v == True:
										print("\tyamlStr:", yamlStr)
										print("\tstatStr:", statStr)
										print("\tyamlDate:", yamlDate)
										print("\tstatDate:", statDate)
										print("\tyamlEpoch:", yamlEpoch)
										print("\tstatEpoch:", statEpoch)
									os.utime(fileName, (yamlEpoch,yamlEpoch))
									file.close()
						except Exception as e:
							print(colors.red+"(fixmeta1)", fileName, "ERROR:",str(e)+colors.endc)
							print("                  line ignored: ["+sline+"] due to error")
					except Exception as e:
						pass
						# print("cannot parse metadata line: ["+sline+"]")
	else:
		print(colors.red+"(fixmeta2)", fileName, "ERROR: no YAML metadata block detected!"+colors.endc)
		print(colors.red+"                  first line: ["+firstline+"]"+colors.endc)
		print(colors.red+"                  (metadata block must must begin & end with \"---\"), and start on the first line of the file."+colors.endc)
		ignore = True

	if ignore == True:
		if v == True:
			print("file untouched.")


def updatemeta(filePath, searchField, valNew, sizeCheck=True, insert=False, dryrun=False, v=False, report=False, listVals=False, appendList=True, ext="md"):
	print(colors.purple+"UPDATEMETA"+colors.endc)
	insert = bool(insert)
	fileName = os.path.basename(filePath)
	print("filename:", fileName)
	if ext != "all" and filePath.endswith("."+ext) == False:
		print(colors.yellow+fileName+":", "extension is not", ext+"."+colors.endc)
		print(fileName+":", colors.green+"original file untouched."+colors.endc)
		print(endline)
		return "extskip"
	if dryrun == True:
		print("DRY RUN")
	result = "none"
	ignore = False
	if listVals == False:
		newLine = searchField+": "+valNew+"\n"
	else:
		newLine = searchField+":\n  - "+valNew+"\n"

	if os.path.isfile(filePath) == True:
		fileMod = os.stat(filePath).st_mtime
	else:
		print(colors.yellow+fileName+":", "not found!"+colors.endc)
		if insert == True and dryrun == False:
			fileMod = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
			creLine = "created: "+fileMod+"\n"
			modLine = "modified: "+fileMod+"\n"
			with open(filePath, "wb") as file:
				file.write(bytes("---\n", "UTF-8"))
				file.write(bytes(creLine, "UTF-8"))
				file.write(bytes(modLine, "UTF-8"))
				if searchField != "modified" and searchField != "created":
					file.write(bytes(newLine, "UTF-8"))
				file.write(bytes("---\n", "UTF-8"))
				print(endline)
				return "newFile"
		else:
			print(endline)
			return "noFile"


	newFile = filePath+"-tmp"

	with open(filePath, "r", encoding='utf-8') as file:
		try:
			lines = file.readlines()
		except Exception as e:
			print(colors.red+"(updatemeta1)", fileName, "ERROR: ",str(e)+colors.endc)
			lines = [""]
			ignore = True
		
	with open(newFile, "wb") as file:
		fieldFound = False
		listMode = False
		metaBlock = 0
		lineNum = -1
		listEntry = "  - "+valNew+"\n"

		try:
			if len(lines)> 0 and lines[0].strip() == "---":
				for line in lines:
					lineNum += 1
					sline = line.strip()
					if metaBlock < 2:
						if sline == "---":
							metaBlock += 1
							if metaBlock == 2:
								if fieldFound == False:
									print(colors.yellow+fileName+" ["+searchField+"] not found!"+colors.endc)
									if insert == True:
										print(fileName+":", "adding", newLine)
										file.write(bytes(newLine, "UTF-8"))
										result = "addfield"
									else:
										result = "nofield"
										ignore = True
								elif listMode == True:
									file.write(bytes(listEntry, "UTF-8"))
									listMode = False
						else:
							if listMode == True:
								try:
									match = re.match('^  - (.*)', line)
									value = match.group(1)
								except:
									file.write(bytes(listEntry, "UTF-8"))
									print(fileName+":", "added", valNew, "to empty list.")
									listMode = False
									pass
									
							elif listMode == False:	
								try:
									match = re.match('^(.*?): *(.*)', sline)
									field = match.group(1)
									value = match.group(2)
								except:
									pass
									# if v == True:
									# 	print(fileName+":", "cannot parse metadata line: ["+sline+"]")
								
							try:
								if field == searchField or listMode == True:
									fieldFound = True
									print(fileName+":","field found:", field)
									valOld = value
									if valOld == valNew:
										print("match")
										result = "match"
										ignore = True
										print(colors.green+fileName+":", "metadata matches:"+colors.endc, fileName)
										if v == True:
											print("\tvalOld:", valOld)
											print("\tvalNew:", valNew)
										listMode = False
									elif listVals == True or lines[lineNum+1].startswith("  - "):
										print(fileName+":", "LISTMODE")
										listMode = True
									else:
										result = "diff"
										if listVals == False and listMode == False:
											print(colors.yellow+fileName+":", "updating ["+field+"] in",fileName+colors.endc)
											print(fileName+":", "from ["+valOld+"] to ["+valNew+"]...")
											line = re.sub(rf"^{field}: {valOld}", rf"{field}: {valNew}", line)
										elif appendList == False and lines[lineNum+1].startswith("  - ") == False:
											line = re.sub(rf"^  - {valOld}", rf"  - {valNew}", line)
										else:
											file.write(bytes(line, "UTF-8"))
											line = listEntry
											print(fileName+":", "appending", valNew, "to end of list.")
											listMode = False
										# else:
										# 	print(colors.yellow+"metadata does mot match:"+colors.endc, fileName)
										# 	print("\tvalOld:", valOld)
										# 	print("\tvalNew:", valNew)

							except Exception as e:
								print(colors.red+"(updatemeta2)", fileName, "ERROR: ",str(e)+colors.endc)

							field = ""
						
					file.write(bytes(line, "UTF-8"))
					# file.write(line)

			else:
				print(colors.yellow+fileName+":", "no YAML metadata block detected!"+colors.endc)
				if insert == True:
					tsCre = getts(filePath, style="o", mode="cre")
					tsMod = getts(filePath, style="o", mode="mod")
					creLine = "created: "+tsCre+"\n"
					modLine = "modified: "+tsMod+"\n"
					file.write(bytes("---\n", "UTF-8"))
					file.write(bytes(creLine, "UTF-8"))
					file.write(bytes(modLine, "UTF-8"))
					if searchField != "modified" and searchField != "created":
						file.write(bytes(newLine, "UTF-8"))
					file.write(bytes("---\n", "UTF-8"))
					for line in lines:
						file.write(bytes(line, "UTF-8"))
					sizeCheck = False
					result = "addYAML"
				else:
					result = "noYAML"
					ignore = True
				# print("                     first line: ["+firstline+"]")
				# print("                     (metadata block must must begin & end with \"---\"), and start on the first line of the file.")
		except Exception as e:
			# print("(updatemeta4) ERROR: file appears to be empty.")
			print(colors.red+"(updatemeta4)", fileName, "ERROR: ",str(e)+colors.endc)
			ignore = True
			
	if sizeCheck == True and ignore == False:
		origSize = os.stat(filePath).st_size
		newSize = os.stat(newFile).st_size

		print("SIZE CHECK:",origSize," (original file) ->",newSize,"(updated file)")
		if origSize == newSize:
			print(colors.green+fileName+":", "no errors detected."+colors.endc)
		else:
			print(colors.red+"(updatemeta5)", fileName, "ERROR: new file is not the same size as original file. (",origSize,"->",newSize,")"+colors.endc)
			ignore = True
	
	if ignore == True or dryrun == True:
		if v == True:
			print(fileName+":", colors.green+"original file untouched."+colors.endc)
	else:
		print(fileName+":", "updating original ...")
		shutil.copyfile(newFile, filePath)
		os.utime(filePath, (fileMod,fileMod))

	try:
		if v == True:
			print("cleaning up...")
		shutil.copy(os.path.join(os.getcwd(),newFile),"C:/Users/Rose/Sync/coding/projects/obsDB/bkp-tmp/")
		os.remove(os.path.join(os.getcwd(),newFile))
	except Exception as e:
		print(colors.red+"(updatemeta6)", fileName, "ERROR: ",str(e)+colors.endc)
		os.remove(os.path.join(os.getcwd(),newFile))
	
	print(endline)

	if report == True:
		return result


# Update "modified" field in file's yaml metadata
def updatemod(filePath, insert=False):
	updatemeta(filePath, "modified", getts(filePath, "o"), v=True, insert=insert)


# metautils.py modcheck S False
def modcheck(colored="c", mode="a", separator="s", diffchars="x", retmode="print"):
	# print(colors.purple+"MODCHECK"+colors.endc)
	# print("colored: ["+colored+"]")
	# print("mode: ["+mode+"]")
	# print("separator: ["+str(separator)+"]")
	# print("diffchars: ["+str(diffchars)+"]")
	repo = git.Repo()
	chglist = []
	if colored == "c":
		addc = colors.green
		modc = colors.yellow
		rnac = colors.blue
		delc = colors.red
		endc = colors.endc
	else:
		addc = ""
		modc = ""
		rnac = ""
		delc = ""
		endc = ""

	if mode == "s" or mode == "a":
		staged = repo.git.diff(name_status=True, cached=True).split('\n')
		for line in staged:
			chglist.append(line)
	if mode == "us" or mode == "a":
		unstaged = repo.git.diff(name_status=True).split('\n')
		for line in unstaged:
			chglist.append(line)
	if mode == "ut" or mode == "us" or mode == "a":
		untracked = repo.git.ls_files(others=True, exclude_standard=True).split('\n')
		for line in untracked:
			if line != "":
				line = "A\t"+line
				chglist.append(line)
	
	chglist = [i for i in chglist if i]
	# print(chglist)
	filelist = []
	for line in chglist:
		[ prefix, *path ] = line.split('\t')

		try:
			if prefix == "A" or prefix == "M":
				timestamp = getts(path[0], 'h')
				gitstamp = getts(path[0],"g")
				if prefix == "A":
					label = gitstamp+addc+" "+timestamp+" "+prefix+" "+path[0]+endc

				elif prefix == "M":
					if diffchars != "x":
						# print("DIFFCHARS")
						plus = 0
						neg = 0
						mdiff = repo.git.diff(path[0])
						for line in mdiff.split('\n'):
							if re.match('^+[^+]', line):
								plus += len(line)
							elif re.match('^-[^-]', line):
								neg += len(line)
						difflen = plus - neg
						label = gitstamp+modc+" "+timestamp+" "+prefix+" "+path[0]+endc+"\t"+str(difflen)
					else:
						label = gitstamp+modc+" "+timestamp+" "+prefix+" "+path[0]+endc

			if prefix == "R100":
				#                      YYYY-MM-DD HH:MM:SS.mmmmmm  DD MMM YYYY HH:MM:SS AM WWW R
				label = rnac+"                       (renamed)                        "+prefix+" "+path[0]+" -> "+path[1]+endc

			if prefix == "D":
				#                    2023-07-13 10:43:22.799047  13 Jul 2023 10:43:22 AM Thu D
				label = delc+"                       (deleted)                        "+prefix+" "+path[0]+endc
			
			filelist.append(label)
			# print("appending: ["+label+"]")
				
		except:
			print(colors.red+"(modcheck) ERROR: ["+line+"]"+colors.endc)
			print(colors.red+"           prefix: ["+prefix+"]"+colors.endc)
			print(colors.red+"           path: ["+str(path)+"]"+colors.endc)

	filelist.sort()

	if retmode == "print":
		if separator != "x":
			# lastDate = [ line[:10] for line in str(filelist[0]) ]
			# print("["+str(filelist)+"]")
			try:
				lastDate = filelist[0][:10]
				for line in filelist:
					date = line[:10]
					if date != lastDate:
						print("---------------------------------------------------------")
						# print("_______________________________________________________\n")
					print(line)
					lastDate = date
			except:
				pass
		else:
			# print("else")
			for line in filelist: print(line)
	else:
		return filelist
		

# metautils.py gitadd gitlist False
def gitadd(addfile, listmode=True, yamlupdate=True, usedate="last", report=False):
	print(colors.purple+"GITADD"+colors.endc)
	repo = git.Repo()
	commitdate = ""
	result = ""

	if listmode == True:
		with open(addfile, "r") as addLines:
			addlist = addLines.readlines()
	else:
		chglistStaged = modcheck(mode="s", colored="x", retmode="ret")
		chglistUnstaged = modcheck(mode="us", colored="x", retmode="ret")
		found = False
		fileEntry = "-"

		for entry in chglistStaged:
			if entry.startswith("-----") == False and entry.endswith(" "+addfile) and found == False:
				fileEntry = entry
				print(colors.yellow+addfile+": already-staged changes found."+colors.endc)
				print(colors.green+addfile+": leaving file & git stage untouched."+colors.endc)
				result = "staged"
				found = True
			else:
				pass
		
		for entry in chglistUnstaged:
			if entry.startswith("-----") == False and entry.endswith(" "+addfile) and found == False:
				fileEntry = entry
				print(colors.yellow+"unstaged changes to", addfile, "found..."+colors.endc)
				result = "unstaged"
				found = True
			else:
				pass

		if found == False:		
			print(colors.yellow+addfile+": no changes found."+colors.endc)
			result = "none"

		addlist = [fileEntry]

	# with open(addfile, "r") as addlist:
	for entry in addlist:
		if entry.startswith("-") == False:
			try:
				filepath = entry[58:].strip()

				if yamlupdate == True:
					updatemod(filepath)
				
				if result != "staged":
					repo.git.add(filepath)
					print("staged file: ["+filepath+"]")

				if ((usedate == "first" or usedate == "1st" or usedate == "1") and commitdate == "") or usedate == "last":
					commitdate = entry[:26].strip()

			except Exception as e:
				print(colors.red+"(gitadd)", addfile, "ERROR: ",str(e)+colors.endc)
				print("         skipped line:", entry.strip())
				result = "error"

	if listmode == True:
		print("git commit", "-t ", addfile, "--date=\""+commitdate+"\"")
	elif result != "none":
		print("git commit --date=\""+commitdate+"\"")
	
	print(endline)
	if report == True:
		return result

def gitcomm(usedate="last"):
	commitdate = ""
	stagecheck = modcheck(mode="s", colored="", retmode="ret")
	for entry in stagecheck:
		try:
			if ((usedate == "first" or usedate == "1st" or usedate == "1") and commitdate == "") or usedate == "last":
				commitdate = entry[:26].strip()

		except Exception as e:
			print(colors.red+"(gitcomm) ERROR: ",str(e)+colors.endc)
			print("         skipped line:", entry.strip())
			print()

	print("git commit", "--date=\""+commitdate+"\"")


# while read line; do echo $line | cut -c 56- ; done < gitlist | while read line ; do git add $line ; done

if __name__ == "__main__":
	args = sys.argv
	# args[0] = current file
	# args[1] = function name
	# args[2:] = function args : (*unpacked)
	globals()[args[1]](*args[2:])