import os #lets you search folders
from moviepy.editor import * #lets you edit videos

debugging = True

# raw = ""

# print("Paste Log Output ")
# while(True):
#     line = input()
#     raw += line
#     if("]]" in line):
#         break

# SLOW_OR_AIM_SPEED = .2
# FAST_SPEED = 6

# oneLine = raw.replace("[Unknown Script] ", "")
# split = oneLine.split("], [")
# inp = [split[0][2:]] + split[1:5] + [split[5][:-2]]

# recTimes = [inp[0].split(", ")]
# stopTimes = [inp[1].split(", ")]
# throwTimes = [inp[2].split(", ")]
# slowTimes = [inp[3].split(", ")]
# aimTimes = [inp[4].split(", ")]
# fastTimes = [inp[5].split(", ")]
 
# if(debugging):
#     print("R: " + str(recTimes))
#     print("P: " + str(stopTimes))
#     print("T: " + str(throwTimes))
#     print("S: " + str(slowTimes))
#     print("A: " + str(aimTimes))
#     print("F: " + str(fastTimes))

inVidExt = ".mov"
inVidName = [_ for _ in os.listdir(os.getcwd()) if _.endswith(inVidExt)][0]
inVid = VideoFileClip(inVidName)

outVid = inVid.fx(vfx.speedx, .5)

outVid.write_videofile(inVidName+"_out.mp4")