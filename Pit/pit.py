import XBee
import datetime
from time import sleep
import Tkinter as tk
import ttk
import threading
import Queue

class gui_class(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.tab = SimpleTable(self, 4, 6)
        self.tab.pack(side = "top", fill = "x")
        self.tab.set(0,0, "Front Left LVDT")
        self.tab.set(0,3, "Front right LVDT")
        self.tab.set(1,0, "Back Left LVDT")
        self.tab.set(1,3, "Back Right LVDT")
        self.tab.set(2,0, "Speed")
        self.tab.set(3,0, "RPM")
        self.tab.set(2,3, "Engine Temperature")
        
        self.queue = Queue.Queue()
        thread = RecvThread(self.queue)
        thread.start()
        self.process_data()
    def process_data(self):
        #print(self.queue.qsize())
        while self.queue.qsize():
            try:
                contents = self.queue.get()
                #print(contents)
                speed = contents[0] + " mph "
                rpm = contents[1]
                lvdt_fl_in = contents[2] + " inches "
                lvdt_fl_cm = contents[3] + " centimeters "
                lvdt_fr_in = contents[4] + " inches "
                lvdt_fr_cm = contents[5] + " centimeters "
                lvdt_bl_in = contents[6] + " inches "
                lvdt_bl_cm = contents[7] + " centimeters "
                lvdt_br_in = contents[8] + " inches "
                lvdt_br_cm = contents[9] + " centimeters "
                tmp_eng_f = contents[10] + " C "
                tmp_eng_c = contents[11] + " F "

                self.tab.set(0,1,lvdt_fl_in)
                self.tab.set(0,2,lvdt_fl_cm)
                self.tab.set(0,4,lvdt_fr_in)
                self.tab.set(0,5,lvdt_fr_cm)
                self.tab.set(1,1,lvdt_bl_in)
                self.tab.set(1,2,lvdt_bl_cm)
                self.tab.set(1,4,lvdt_br_in)
                self.tab.set(1,5,lvdt_br_cm)
                self.tab.set(3,1,rpm)
                self.tab.set(2,1,speed)
                self.tab.set(2,4,tmp_eng_f)
                self.tab.set(2,5,tmp_eng_c)
                
            except Queue.Empty:
                pass
        self.after(100, self.process_data)


class SimpleTable(tk.Frame):
    def __init__(self, parent, rows=4, columns=6):
        # use black background so it "peeks through" to 
        # form grid lines
        tk.Frame.__init__(self, parent, background="black")
        self._widgets = []
        for row in range(rows):
            current_row = []
            for column in range(columns):
                label = tk.Label(self, text="", 
                                 borderwidth=20, width=40, font=("Helvetica", 20))
                label.grid(row=row, column=column, sticky="nsew", padx=1, pady=1)
                current_row.append(label)
            self._widgets.append(current_row)

        for column in range(columns):
            self.grid_columnconfigure(column, weight=1)


    def set(self, row, column, value):
        #print("set: {} {} {}".format(row,column,value))
        widget = self._widgets[row][column]
        widget.configure(text=value)

        
class RecvThread(threading.Thread):
    def __init__(self, queue):
        #print("thread init")
        threading.Thread.__init__(self)
        self.queue = queue
	with open("name.txt", "r") as f:
	    for line in f:
		self.fname = int(line.split()[0])
	with open("name.txt", "w") as f:
	    temp = self.fname+1
	    f.write("{}".format(temp))
	self.fname = "{}.csv".format(self.fname)
	with open(self.fname, "w") as f:
	    f.write("time,mph,rpm,fl_lvdt_inch,fl_lvdt_cm,fr_lvdt_inch,fr_lvdt_cm,bl_lvdt_inch,bl_lvdt_cm,br_lvdt_inch,br_lvdt_cm,eng_temp_f,eng_temp_c,\n")
    def run(self):
        #print("thread recv")
        self.xbee = XBee.XBee("/dev/ttyUSB0")  # Your serial port name here
        try:
            while(1):
		sleep(0.1)
                Msg = self.xbee.Receive()
                print(Msg)
                if Msg:
                    content = Msg[14:-1].decode('ascii')
                    parsed_content = content.split("%$%")
                    self.queue.put(parsed_content)
                    #self.content_len = len(self.content)
                    #self.myLabel.config(text = self.content)
                    #print(content_len)
                    print("HE 1: {}, HE 2: {}, LVDT 1: {}|{}, LVDT 2: {}|{}, LVDT 3: {}|{}, LVDT 4: {}|{}, Temp Amb: {}, Temp Eng: {}".format(*(parsed_content)))
		    dt = "{}".format(datetime.datetime.now())
		    dt = dt[:-7]
		    with open(self.fname, "a") as f:
		    	f.write("{},{},{},{},{},{},{},{},{},{},{},{},{},\n".format(dt,*(parsed_content)))
	except KeyboardInterrupt:
	    self.xbee.close()
	    self.f.close()
            exit()
            #sleep(0.1)
        
if __name__ == "__main__":
    gui = gui_class()
    gui.mainloop()
