# Heat Signature Replay
 OBS Plugin that lets you record and (just about) automatically edit Heat Signature clips to realtime speed

## Example
Before: https://youtu.be/8BLbGGG98ZE

After: https://youtu.be/lhgmKK2K1wk

## Caveats
* Built around recording clips in which you stay on one ship (possibly works either way, but not sure yet)
* Time still slowed when enemies see you.
* Some frames lost unnecessarily here and there from the original footage to make sure edit doesn't include pause frames.
* Can't account for minimizing the game.

## To-Do
* Find (and handle) edge cases I missed
* Combine both programs into one
* Make UI friendlier
* Add keybind to stop recording rather than just having a toggle
* Let you start recording while paused
* Speed up time slightly after a successful throw as that slows down time

## Setup
1. Install OBS (www.obsproject.com)
2. Install Python 3.6 (www.python.org/downloads/release/python-368)
3. Download Python dependencies by typing the following into command prompt:
~~~~
pip3.6 install pillow
pip3.6 install pynput
pip3.6 install moviepy
~~~~
4. Download the latest release of this program (two .py files) and put it in a folder on its own (www.github.com/ineeddspelchek/Heat-Signature-Replay/releases)
5. Open `heatSigReplayProcessing.py` and edit `leaveFastMo` (`False` to slow down Fast Mo segments; `True` to not), inVidExt, and outVidExt to whatever you want
6. Find some way to run `heatSigReplayProcessing.py` (I use Visual Studio Code; for some reason opening it with python.exe reads files from another folder instead of from the one it's in, so that won't work)
7. Open OBS
8. Go to Tools > Scripts
9. Go to the `Python Settings` tab
10. Browse and add Install Path for Python ***3.6*** (must be that version; earlier *might* work; later will never)
11. Go back to `Scripts`
12. Press the "+" sign 
13. Add `heatSigReplay.py`
14. Click on it in the Script Menu
15. Set up your keybinds as you have them in the game and set the record keybind to be easy to reach but hard to accidentally press
16. Start Heat Signature
17. Press `Enable Replay` and `Finding Coords` in the Script Menu
18. Go through each of the 5 coordinates and set them according to directions on the Script Menu (or set them to what worked for me, though they may not line up with your setup)
19. ***Press `Disable Replay` (otherwise, the key and mouse listeners don't get killed until OBS is closed)***
20. Set up a Game Capture source for Heat Signature's window

## Running
1. Start Heat Signature
2. Start OBS
3. Open Script Menu
4. Open `Script Log`
5. Press `Enable Replay`
6. Play game until you want to start recording.
7. Unpause game if it is paused
8. Press your record keybind
9. Rip and Tear
10. Once you are done, unpause the game if it is paused
11. Press the record keybind again.
12. Press `Disable Replay` unless you're confident you won't accidentally press record
13. Drag the recording from OBS' folder to the folder containing this program and make sure it is the only video file in the folder
14. Open the log
15. Copy text from `[[` to `]]` (don't worry about copying line breaks or `[Unknown Script] `s in between just don't get anything before or after)
16. Run `heatSigReplayProcessing.py` and input the copied text
17. Wait for it to edit (should take x2-x4 the capture's length)
18. Enjoy the output file placed in the same folder.
19. Re-enable Replay if you disabled it.
20. Continue playing.
21. Close OBS once you're done (preferrably disabling replay before you do).
