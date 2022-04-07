#note: code doesn't properly handle pause cutting-off slow-mo and fast-mo, but it doesn't matter since the paused chunk just goes unrecorded anyway

import obspython as obs #lets you control obs

from threading import Timer #lets you delay function execution
import time #lets you get current time
from PIL import ImageGrab #lets you take a screenshot to analyze

from pynput import mouse #lets you check mouse clicks and locations
from pynput import keyboard #lets you check key presses
from pynput.keyboard import Key #simplifies access of non-alphanumeric keys
from pynput.keyboard import KeyCode #simplifies access of alphanumeric keys

debugging = False #when True, program prints what's going on to the log 

#---------------------------------------------------------------------------------------------------------------------------
#Constants

REC_KB = KeyCode.from_char('g') #start/stop recording keybind
STOP_KB = Key.space #pause/unpause keybind ("Inventory")
THROW_KB = KeyCode.from_char('t') #throw keybind ("Throw")
SLOW_KB = KeyCode.from_char('r') #slow down time keybind ("Slow Mo")
#AIM_KB too much work to make work because keyboard and mouse are handled differently (and its pretty unlikely anyone changed the default keybind for primary and secondary attack)
FAST_KB = KeyCode.from_char('f') #speed up time keybind ("Fast Mo")

#all buttons (besides STOP_KB and THROW_KB) that take you out of pause (if not already held when pause or throw was pressed) ("Move Up", "Move Left", "Move Down", "Move Right")
UNSTOP_KBs = [KeyCode.from_char('w'),
              KeyCode.from_char('a'),
              KeyCode.from_char('s'),
              KeyCode.from_char('d')]

#keys that need to be logged
importantKeys = [REC_KB, STOP_KB, THROW_KB, SLOW_KB, FAST_KB] + UNSTOP_KBs

#pixel color test coords
pLBarLoc = (174, 24) #one coordinate on the black part of the top-left bar open when paused ("You")
pRBarLoc = (1764, 24) #one coordinate on the black part of the top-right bar open when paused ("Mission")
aBarLoc1 = (207, 140) #top right coordinate on the black part of the "Cancel Aim" bar
aBarLoc2 = (90, 174) #bottom left coordinate on the black part of the "Cancel Aim" bar
fTxtLoc = (69, 1052) #coordinate on the white part of the ">> x6" text

timeAdjusts = [[0, .14], [-.12, -.25], [0, 0], [0, 0], [-.30, -.25], [-.2, -.27]] #how much to add to certain timestamps to account for their inaccuracy; rows - rec, stop, throw, slow, aim, fast; columns - start, end

#---------------------------------------------------------------------------------------------------------------------------
#Setup

kListener = None #creates eventual keyboard listener
mListener = None #creates eventual mouse listener

findingMouseCoords = False #when True, pressing backspace will log mouse location
replayEnabled = False #when True, listeners are on and recording can begin

#partial dictionary that converts strings of (non-alphanumeric) keys to actual keys
keyDict = {
    "alt_l":Key.alt_l, "alt_r":Key.alt_r, "caps_lock":Key.caps_lock, "ctrl_l":Key.ctrl_l, "ctrl_r":Key.ctrl_r, "esc":Key.esc, "shift_l":Key.shift_l, 
    "shift_r":Key.shift_r, "space":Key.space, "tab":Key.tab, "up":Key.up, "down":Key.down, "left":Key.left, "right":Key.right 
}
#adds alphanumeric keys to dictionary
for i in range(97, 122):
    keyDict[chr(i)] = KeyCode.from_char(chr(i))
    
#description that OBS displays
def script_description():
    return """Heat Signature Replay (OBS Script)
        by ineeddspelchek        
        
Bind Info:
        + Alphanumeric Keys: type the letter
        + Space Bar: type 'space'
        + Other: alt_l/alt_r/caps_lock/ctrl_l/ctrl_r/esc/
          shift_l/shift_r/tab/up/down/left/right
        + type unused and hard to reach keys for binds you 
          don't want to set
Coord Info:
        + Format (no apostrophes): 'x,y'
        + Coords for 1920x1080, auto scaling
            + 174,24; 1764,24; 207,140; 90,174; 69,1052 
        + 'Finding Coords' will make backspace paste current 
          cursor coords to the log while replay enabled (and 
          then color at location after 1 second; pasted color 
          will be the cursor's color if mouse not moved away 
          before 1 second) 
            + 'Not Finding Coords' disables it
        + color for first four coords should be (0, 0, 0)
        + color for last should be (255, 255, 255)

*DON'T CHANGE ANY VALUES WHILE RECORDING 
 (will disable replay and reset recording)"""

#adds pathbox, textboxes and buttons to script window
def script_properties():
    props = obs.obs_properties_create()
    
    #obs.obs_properties_add_path(props, "capPath", "Capture Folder", obs.OBS_PATH_DIRECTORY, "", None)
    
    obs.obs_properties_add_button(props, "enable", "Enable Replay", enable)
    obs.obs_properties_add_button(props, "disable", "Disable Replay", disable)
    obs.obs_properties_add_button(props, "enable_c", "Finding Coords", enable_coords)
    obs.obs_properties_add_button(props, "disable_c", "Not Finding Coords", disable_coords)
    
    obs.obs_properties_add_text(props, "recKB", "Record Keybind", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "stopKB", "Inventory Keybind", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "throwKB", "Throw Keybind", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "slowKB", "Slow Mo Keybind", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "fastKB", "Fast Mo Keybind", obs.OBS_TEXT_DEFAULT)
    
    obs.obs_properties_add_text(props, "muKB", "Move Up Keybind", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "mlKB", "Move Left Keybind", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "mdKB", "Move Down Keybind", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "mrKB", "Move Right Keybind", obs.OBS_TEXT_DEFAULT)
    
    obs.obs_properties_add_text(props, "pLBarLoc", "Coord on black part of 'You' box (seen in top left when paused)", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "pRBarLoc", "Coord on black part of 'Mission' box (seen in top right when paused)", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "aBarLoc1", "Top Right Coord on black part of 'Cancel Aim' box (seen when aiming)", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "aBarLoc2", "Bottom Left coord on black part of 'Cancel Aim' box (seen when aiming)", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "fTxtLoc", "Coord on the white part of the '>> x6' text (seen when fast mo)", obs.OBS_TEXT_DEFAULT)
    
    return props

#called whenever script window elements are interacted with 
def script_update(settings):
    global recording, REC_KB, STOP_KB, THROW_KB, SLOW_KB, FAST_KB, UNSTOP_KBs, importantKeys
    
    if(not recording):
        #change Keybind constants to those currently in script window textboxes
        try:
            REC_KB = keyDict[obs.obs_data_get_string(settings, "recKB")]
        except:
            pass
        try:
            STOP_KB = keyDict[obs.obs_data_get_string(settings, "stopKB")]
        except:
            pass
        try:
            SLOW_KB = keyDict[obs.obs_data_get_string(settings, "slowKB")]
        except:
            pass
        try:
            FAST_KB = keyDict[obs.obs_data_get_string(settings, "fastKB")]
        except:
            pass
        try:
            THROW_KB = keyDict[obs.obs_data_get_string(settings, "throwKB")]
        except:
            pass
        
        try:
            UNSTOP_KBs[0] = keyDict[obs.obs_data_get_string(settings, "muKB")]
        except:
            pass
        try:
            UNSTOP_KBs[1] = keyDict[obs.obs_data_get_string(settings, "mlKB")]
        except:
            pass
        try:
            UNSTOP_KBs[2] = keyDict[obs.obs_data_get_string(settings, "mdKB")]
        except:
            pass
        try:
            UNSTOP_KBs[3] = keyDict[obs.obs_data_get_string(settings, "mrKB")]
        except:
            pass
        
        try:
            coords = obs.obs_data_get_string(settings, "pLBarLoc").split(",")
            pLBarLoc = (int(coords[0]), int(coords[1]))
        except:
            pass
        try:
            coords = obs.obs_data_get_string(settings, "pRBarLoc").split(",")
            pRBarLoc = (int(coords[0]), int(coords[1]))
        except:
            pass
        try:
            coords = obs.obs_data_get_string(settings, "aBarLoc1").split(",")
            aBarLoc1 = (int(coords[0]), int(coords[1]))
        except:
            pass
        try:
            coords = obs.obs_data_get_string(settings, "aBarLoc2").split(",")
            aBarLoc2 = (int(coords[0]), int(coords[1]))
        except:
            pass
        try:
            coords = obs.obs_data_get_string(settings, "fTxtLoc").split(",")
            fTxtLoc = (int(coords[0]), int(coords[1]))
        except:
            pass
    
        #change what keys now need to be logged
        importantKeys = [REC_KB, STOP_KB, THROW_KB, SLOW_KB, FAST_KB] + UNSTOP_KBs
    else: #if values changed while recording, reset the script
        obs.obs_frontend_recording_stop() #makes obs stop recording
        kListener.stop() #kills the keyboard listener
        mListener.stop() #kills the mouse listener
        
        #resets various values
        baseTime = 0
        recording = False
        paused = False
        throwing = False
        wasThrowing = False
        slow = False
        aiming = False
        fast = False
        heldKeys = []
        heldButtons = [False, False]
        recTimes = []
        stopTimes = []
        throwTimes = []
        slowTimes = []
        aimTimes = []
        fastTimes = []
        
        replayEnabled = False

def enable(props, prop): #called when "Enable Replay" pressed
    global replayEnabled, kListener, mListener, baseTime, recording, paused, throwing, wasThrowing, slow, aiming, fast, recTimes, stopTimes, throwTimes, slowTimes, aimTimes, fastTimes, heldKeys, heldButtons
    
    if(not replayEnabled):
        #starts keyboard listener
        kListener = keyboard.Listener(on_press=on_press, on_release=on_release) #keyboard listener (not started yet)
        kListener.start()

        #starts mouse listener
        mListener = mouse.Listener(on_click=on_click) #mouse listener (not started yet)
        mListener.start()
        
        #resets various values
        baseTime = 0
        recording = False
        paused = False
        throwing = False
        wasThrowing = False
        slow = False
        aiming = False
        fast = False
        heldKeys = []
        heldButtons = [False, False]
        recTimes = []
        stopTimes = []
        throwTimes = []
        slowTimes = []
        aimTimes = []
        fastTimes = []
        
        replayEnabled = True
    
def disable(props, prop): #called when "Disable Replay" pressed
    global replayEnabled, kListener, mListener, baseTime, recording, paused, throwing, wasThrowing, slow, aiming, fast, recTimes, stopTimes, throwTimes, slowTimes, aimTimes, fastTimes, heldKeys, heldButtons
    
    if(replayEnabled):
        obs.obs_frontend_recording_stop() #makes obs stop recording
        
        kListener.stop() #kills the keyboard listener
        mListener.stop() #kills the mouse listener
        
        #resets various values
        baseTime = 0
        recording = False
        paused = False
        throwing = False
        wasThrowing = False
        slow = False
        aiming = False
        fast = False
        heldKeys = []
        heldButtons = [False, False]
        recTimes = []
        stopTimes = []
        throwTimes = []
        slowTimes = []
        aimTimes = []
        fastTimes = []
        
        replayEnabled = False
    
def enable_coords(props, prop): #called when "Finding Coords" pressed
    global findingMouseCoords
    
    findingMouseCoords = True
    
def disable_coords(props, prop): #called when "Not Finding Coords" pressed
    global findingMouseCoords
    
    findingMouseCoords = False
    

#---------------------------------------------------------------------------------------------------------------------------
#Key and Gamestate Logging

baseTime = 0 #time recording starts

recording = False #is obs currently recording (pausing still counts as recording)
paused = False #is the recording currently paused
throwing = False #is the player currently throwing
wasThrowing = False #was the player throwing but a slow-mo press unpaused the game
slow = False #is the game currently in slow mo
aiming = False #is the player currently aiming (without fast-mo; "currently in aiming speed" is more accurate)
fast = False #is the game currently in slow mo

heldKeys = [] #all important keys currently held down
heldButtons = [False, False] #whether left and right mouse buttons are held down

#lists of timestamps of when each key was pressed
recTimes = []
stopTimes = []
throwTimes = []
slowTimes = []
aimTimes = []
fastTimes = []

#when a key is pressed
def on_press(key):    
    global baseTime, recording, paused, throwing, wasThrowing, slow, aiming, fast, recTimes, stopTimes, throwTimes, slowTimes, aimTimes, fastTimes, heldKeys
    
    #if backspace hit while looking for mouse coords, print current cursor position and then color at position after a pause
    if(findingMouseCoords and key == Key.backspace):
        m = mouse.Controller()
        pos = m.position
        print("mouse position "+str(pos))
        time.sleep(1)
        image = ImageGrab.grab() #takes a screenshot
        print("color at "+str(pos)+": "+str(image.getpixel(pos)))
    
    if(key == REC_KB and not key in heldKeys): #if record key was pressed and wasn't held already
        if(not recording):
            baseTime = time.time() #sets record start time
            recTimes.append(0) #adds start time to (empty) timestamp list
            recording = True
            obs.obs_frontend_recording_start() #makes obs start recording
            if(debugging):
                print("R")
        else:
            recTimes.append(time.time()-baseTime+timeAdjusts[0][1]) #adds end time to (now 2 long) record press timestamp list
            if(paused):
                stopTimes.append(time.time()-baseTime+timeAdjusts[1][1]) #adds unpause time to timestamp list
            recording = False
            obs.obs_frontend_recording_stop() #makes obs stop recording
            if(debugging):
                print("--R--")
                
            #prints timestamps to log which is then pasted into the second python program (as a log line can only hold 2047 characters, and the "[Unknown Script] " text brings it down to 2030, the output is cut up into lines of 2000)
            out = str([recTimes, stopTimes, throwTimes, slowTimes, aimTimes, fastTimes])
            for i in range(0, int(len(out)/2000)+1):
                print(out[i*30:(i+1)*2000])
                
            print("\n")
            
            #resets various values
            baseTime = 0
            recording = False
            paused = False
            throwing = False
            wasThrowing = False
            slow = False
            aiming = False
            fast = False
            heldKeys = []
            heldButtons = [False, False]
            recTimes = []
            stopTimes = []
            throwTimes = []
            slowTimes = []
            aimTimes = []
            fastTimes = []

    if(recording):
        if(key == STOP_KB and not key in heldKeys): #if pause key was pressed and it wasn't held already
            if(not paused):
                stopTimes.append(time.time()-baseTime+timeAdjusts[1][0]) #adds pause time to timestamp list
                paused = True
                if(debugging):
                    print("P")

                wasThrowing = False
                if(throwing): #if was throwing when pause happened
                    throwTimes.append(time.time()-baseTime+timeAdjusts[2][1]) #adds throw end to timestamp list (same as throw start when pausing taken into account)
                    throwing = False
                    if(debugging):
                        print("--T--")
                if(slow): #if was slow-mo when pause happened
                    slowTimes.append(time.time()-baseTime+timeAdjusts[3][1]) #adds slow-mo end to timestamp list
                    slow = False
                    if(debugging):
                        print("--S--")
                if(aiming): #if was aiming when pause happened
                    aimTimes.append(time.time()-baseTime+timeAdjusts[4][1]) #adds aiming end to timestamp list
                    aiming = False
                    if(debugging):
                        print("--A--")
                if(fast): #if was fast-mo when pause happened
                    fastTimes.append(time.time()-baseTime+timeAdjusts[5][1]) #adds fast mo end to timestamp list
                    fast = False
                    if(debugging):
                        print("--F--")
            else:
                uTimer = Timer(.05, checkIfPaused) #set up delayed "unpause" check
                uTimer.start() #start 50ms timer till "unpause" check called
                                    
        
        elif(key == THROW_KB and not key in heldKeys): #if throw key was pressed and it wasn't held already
            if(not throwing):
                if(paused):
                    #check if throw "unpaused" game
                    uTimer = Timer(.05, checkIfPaused) #set up delayed "unpause" check
                    uTimer.start() #start 50ms timer till "unpause" check called
                    
                    #check if throwing (delayed to happen after the "unpause" unpauses the recording)
                    tTimer = Timer(.2, checkIfThrowing) #set up delayed throw check
                    tTimer.start() #start 200ms timer till throwPause called
                else:
                    throwTimes.append(time.time()-baseTime+timeAdjusts[2][0]) #adds throwing start to timestamp list
                    throwing = True
                    if(debugging):
                        print("T")
                
            else:
                throwTimes.append(time.time()-baseTime+timeAdjusts[2][1]) #adds throw end to timestamp list (same as throw start when pausing taken into account)
                throwing = False
                if(debugging):
                    print("--T--")
        elif(not slow and key == SLOW_KB and not key in heldKeys and not fast and not aiming): #if slow-mo key pressed and it wasn't held already
            slowTimes.append(time.time()-baseTime+timeAdjusts[3][0]) #adds slow-mo start to timestamp list
            slow = True
            if(debugging):
                print("S")
            if(throwing): #if was throwing before slow mo press
                throwTimes.append(time.time()-baseTime+timeAdjusts[2][1]) #adds throw end to timestamp list (same as throw start when pausing taken into account)
                throwing = False
                wasThrowing = True
                if(debugging):
                    print("--T--")
        elif(not fast and key == FAST_KB and not key in heldKeys): #if fast-mo key pressed and it wasn't held already
            fTimer = Timer(.3, checkIfFast) #set up delayed fast mo check
            fTimer.start() #start 300ms timer till fast mo check called
            
    if(key in UNSTOP_KBs and not key in heldKeys): #key that unpauses/unthrows was pressed and it wasn't held already
        if(throwing):
            throwTimes.append(time.time()-baseTime+timeAdjusts[2][1]) #adds throw end to timestamp list (same as throw start when pausing taken into account)
            throwing = False
            if(debugging):
                print("--T--")
        elif(paused):
            uTimer = Timer(.05, checkIfPaused) #set up delayed pause check
            uTimer.start() #start 50ms timer till pause check called
        
    if(not key in heldKeys and key in importantKeys): #if pressed key is important and it isn't already considered held
        heldKeys.append(key) #consider it held
        #print(heldKeys)

    #when a key is released
def on_release(key): 
    global baseTime, slow, throwing, wasThrowing, fast, throwTimes, slowTimes, fastTimes
    
    if(slow and key == SLOW_KB): #if slow-mo key released while in slow-mo
        slowTimes.append(time.time()-baseTime+timeAdjusts[3][1]) #adds slow-mo end to timestamp list
        slow = False
        if(debugging):
            print("--S--")
        if(wasThrowing): #was throwing before slow-mo unfroze game
            throwTimes.append(time.time()-baseTime+timeAdjusts[2][0]) #adds throwing start to timestamp list
            throwing = True
            wasThrowing = False
            if(debugging):
                print("T")
    elif(fast and key == FAST_KB): #if fast-mo key released while in fast-mo
        fTimer = Timer(.1, checkIfFast) #set up delayed fast mo check
        fTimer.start() #start 100ms timer till fast mo check called
        
    if(key in heldKeys): #if unpressed key is considered held
        heldKeys.remove(key) #consider it unheld
        #print(heldKeys)


#when the mouse is pressed or released
def on_click(x, y, button, pressed):
    global baseTime, paused, throwing, throwTimes, heldButtons

    if(recording):
        if(button == mouse.Button.left): #if left click pressed or released
            uTimer = Timer(.05, checkIfPaused) #set up delayed pause check
            uTimer.start() #start 50ms timer till pause check called
            
            aTimer = Timer(.05, checkIfAiming) #set up delayed aim check
            aTimer.start() 
            
            if(not paused): 
                #check if click will start aiming after a reload
                aTimer = Timer(0.5, checkAimingRepeat) #set up delayed repeating aim check
                aTimer.start() #start delayed check

            if(pressed): #if left click pressed
                heldButtons[0] = True
            else: #if left click released
                heldButtons[0] = False
        elif(button == mouse.Button.right): #if right click pressed or released   
            uTimer = Timer(.05, checkIfPaused) #set up delayed pause check
            uTimer.start() #start 50ms timer till pause check called
            
            if(not paused): 
                #check if click started/ended aiming
                aTimer = Timer(.05, checkIfAiming) #set up delayed aim check
                aTimer.start() #start 50ms timer till aim check called 
                                
            if(pressed): #if right click pressed
                heldButtons[1] = True
            else: #if right click released
                heldButtons[1] = False
                
        if(throwing and not pressed): #if was throwing and mouse press released
            throwTimes.append(time.time()-baseTime+timeAdjusts[2][1]) #adds throw end to timestamp list (same as throw start when pausing taken into account)
            throwing = False
            if(debugging):
                print("--T--")

#checks if game paused/unpause
def checkIfPaused():
    global baseTime, paused, throwing, wasThrowing, slow, aiming, fast, stopTimes, throwTimes, slowTimes, aimTimes, fastTimes
    
    image = ImageGrab.grab() # take a screenshot
    if(image.getpixel(pLBarLoc) != (0, 0, 0) and image.getpixel(pRBarLoc) != (0, 0, 0)): #if two test points are not black meaning you've unpaused
        if(paused): #if not yet considered unpaused
            stopTimes.append(time.time()-baseTime+timeAdjusts[1][1]) #adds unpause time to timestamp list
            paused = False        
            if(debugging):
                print("--P--")
            
            if(not fast and FAST_KB in heldKeys): #if fast-mo key was held while paused and it is still being held 
                fastTimes.append(time.time()-baseTime+timeAdjusts[5][0]) #adds fast-mo start to timestamp list
                fast = True
                if(debugging):
                    print("F")
            elif(not slow and SLOW_KB in heldKeys): #if slow-mo key was held while paused and it is still being held (elif because fast-mo overrides slow-mo)
                slowTimes.append(time.time()-baseTime+timeAdjusts[3][0]) #adds slow-mo start to timestamp list
                slow = True
                if(debugging):
                    print("S")
            
            if(not aiming and heldButtons[0] or heldButtons[1]): #if left or right click was held while paused and it is still being held
                aimTimes.append(time.time()-baseTime+timeAdjusts[4][0]) #adds aiming start to timestamp list
                aiming = True
                if(debugging):
                    print("A")
                
    else: #paused
        if(not paused): #if not yet considered paused
            stopTimes.append(time.time()-baseTime+timeAdjusts[1][0]) #adds pause time to timestamp list
            paused = True
            if(debugging):
                print("P")

        wasThrowing = False
        if(throwing): #if was throwing when pause happened
            throwTimes.append(time.time()-baseTime+timeAdjusts[2][1]) #adds throw end to timestamp list (same as throw start when pausing taken into account)
            throwing = False
            if(debugging):
                print("--T--")
        if(slow): #if was slow-mo when pause happened
            slowTimes.append(time.time()-baseTime+timeAdjusts[3][1]) #adds slow-mo end to timestamp list
            slow = False
            if(debugging):
                print("--S--")
        if(aiming): #if was aiming when pause happened
            aimTimes.append(time.time()-baseTime+timeAdjusts[4][1]) #adds aiming end to timestamp list
            aiming = False
            if(debugging):
                print("--A--")
        if(fast): #if was fast-mo when pause happened
            fastTimes.append(time.time()-baseTime+timeAdjusts[5][1]) #adds fast mo end to timestamp list
            fast = False
            if(debugging):
                print("--F--")
                
#checks if player throwing (used because pressing t while hovering over an inventory menu element, it doesn't actually make you throw)
def checkIfThrowing():
    global baseTime, timeAdjusts, throwing, throwTimes
    
    image = ImageGrab.grab() #takes a screenshot
    if(not throwing and image.getpixel(aBarLoc1) == (0, 0, 0) and image.getpixel(aBarLoc2) == (0, 0, 0)):
        throwTimes.append(time.time()-baseTime+timeAdjusts[2][0]) #adds throwing start to timestamp list
        throwing = True
        if(debugging):
            print("T")
        
#checks if player aiming
def checkIfAiming():
    global baseTime, timeAdjusts, aiming, aimTimes, slow, fast, slowTimes
    
    image = ImageGrab.grab() #takes a screenshot
    if(image.getpixel(aBarLoc1) == (0, 0, 0) and image.getpixel(aBarLoc2) == (0, 0, 0) and not fast and not throwing): #if two test points are black meaning you're at aiming speed (so long as you aren't in fast-mo or throwing) (can false positive on the rare occasion that you are paused and hovering over the first inventory slot and the cursor border is over the lower coord)
        if(not aiming): #if you weren't aiming already
            aimTimes.append(time.time()-baseTime+timeAdjusts[4][0]) #adds aiming start time to timestamp list
            aiming = True
            if(debugging):
                print("A")
            
            if(slow):
                slowTimes.append(time.time()-baseTime+timeAdjusts[3][1]) #adds slow-mo end time to timestamp list
                slow = False
                if(debugging):
                    print("--S--")        
    elif(aiming): #if considered aiming, but not actually
            aimTimes.append(time.time()-baseTime+timeAdjusts[4][1]) #adds aiming end time to timestamp list
            aiming = False #stop considering aiming
            if(debugging):
                print("--A--")
            if(SLOW_KB in heldKeys): #if slow-mo key was held while aiming and it is still being held
                slowTimes.append(time.time()-baseTime+timeAdjusts[3][0]) #adds slow-mo start to timestamp list
                slow = True
                if(debugging):
                    print("S")
                    
#used to check if aiming after button is pressed because you will start aiming after an item finishes realoading if you were holding down the button as it was reloading
def checkAimingRepeat():
    checkStart = time.time()
    while(time.time() - checkStart < 8 and (heldButtons[0] or heldButtons[1]) and not aiming):
        checkIfAiming()

#checks if fast mo
def checkIfFast():
    global baseTime, throwing, wasThrowing, slow, aiming, fast, throwTimes, slowTimes, aimTimes, fastTimes
    
    image = ImageGrab.grab() #takes a screenshot
    if(not fast and FAST_KB in heldKeys and image.getpixel(fTxtLoc) == (255, 255, 255)): #if test point is white meaning you're in fast-mo
        fastTimes.append(time.time()-baseTime+timeAdjusts[5][0]) #adds fast-mo start to timestamp list
        fast = True
        if(debugging):
            print("F")
        
        if(aiming):
            #fast-mo overrides aiming speed
            aimTimes.append(time.time()-baseTime+timeAdjusts[4][1]) #adds aiming end time to timestamp list
            aiming = False #stop considering aiming
            if(debugging):
                print("--A--")
            
        if(slow):
            slowTimes.append(time.time()-baseTime+timeAdjusts[3][1]) #adds slow-mo end to timestamp list
            slow = False #fast mo overrides slow mo
            if(debugging):
                print("--S--")
        if(throwing): #if was throwing before fast-mo press
            throwTimes.append(time.time()-baseTime+timeAdjusts[2][1]) #adds throw end to timestamp list (same as throw start when pausing taken into account)
            throwing = False
            wasThrowing = True
            if(debugging):
                print("--T--")
    elif(fast and not FAST_KB in heldKeys):
        fastTimes.append(time.time()-baseTime+timeAdjusts[5][1]) #adds fast-mo end to timestamp list
        fast = False
        if(debugging):
            print("--F--")
            
        #check if fast-mo paused aiming (speed)
        aTimer = Timer(.05, checkIfAiming) #set up delayed aim check
        aTimer.start() #start 50ms timer till aim check called 
        
        if(SLOW_KB in heldKeys): #if slow-mo key was held while fast-mo was held and it is still being held
            slowTimes.append(time.time()-baseTime+timeAdjusts[3][0]) #adds slow-mo start to timestamp list
            slow = True
            if(debugging):
                print("S")
        if(wasThrowing): #was throwing before fast-mo unfroze game
            throwTimes.append(time.time()-baseTime+timeAdjusts[2][0]) #adds throwing start to timestamp list
            throwing = True
            wasThrowing = False
            if(debugging):
                print("T")
        
def throwPause():
    global baseTime, timeAdjusts, throwing, throwTimes
    throwTimes.append(time.time()-baseTime+timeAdjusts[2][0]) #adds throwing start to timestamp list
    throwing = True
    if(debugging):
        print("T")