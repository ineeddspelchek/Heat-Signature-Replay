import os #lets you search folders
from moviepy.editor import * #lets you edit videos

debugging = True

SLOW_OR_AIM_SPEED = .20
FAST_SPEED = 6.00

raw = ""

print("Paste Log Output ")
while(True):
    line = input()
    raw += line
    if("]]" in line):
        break


oneLine = raw.replace("[Unknown Script] ", "")
split = oneLine.split("], [")
inp = [split[0][2:]] + split[1:5] + [split[5][:-2]]

allTimes = []
for i in range(0, len(inp)):
    times = inp[i].split(", ")
    if(len(times) > 1):
        for j in range(0, len(times)):
            times[j] = float(times[j])
    else:
        times = []
    allTimes.append(times)

recTimes = allTimes[0]
stopTimes = allTimes[1]
throwTimes = allTimes[2]
slowTimes = allTimes[3]
aimTimes = allTimes[4]
fastTimes = allTimes[5]

if(debugging):
    print("")
    print("R: " + str(recTimes))
    print("P: " + str(stopTimes))
    print("T: " + str(throwTimes))
    print("S: " + str(slowTimes))
    print("A: " + str(aimTimes))
    print("F: " + str(fastTimes))
    print()

inVidExt = ".mov"
try:
    inVidName = [_ for _ in os.listdir(os.getcwd()) if _.endswith(inVidExt)][0]
    inVid = VideoFileClip(inVidName)
    inVid = inVid.without_audio()

    if(len(slowTimes) + len(aimTimes) + len(fastTimes) == 0):
        print("No more edits to make. Pause edits already handled by previous program. No speed edits to do.")
    else: 
        allClips = []
        
        for i in range(0, len(slowTimes), 2):
            clip = inVid.subclip(slowTimes[i], slowTimes[i+1])
            clip = clip.fx(vfx.speedx, 1/SLOW_OR_AIM_SPEED)
            allClips.append([slowTimes[i], slowTimes[i+1], clip])
            
        for i in range(0, len(aimTimes), 2):
            clip = inVid.subclip(aimTimes[i], aimTimes[i+1])
            clip = clip.fx(vfx.speedx, 1/SLOW_OR_AIM_SPEED)
            allClips.append([aimTimes[i], aimTimes[i+1], clip])
            
        for i in range(0, len(fastTimes), 2):
            clip = inVid.subclip(fastTimes[i], fastTimes[i+1])
            clip = clip.fx(vfx.speedx, 1/FAST_SPEED)
            allClips.append([fastTimes[i], fastTimes[i+1], clip])
            
        allClips = sorted(allClips, key=lambda x: x[0])
        
        print(str(allClips)+"\n")
        
        allClips.insert(0, [0, allClips[0][0], inVid.subclip(0, allClips[0][0])])
        
        i = 1
        while i < len(allClips)-1:
            currEnd = allClips[i][1]
            nextStart = allClips[i+1][0]
            diff = nextStart - currEnd
            if(diff > 0):
                allClips.insert(i+1, [currEnd, nextStart, inVid.subclip(currEnd, nextStart)])
                i += 1
            elif(diff < 0):
                allClips[i][2] = allClips[i][2].subclip(0, allClips[i][2].duration-abs(diff/2))
                allClips[i+1][2] = allClips[i+1][2].subclip(abs(diff/2), allClips[i+1][2].duration)
            i += 1
        allClips.append([allClips[-1][1], recTimes[1], inVid.subclip(allClips[-1][1], inVid.duration)]) 
        
        if(debugging):
            print(str(allClips)+"\n")
        
        outVid = concatenate_videoclips([i[2] for i in allClips])
        outVid.write_videofile(inVidName+"_out.mp4", fps=60)
except IndexError:
    print("Capture not moved into folder")