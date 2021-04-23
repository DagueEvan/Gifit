from PIL import Image, ImageTk # To handle images from the screenshots and turn to a gif.
import numpy as np # Numpy and cv2 to turn gifs into mp4
import cv2
import tkinter as tk # GUI interface
import mss # MSS for screen capturing
from tkinter.filedialog import askdirectory
import os # os to grab  file path
import subprocess # subprocess to open file explorer
from win32api import GetMonitorInfo, MonitorFromPoint # grab monitor height and exclude the taskbar height.

# GUI using TKinter
class VideoEditor(tk.Frame):
    # initialize the GUI
    def __init__(self, img, recordedFPS, audio=None, master=None):
        super().__init__(master)
        # save the master variable.
        self.master = master
        
        # Save a new copy of images to alter. 
        self.images = img.copy()
        self.savedImages = img.copy()
        
        self.play = False # Var for whether or not to play the video.
        self.i = 0 # Current frame.
        
        # Hold the width and height of the video.
        self.width = tk.IntVar()
        self.height = tk.IntVar()
        self.width.set(self.images[0].size[0])
        self.height.set(self.images[0].size[1])
        
        # Find the max and min height/width, as well as hold the ratio of height to width.
        self.maxh = self.height.get()
        self.maxw = self.width.get()
        
        # For the crop function.
        self.minx = 0
        self.maxx = self.width.get()
        self.miny = 0
        self.maxy = self.height.get()
        self.ratio = (self.minx/self.width.get(), self.maxx/self.width.get(), self.miny/self.height.get(), self.maxy/self.height.get())
        
        # Variables for the custom range slider (Start/end frame).
        self.y = 10
        self.offset = 6
        self.values = len(self.images)
        self.range = (self.width.get() - 2*self.offset) / (self.values-1)
        self.rect1Val = 0
        self.rect2Val = self.values-1
        
        # with the variables set, create the GUI
        self.create_widgets(recordedFPS)

    # Function to create the GUI
    def create_widgets(self, recordedFPS):      
        # Start with a canvas to cover the window and hold everything.
        self.canvas = tk.Canvas(self.master, width=self.width.get(), height=self.height.get(), highlightthickness=0)
        self.canvas.grid(row=0, columnspan = 3, padx=(25,25), pady=(5,5))
        
        # Insert the first image of the video 
        a = ImageTk.PhotoImage(image=self.images[self.i])
        self.l = tk.Label(self.master, image = a)
        self.l.image = a
        #self.l.grid(row = 0, columnspan = 3, padx=(25,25), pady=(5,5))
        
        # Insert the first image of the video, and put a black border around it for the crop feature.
        self.currimage = self.canvas.create_image(0, 0, anchor="nw", image=a)
        self.crop = self.canvas.create_rectangle(self.minx, self.miny, self.maxx, self.maxy, width=3)
        # Assign a drag feature to the crop border.
        self.canvas.tag_bind(self.crop, '<1>', self.crop_click)
        self.canvas.tag_bind(self.crop, '<B1-Motion>', self.crop_update)
        
        # Creater a custom 2 value slider.
        self.slidercanvas = tk.Canvas(self.master, width=self.width.get(), height=self.y*4, highlightthickness=0)
        self.slidercanvas.grid(row=1, columnspan=3)
        self.line = self.slidercanvas.create_line(0,self.y,self.width.get(),self.y, width=10, fill="gray")
        self.rect1 = self.slidercanvas.create_rectangle(self.rect1Val*self.range+self.offset-4, self.y-5, self.rect1Val*self.range+self.offset+4, self.y+5, width=1, fill="white", outline="black")
        self.rect2 = self.slidercanvas.create_rectangle(self.rect2Val*self.range+self.offset-4, self.y-5, self.rect2Val*self.range+self.offset+4, self.y+5, width=1, fill="white", outline="black")
        
        # Slider values.
        self.text1 = self.slidercanvas.create_text(min(self.rect1Val*self.range+self.offset, self.width.get()-15), self.y+15, text=self.rect1Val+1)
        self.text2 = self.slidercanvas.create_text(min(self.rect2Val*self.range+self.offset, self.width.get()-15), self.y+15, text=self.rect2Val+1)
        
        # Functions for slider updates.
        self.slidercanvas.tag_bind(self.rect1, '<B1-Motion>', self.rect1_update)
        self.slidercanvas.tag_bind(self.rect2, '<B1-Motion>', self.rect2_update)
        
        # Play button to start/stop the video.
        self.d = tk.Button(self.master, text="Play", width = 10, command = self.Play)
        self.d.grid(row = 2, column = 1)
        
        # label and slider to change the framerate of the video.
        self.fps = tk.Scale(self.master, from_=1, to=50, orient=tk.HORIZONTAL, bd=2, showvalue = 0, command=self.UpdateFPS)
        self.fps.set(recordedFPS)
        self.fpslabel = tk.Label(self.master, text="Framerate: %i fps" % self.fps.get())
        self.fpslabel.grid(row=3, column=0)
        self.fps.grid(row=3, column=1, columnspan = 2, sticky = "NESW")
        
        # Create a frame and put the height&width on the same row. 
        f1 = tk.Frame(self.master)
        f1.grid(row=4, columnspan=3)
        tk.Label(f1, text="Height(px):").grid(row = 0, column=0)
        h = tk.Entry(f1, textvariable = self.height)
        h.grid(row = 0, column = 1)
        tk.Label(f1, text="Width(px):").grid(row = 0, column=2)
        i = tk.Label(f1, textvariable = self.width)
        i.grid(row = 0, column = 3)
        j = tk.Button(f1, text="Set", width = 10, command = self.SetSize)
        j.grid(row = 0, column = 4)
        
        # Another frame to hold the prefered save extension and file name. 
        f2 = tk.Frame(self.master)
        f2.grid(row=5, columnspan=3)
        
        # File name variables. Put it with the save extensions.
        self.fname = tk.StringVar()
        self.fname.set("gifit") # Set a default name of gifit
        fileName = tk.Entry(f2, textvariable=self.fname, bd=2)
        fileName.grid(row=0, column=0, sticky="E")
        tk.Label(f2, text=".").grid(row=0, column=1, sticky="W")
        
        # Save extension
        self.fileType = tk.IntVar()
        self.fileType.set(1)
        k = tk.Radiobutton(f2, text="GIF", variable=self.fileType, value=1, indicatoron=0, width=20)
        k.grid(row=0, column=2)
        n = tk.Radiobutton(f2, text="MP4", variable=self.fileType, value=2, indicatoron=0, width=20)
        n.grid(row=0, column=3)
        
        # Allow user to change where the file will be saved.
        self.filePath = tk.StringVar()
        self.filePath.set(os.path.realpath("")) # Grab the current file path.
        changePath = tk.Button(self.master, text="Change Path", fg="green", command= self.SetPath)
        changePath.grid(row=8, column=0)
        fp = tk.Label(self.master, textvariable=self.filePath)
        fp.grid(row=8, column=1)
        start = tk.Button(self.master, text="Save", fg="green", command= self.Save)
        start.grid(row=8, column=2)
        
        # Height of the window
        monitor_info = GetMonitorInfo(MonitorFromPoint((0,0)))
        mon_work_area = monitor_info.get("Work") # Maximum usable monitor size
        
        #update the window
        self.master.update_idletasks()  
        
        # rough size of the title bar
        tb_size = 19
        
        # Get the height of the widgets in the window. Define max height (for displaying the video) from that.
        self.master.update_idletasks()  
        self.widgetsHeight = self.master.winfo_reqheight() - self.height.get()
        self.maxHeight = mon_work_area[3] - self.widgetsHeight - tb_size #max height of the image is the total usable area minus widget height. Also take out the height of the title bar
        
        # Update the video size.
        self.SetSize()
        
        # if video normall will be as large or larger than can be displayed, put window in full screen
        if(self.height.get() >= self.maxHeight):
            self.master.state('zoomed')
    
    # update the begining frame slider.
    def rect1_update(self, event):
        # Find the closest value to the user's cursor
        n = round((event.x - self.offset) / self.range)
        
        # ensure the slider wont go above the max, above the right slider, or below the min
        if(n < 0):
            self.rect1Val = 0
        elif(n > self.rect2Val):
            self.rect1Val = self.rect2Val
        else:
            self.rect1Val = n
        
        # Update the slider location to fit where it should be.
        self.slidercanvas.coords(self.rect1, self.rect1Val*self.range+self.offset-4, self.y-5, self.rect1Val*self.range+self.offset+4, self.y+5)
        self.slidercanvas.coords(self.text1, min(self.rect1Val*self.range+self.offset, self.width.get()-15), self.y+15)
        self.slidercanvas.itemconfig(self.text1, text=self.rect1Val+1)
        
        # Update the images to show what's selected.
        self.showImage(self.rect1Val)
    
    # Update the ending frame slider.
    def rect2_update(self, event):
        # Find the closest value to the user's cursor
        n = round((event.x - self.offset) / self.range)
        
        # ensure the slider wont go above the max, below the left slider, or below the min
        if(n < self.rect1Val):
            self.rect2Val = self.rect1Val
        elif(n > self.values - 1):
            self.rect2Val = self.values - 1
        else:
            self.rect2Val = n
        
        # Update the slider location to fit where it should be.
        self.slidercanvas.coords(self.rect2, self.rect2Val*self.range+self.offset-4, self.y-5, self.rect2Val*self.range+self.offset+4, self.y+5)
        self.slidercanvas.coords(self.text2, min(self.rect2Val*self.range+self.offset, self.width.get()-15), self.y+15)
        self.slidercanvas.itemconfig(self.text2, text=self.rect2Val+1)
        
        # Update the images to show what's selected.
        self.showImage(self.rect2Val)
    
    # Update fps labe.
    def UpdateFPS(self, val):
        self.fpslabel.config(text="Framerate: %s fps" % val)
        
    # Update quality label
    def UpdateQuality(self, val):
        self.qualityLabel.config(text="Quality: %s" % val)
    
    # Set the path to a directory the user selects.
    def SetPath(self):
        self.filePath.set(askdirectory(title='Select Folder'))
    
    # Save the video 
    def Save(self):
        # make sure the width-height ratio is correct and updated.
        self.width.set(self.height.get() * self.maxw / self.maxh)
        
        # Update all images to be the size the user wants it to be.
        for i in range(self.values):
            self.images[i] = self.savedImages[i].resize((self.width.get(), self.height.get()))
        
        # Crop all the images based on the user's specifications.
        for i in range(len(self.images)):
            self.images[i] = self.images[i].crop((self.width.get() * self.ratio[0], self.height.get() * self.ratio[2], self.width.get() * self.ratio[1], self.height.get() * self.ratio[3]))
        
        # if the user selected gif extension, save as a gif.
        if(self.fileType.get() == 1):
            self.images[self.rect1Val].save('{}/{}.gif'.format(self.filePath.get(), self.fname.get()), save_all=True, append_images=self.images[self.rect1Val+1:self.rect2Val], fps=self.fps.get(), loop=0, optimize=True)
        elif(self.fileType.get() == 2):
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            video = cv2.VideoWriter('{}/{}.mp4'.format(self.filePath.get(), self.fname.get()), fourcc = fourcc, fps = self.fps.get(), frameSize =  (self.width.get(), self.height.get()))
            
            for img in self.images:
                video.write(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
            video.release()
        
        # open the folder to where the user saved the video.
        subprocess.Popen('explorer /select, {}'.format(os.path.realpath(self.filePath.get()+"/{}.gif".format(self.fname.get()))))
        
        #Update the size of the video.
        self.SetSize()
        
    # Check if the user is clicking one of the black borders.
    def crop_click(self, event):
        self.change = ""
        
        #As the border includes the empty space in the middle, check if the user is clicking close to the border
        # If the user is clicking the border, update which border they are clicking (top bottom left right )
        if(abs(event.y - self.miny) < 10):
            self.change += "T"
        elif(abs(event.y - self.maxy) < 10):
            self.change += "B"
        else:
            self.change += "N"
            
        if(abs(event.x - self.minx) < 10):
            self.change += "L"
        elif(abs(event.x - self.maxx) < 10):
            self.change += "R"
        else:
            self.change += "N"
        
    # update the crop border.
    def crop_update(self, event):
        # if the user changed the top or the bottom, move the border with the cursor.
        if(self.change[0] == 'T'):
            self.miny = max(0,event.y)
        elif(self.change[0] == 'B'):
            self.maxy = min(self.height.get(),event.y)
        
        # if the user changed the left or thwe right, move the border with the cursor.
        if(self.change[1] == 'L'):
            self.minx = max(0,event.x)
        elif(self.change[1] == 'R'):
            self.maxx = min(self.width.get(),event.x)
            
        # Upodate the border and the ratio of width-height
        self.canvas.coords(self.crop, self.minx, self.miny, self.maxx, self.maxy)
        self.ratio = (self.minx/self.width.get(), self.maxx/self.width.get(), self.miny/self.height.get(), self.maxy/self.height.get())
    
    # Set the width and height of the video and images.
    def SetSize(self):    
        # if the user tries to make the video larger than the max (Would reduce quality), set it to the max.
        # if not, set it to the correct height-width ratio based on the height.
        if(self.height.get() >= self.maxh):
            self.height.set(self.maxh)
            self.width.set(self.maxw)            
        else:
            self.width.set(self.height.get() * self.maxw / self.maxh)
        
        # height and width of the video. 
        h = min(self.maxHeight, self.height.get())
        w = int(h * self.maxw / self.maxh)
        
        # update all images from the saved image set and resize them.
        for i in range(self.values):
            self.images[i] = self.savedImages[i].resize((w, h))
        
        # set the minimum window size to not hide anything.
        self.master.minsize(w, h+self.widgetsHeight)
        
        # update the crop variables based on the ratios to fit the image size.
        self.minx = w * self.ratio[0]
        self.maxx = w * self.ratio[1]
        self.miny = h * self.ratio[2]
        self.maxy = h * self.ratio[3]
        self.canvas.coords(self.crop, self.minx, self.miny, self.maxx, self.maxy)
        self.canvas.config(width=w, height=h)
        
        # update the frame sliders to fit the image size.
        self.slidercanvas.config(width=w, height=self.y*4)
        self.range = (w - 2*self.offset) / (self.values-1)
        self.slidercanvas.coords(self.rect1, self.rect1Val*self.range+self.offset-4, self.y-5, self.rect1Val*self.range+self.offset+4, self.y+5)
        self.slidercanvas.coords(self.text1, min(self.rect1Val*self.range+self.offset, self.width.get()-15), self.y+15)
        self.slidercanvas.coords(self.rect2, self.rect2Val*self.range+self.offset-4, self.y-5, self.rect2Val*self.range+self.offset+4, self.y+5)
        self.slidercanvas.coords(self.text2, min(self.rect2Val*self.range+self.offset, self.width.get()-15), self.y+15)
        
        # Show the first image based on the slider.
        self.showImage(self.rect1Val)
    
    # Decrease the framerate.
    def Slower(self):
        if(self.fr.get() > 1):
            self.fr.set(self.fr.get()-1)
    
    # Increase the framerate.
    def Faster(self):
        if(self.fr.get() < 30):
            self.fr.set(self.fr.get()+1)    
    
    # Play the video and change the button to stop the video on next click.
    def Play(self):
        self.play = True
        self.d.configure(text="Stop", command = self.Stop)

        # loop actually plays the video, play just updates the variable and button.
        self.Loop()
    
    # Plays the video. 
    def Loop(self):
        # If the video would be going past the last slide, set it to the first.
        # Update the shown image to be the correct one.
        if(self.i >= self.rect2Val):
            self.i = self.rect1Val
            
            a = ImageTk.PhotoImage(image=self.images[self.i])
            self.l.configure(image = a)
            self.l.image = a
            
            self.canvas.itemconfig(self.currimage, image = a)
        else:
            self.i += 1
            
            a = ImageTk.PhotoImage(image=self.images[self.i])
            self.l.configure(image = a)
            self.l.image = a
            
            self.canvas.itemconfig(self.currimage, image = a)
            
        # Run this function again according to the framerate.
        self._job = self.master.after(int(1000/self.fps.get()), self.Loop)
            
    # Stops playing the video.
    def Stop(self):
        # Updates button
        self.play = False
        self.d.configure(text="Play", command = self.Play)
        
        # Cancels the loop.
        self.master.after_cancel(self._job)
        self._job = None
    
    # Goes to the first image.
    def firstImage(self):
        self.i = 0
            
        a = ImageTk.PhotoImage(image=self.images[0])
        self.l.configure(image = a)
        self.l.image = a
        
        self.canvas.itemconfig(self.currimage, image = a)
    
    # Goes to the next image.
    def nextImage(self):
        if(self.i < self.rect2Val):
            self.i += 1
            
            a = ImageTk.PhotoImage(image=self.images[self.i])
            self.l.configure(image = a)
            self.l.image = a
            
            self.canvas.itemconfig(self.currimage, image = a)
    
    # goes to the last image.
    def lastImage(self):
        if(self.i > self.rect1Val):
            self.i -= 1
            
            a = ImageTk.PhotoImage(image=self.images[self.i])
            self.l.configure(image = a)
            self.l.image = a
            
            self.canvas.itemconfig(self.currimage, image = a)
    
    # shows an image based off a given variable.
    def showImage(self, i):
        self.i = i
        a = ImageTk.PhotoImage(image=self.images[self.i])
        self.l.configure(image = a)
        self.l.image = a
            
        self.canvas.itemconfig(self.currimage, image = a)

# all of this is just to test the program.
if(__name__ == "__main__"):
    root = tk.Tk()
    root.title("Gifit Video Editor")
    
    img = []
    n = 50
    w = 750
    h = 500
    
    monitor = monitor = {"top": 0, "left": 0, "width": w, "height": h}
    with mss.mss() as sct:
        for i in range(n):
            sct_img = sct.grab(monitor)
            img.append(Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX"))
            
            monitor["top"] += 10
            monitor["left"] += 10
            
    # set the root of the GUI and start it

    app = VideoEditor(img, 30, master=root)
    app.mainloop()