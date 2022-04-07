import os #lets you search folders
from moviepy.editor import * #lets you edit videos

debugging = False #when true, prints timestamp and clip lists

SLOW_OR_AIM_SPEED = .20 #how much slow mo or aim slow down the game
FAST_SPEED = 6.00 #how much fast mo or speeds up the game

leaveFastMo = True #when true, doesn't slow down fast mo


inVidExt = ".mov" #extension of the input file
inVidName = "" #name of the input file
inVid = None #the input video clip
outVidExt = ".mp4" #extension of the output file

try:
    inVidName = [_ for _ in os.listdir(os.getcwd()) if _.endswith(inVidExt)][0] #use the first file with a matching extension
    inVid = VideoFileClip(inVidName) #get input clip
    inVid = inVid.without_audio() #remove audio from input clip

except IndexError: #if capture wasn't found
    print("Capture not found") #break the news
    exit()

raw = "" #raw text input

print("\nPaste Log Output ") #prompt user
while(True):
    line = input() #take in line
    raw += line #add line to raw input 
    #if line has the end of the list, stop reading
    if("]]" in line):
        break


oneLine = raw.replace("[Unknown Script] ", "") #get rid of any log text
split = oneLine.split("], [") #separate strings by sublist
inp = [split[0][2:]] + split[1:5] + [split[5][:-2]] #put sublists together in list

allTimes = [] #all times in final (float) form
for i in range(0, len(inp)): #iterate through the 6 timestamp lists
    times = inp[i].split(", ") #separate timestamp strings
    if(len(times) > 1): 
        for j in range(0, len(times)):
            times[j] = float(times[j]) #convert timestamp from string to float
    else:
        times = [] #leave list blank
    allTimes.append(times) #add timestamp list to list of timestamp lists

#decoded timestamp lists
recTimes = allTimes[0]
stopTimes = allTimes[1]
throwTimes = allTimes[2]
slowTimes = allTimes[3]
aimTimes = allTimes[4]
fastTimes = allTimes[5]

#print lists if debugging
if(debugging):
    print("")
    print("R: " + str(recTimes))
    print("P: " + str(stopTimes))
    print("T: " + str(throwTimes))
    print("S: " + str(slowTimes))
    print("A: " + str(aimTimes))
    print("F: " + str(fastTimes))
    print()

allClips = [] #all clips that will be concatenated

#add skipped and/or edited segments to list
#HERE__________________ 

#add pause clips (third variable, the actual clip, omitted so it can be skipped later)
for i in range(0, len(stopTimes), 2):
    allClips.append([stopTimes[i]-.05, stopTimes[i+1]+.05])

#add throw clips (third variable, the actual clip, omitted so it can be skipped later)
for i in range(0, len(throwTimes), 2):
    allClips.append([throwTimes[i]-.02, throwTimes[i+1]+.02])

#add sped-up slow clips
for i in range(0, len(slowTimes), 2):
    clip = inVid.subclip(slowTimes[i], slowTimes[i+1])
    clip = clip.fx(vfx.speedx, 1/SLOW_OR_AIM_SPEED)
    allClips.append([slowTimes[i], slowTimes[i+1], clip])
  
#add sped-up aim clips  
for i in range(0, len(aimTimes), 2):
    clip = inVid.subclip(aimTimes[i], aimTimes[i+1])
    clip = clip.fx(vfx.speedx, 1/SLOW_OR_AIM_SPEED)
    allClips.append([aimTimes[i], aimTimes[i+1], clip])

#if not leaving fast clips alone add them slowed down   
if(not leaveFastMo):
    for i in range(0, len(fastTimes), 2):
        clip = inVid.subclip(fastTimes[i], fastTimes[i+1])
        clip = clip.fx(vfx.speedx, 1/FAST_SPEED)
        allClips.append([fastTimes[i], fastTimes[i+1], clip])

#__________________TO HERE

#sort all clips by start timestamp
allClips = sorted(allClips, key=lambda x: x[0])

#print sorted clips if debugging
if(debugging):
    print(str(allClips)+"\n")

#if there are edited clips, add original footage between them
if(len(allClips) >  0):
    allClips.insert(0, [0, allClips[0][0], inVid.subclip(0, allClips[0][0])]) #add original footage from start to first edit
    i = 1
    while i < len(allClips)-1: #while there are pairs of edits
        currEnd = allClips[i][1] #end of current clip
        nextStart = allClips[i+1][0] #start of next clip
        diff = nextStart - currEnd #difference between the two above
        if(diff > 0): #if clips don't intersect
            allClips.insert(i+1, [currEnd, nextStart, inVid.subclip(currEnd, nextStart)]) #add original footage from between the two
            i += 1
        elif(diff < 0): #if clips do intersect...
            if(len(allClips[i]) == 3 and len(allClips[i+1]) == 3): #...and if neither clip is a skip
                allClips[i][2] = allClips[i][2].subclip(0, allClips[i][2].duration-abs(diff/2)) #cut current clip half-way through intersection
                allClips[i+1][2] = allClips[i+1][2].subclip(abs(diff/2), allClips[i+1][2].duration) #start next clip half-way through intersection 
        i += 1
else: #if there are no edited clips
    allClips = [[0, inVid.duration, inVid]] #output the original footage in its entirety

if(len(allClips) >  1): #if there are edited clips
    allClips.append([allClips[-1][1], recTimes[1], inVid.subclip(allClips[-1][1], inVid.duration)]) #add original footage from end of last edit to end of footage

#print list of clips if debugging
if(debugging):
    print(str(allClips)+"\n")

#remove any clips that don't a third element (i.e. they are pauses/throws)
i = 0
while i < len(allClips):
    if(len(allClips[i]) < 3):
        allClips.pop(i)
        i -= 1
    i += 1

#print list of clips if debugging
if(debugging):
    print(str(allClips)+"\n")


outVid = concatenate_videoclips([i[2] for i in allClips]) #combine clips into one
outVid.write_videofile(inVidName+"_out"+outVidExt, fps=60) #output