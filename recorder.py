import mss # MSS for screen capturing
import time # Time for FPS usage
try:
    from PIL import Image # PIL.Image to save a gif
except:
    import Image 
import tkinter as tk # Tkinter for GUI
import win32gui # win32 for drawing on the user's screen (showing partial screen capture)
import win32ui 
import win32api #SystemMetrics to grab screen size and cursor click/position
import win32con 
import keyboard # Keyboard for keyboard pressing (to start/stop recording)
from videoeditor import VideoEditor # For editing the video once finished
    
# GUI using TKinter
class Recorder(tk.Frame):
    # initialize the GUI
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        
        # Two variables for when the user wants to make a gif of a specfic size, it will use two of their mouse locations.
        self.ploc = [-1,-1]
        self.rloc = [0,0]
        
        # Get the DC object from windows, grab a handle tio the monitor (hwnd), and grab the monitor size
        self.dc = win32gui.GetDC(0)
        self.dcObj = win32ui.CreateDCFromHandle(self.dc)
        self.hwnd = win32gui.WindowFromPoint((0,0))
        self.monitor = (0, 0, win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1))
        
        # Create a transparent brush so the user can see through, and a blue pen for an outline
        self.brush = win32ui.CreateBrush(1, 0, 0)
        self.dcObj.SelectObject(self.brush)      
        self.pen = win32ui.CreatePen(0, 1, 0xFF0000)     # create a pen (solid, 1pixel  wide, blue color)
        self.dcObj.SelectObject(self.pen)
        
        self.create_widgets()

    # Function to create the GUI
    def create_widgets(self):
        # Create a frame to hold the screenshot buttons
        self.f1 = tk.Frame(self.master)
        self.f1.grid(row=0, columnspan=2)
        
        # Place the screenshot buttons so user can select one or the either
        self.v = tk.IntVar()
        self.v.set(1)
        tk.Radiobutton(self.f1, text="Full Screenshot", variable=self.v, value=1, indicatoron=0, width=20).pack(side="left")
        tk.Radiobutton(self.f1, text="Partial Screenshot", variable=self.v, value=2, indicatoron=0, width=20).pack(side="right")
        
        # Allow user to change the framerate of the gif
        tk.Label(self.master, text="FPS:").grid(row=1, column=0, sticky="SW")
        self.fps = tk.Scale(self.master, from_=5, to=50, length=200, resolution=5, orient=tk.HORIZONTAL, bd=2)
        self.fps.set(50)
        self.fps.grid(row=1, column=1, sticky = "NESW")

        # Allow user to change the key that starts and ends the gif recording.
        tk.Label(self.master, text="Start&End Key:").grid(row=2,column=0, sticky="W")
        self.key = tk.StringVar()
        self.key.set("F6") # Set a default variable of F6
        self.startKey = tk.Entry(self.master, textvariable=self.key, bd=2)
        self.startKey.grid(row=2, column=1, sticky="NESW")

        # Fourth frame to hold the start and close buttons
        self.f4 = tk.Frame(self.master)
        self.f4.grid(row=5, columnspan=2)
        
        # Define the start and close buttons to start or close
        self.quit = tk.Button(self.f4, text="Cancel", fg="red", command=self.master.destroy)
        self.quit.pack(side="left")
        
        # Button to start the gif-recording
        start = tk.Button(self.f4, text="Start", fg="green")
        start.bind("<ButtonRelease-1>", self.findSize)
        start.pack(side="right")
        
    # Function definition for creating a gif of a portion of the screen the user selects.
    def record(self):
        # make sure ploc and rloc are not the same.
        if(self.ploc == self.rloc):
            return
        
        with mss.mss() as sct:
            # Grab the framerate and time of the gif the user wants.
            self.fps.set(50 if self.fps.get() > 50 else self.fps.get()) # 50 is the max framerate. Any higher and the gif defaults to 10frames/sec
            
            # Find the top, left, width, and height of the portion of the screen the user wants.
            w = abs(self.ploc[0]-self.rloc[0]) 
            h = abs(self.ploc[1]-self.rloc[1]) 
            left = min(self.ploc[0], self.rloc[0])
            top = min(self.ploc[1], self.rloc[1])
            
            # Part of the screen to capture
            mon = {"top": top, "left": left, "width": w, "height": h}
            
            # Image list
            img = [] # Creating a full list because we know the size of it, to improve speed of adding each image.
            
            self.dcObj.SelectObject(win32ui.CreatePen(0, 1, 0x00FF00)) # change the brush to green so the user can tell it's ready to record
            
            # wait for the key input to begin
            while(not keyboard.is_pressed(self.key.get())):
                win32gui.InvalidateRect(self.hwnd, self.monitor, True) # Refresh the entire monitor
                self.dcObj.Rectangle((left-1, top-1, left+w+1, top+h+1))
                time.sleep(1/10)
            # after user presses the key, wait for them to release it to start
            while(keyboard.is_pressed(self.key.get())):
                time.sleep(1/10)
            
            maxTime = time.time() + 60
            lastTime = time.time()
            avgfps = 0
            
            self.dcObj.SelectObject(win32ui.CreatePen(0, 1, 0x0000FF)) # change the red to green so the user can tell it's recording
            # Time variable
            delay = 1/self.fps.get()
            nextt = time.time() + delay
            while(not keyboard.is_pressed(self.key.get()) and time.time() <= maxTime):
                win32gui.InvalidateRect(self.hwnd, self.monitor, True) # Refresh the entire monitor
                self.dcObj.Rectangle((left-1, top-1, left+w+1, top+h+1))
                t = time.time()
                
                avgfps += t-lastTime
                #print(t-lastTime)
                lastTime = t
                
                # Get raw pixels from the screen, save it to the list
                sct_img = sct.grab(mon)
                img.append(sct_img)
                
                # wait until the time the next frame is supposed to be
                if(nextt < t):
                    nextt = t
                time.sleep(nextt - t)
                nextt = nextt + delay
            
            # Turn all images into PIL compatable images
            for i in range(len(img)):
                img[i] = Image.frombytes("RGB", img[i].size, img[i].bgra, "raw", "BGRX")
            
            # Print the average fps recorded at
            avgfps = avgfps / len(img)
            print(1/avgfps)
            
            fps = self.fps.get()
            self.master.destroy() # destroy the current window creating the video editor
            # Create a video editor with the frames gathered
            root = tk.Tk()
            root.title("Gifit Video Editor")
            
            ve = VideoEditor(img, fps, master=root)
            ve.mainloop()
            
    def areaDraw(self):
        self.master.wm_state("iconic") # minimize the window
        
        # While the user has the mouse button held down, draw a box.
        while(True):
            loc = win32api.GetCursorPos()
            # Ask windows to clear the screen (they won't right away), then draw a rectangle where the recording would be
            win32gui.InvalidateRect(self.hwnd, self.monitor, True) # Refresh the entire monitor
            self.dcObj.Rectangle((min(self.ploc[0],loc[0])-1, min(self.ploc[1],loc[1])-1, max(self.ploc[0],loc[0])+1, max(self.ploc[1],loc[1])+1))
            
            # once mouse button is released, gather the location and return
            if(win32api.GetAsyncKeyState(win32con.VK_LBUTTON) >= 0):
                self.rloc[0] = loc[0]
                self.rloc[1] = loc[1]
                
                return
            time.sleep(1/50)
    
    
    def clickWait(self):            
        # wait for the user to click and gather the click location
        while(True):
            if(win32api.GetAsyncKeyState(win32con.VK_LBUTTON) < 0):
                loc = win32api.GetCursorPos()
                self.ploc[0] = loc[0]
                self.ploc[1] = loc[1]
                
                self.areaDraw()
                return
            time.sleep(1/10)
        
    def findSize(self, event):
        if(self.v.get()==2):
            # user is doing a partial screen record
            # Set the ploc locations to outside the screen, and record for their mouse usage.
            self.ploc[0] = 0
            self.ploc[1] = 0
            
            self.clickWait()
            
        elif(self.v.get()==1):
            # user is doing full screen record, set the dimensions to the full screen size - 1 pixel so the border isn't seen
            self.ploc[0] = 1
            self.ploc[1] = 1
            self.rloc[0] = win32api.GetSystemMetrics(0)-1
            self.rloc[1] = win32api.GetSystemMetrics(1)-1
                
        else:
            # User did not select an option
            return
        
        self.record()
    
# set the root of the GUI and start it
root = tk.Tk()
root.title("Gifit")

rec = Recorder(master=root)
rec.mainloop()   