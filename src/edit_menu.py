import datetime as dt
import tkinter as tk
import tkinter.messagebox as messagebox
import collections

import src.utils as utils
import src.plots as plots


class EditMenu(tk.Menu):
    """
    Implements all the edition options for tracks: cut, reverse, insert time,
    split...
    """
    def __init__(self, parent, controller):
        # Define hinheritance
        tk.Menu.__init__(self, parent)
        self.controller = controller  # self from parent class
        self.parent = parent

        # Define menu
        self.editmenu = tk.Menu(parent, tearoff=0)
        self.editmenu.add_command(label='Cut', command=self.cut_segment)
        self.editmenu.add_command(label='Reverse',
                                  command=self.reverse_segment)
        self.editmenu.add_command(label='Insert time',
                                  command=self.insert_time)
        self.editmenu.add_command(label='Fix elevation',
                                  command=self.fix_elevation)
        self.editmenu.add_command(label='Split segment',
                                  command=self.split_segment)
        parent.add_cascade(label='Edit', menu=self.editmenu)

        # Time variables initialization
        self.timestamp = dt.datetime(2000, 1, 1, 0, 0, 0)
        self.speed = 0

    @utils.not_implemented
    def cut_segment(self):
        pass

    def reverse_segment(self):
        selected_segment = \
            self.controller.shared_data.my_track.selected_segment_idx

        if len(selected_segment) == 1:
            segment_idx = selected_segment[0]
            self.controller.shared_data.my_track.reverse_segment(segment_idx)

            # Update plot
            plots.plot_track_info(
                self.controller.shared_data.my_track,
                self.controller.shared_data.ax_track_info)

            plots.plot_elevation(self.controller.shared_data.my_track,
                                 self.controller.shared_data.ax_ele)

            self.controller.shared_data.canvas.draw()

        elif len(selected_segment) > 1:
            messagebox.showerror('Warning',
                                 'More than one segment is selected')
        elif len(selected_segment) == 0:
            messagebox.showerror('Warning',
                                 'No segment is selected')

    def insert_time(self):
        """
        Open a new window to introduce time and speed, then a timestamp is
        added to the whole track
        """
        if self.controller.shared_data.my_track.size == 0:
            message = 'There is no loaded track to insert timestamp'
            messagebox.showwarning(title='Insert Time Assistant',
                                   message=message)
            return

        self.timestamp = dt.datetime(2000, 1, 1, 0, 0, 0)
        self.speed = 0

        spinbox_options = {'year': [1990, 2030, 2000],
                           'month': [1, 12, 1],
                           'day': [1, 31, 1],
                           'hour': [0, 23, 0],
                           'minute': [0, 59, 0],
                           'second': [0, 59, 0]}

        top = tk.Toplevel()
        top.title('Insert Time Assistant')

        # Insert data frame
        frm_form = tk.Frame(top, relief=tk.FLAT, borderwidth=3)
        frm_form.pack()  # insert frame to use grid on it
        spn_time = collections.defaultdict()

        for i, entry in enumerate(spinbox_options):
            # This allow resize the window
            top.columnconfigure(i, weight=1, minsize=75)
            top.rowconfigure(i, weight=1, minsize=50)

            # Create widgets
            var = tk.StringVar(top)
            var.set(spinbox_options[entry][2])

            spn_time[entry] = tk.Spinbox(from_=spinbox_options[entry][0],
                                         to=spinbox_options[entry][1],
                                         master=frm_form,
                                         width=8,
                                         textvariable=var,
                                         justify=tk.RIGHT,
                                         relief=tk.FLAT)

            lbl_label = tk.Label(master=frm_form, text=f'{entry}', anchor='w')

            # Grid
            lbl_label.grid(row=i, column=0)  # grid attached to frame
            spn_time[entry].grid(row=i, column=1)

        # Insert speed
        i = len(spn_time)
        top.columnconfigure(i, weight=1, minsize=75)
        top.rowconfigure(i, weight=1, minsize=50)
        spn_speed = tk.Spinbox(from_=0, to=2000,
                               master=frm_form,
                               width=8,
                               justify=tk.RIGHT,
                               relief=tk.FLAT)
        lbl_label = tk.Label(master=frm_form, text=f'speed (km/h)', anchor='w')
        lbl_label.grid(row=i, column=0, pady=10)
        spn_speed.grid(row=i, column=1)

        def check_timestamp():
            try:
                self.timestamp = dt.datetime(int(spn_time['year'].get()),
                                             int(spn_time['month'].get()),
                                             int(spn_time['day'].get()),
                                             int(spn_time['hour'].get()),
                                             int(spn_time['minute'].get()),
                                             int(spn_time['second'].get()))
                self.speed = float(spn_speed.get())
                if self.speed <= 0:
                    raise ValueError('Speed must be a positive number.')

                # Insert timestamp
                self.controller.shared_data.my_track.\
                    insert_timestamp(self.timestamp, self.speed)
                top.destroy()

            except (ValueError, OverflowError) as e:
                messagebox.showerror('Input Error', e)

        def clear_box():
            for s in spn_time:
                spn_time[s].delete(0, 8)
                spn_time[s].insert(0, spinbox_options[s][2])
            spn_speed.delete(0, 8)
            spn_speed.insert(0, 0)

        # Button frame
        frm_button = tk.Frame(top)
        frm_button.pack(fill=tk.X, padx=5,
                        pady=5)  # fill in horizontal direction

        btn_clear = tk.Button(master=frm_button, text='Clear',
                              command=clear_box)
        btn_submit = tk.Button(master=frm_button, text='Submit',
                               command=check_timestamp)
        btn_clear.pack(side=tk.RIGHT, padx=10)
        btn_submit.pack(side=tk.RIGHT, padx=10)

    def fix_elevation(self):
        selected_segment = \
            self.controller.shared_data.my_track.selected_segment_idx

        if len(selected_segment) == 1:
            segment_idx = selected_segment[0]
            self.controller.shared_data.my_track.fix_elevation(segment_idx)

            # Update plot
            plots.plot_track_info(
                self.controller.shared_data.my_track,
                self.controller.shared_data.ax_track_info)

            plots.plot_elevation(self.controller.shared_data.my_track,
                                 self.controller.shared_data.ax_ele)

            self.controller.shared_data.canvas.draw()

        elif len(selected_segment) > 1:
            messagebox.showerror('Warning',
                                 'More than one segment is selected')
        elif len(selected_segment) == 0:
            messagebox.showerror('Warning',
                                 'No segment is selected')

    @utils.not_implemented
    def split_segment(self):
        pass