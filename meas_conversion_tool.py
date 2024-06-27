"""meas_conversion_tool.py

   Converts measurement lables to Excel or Matlab files with a selected raster
   
   @file meas_conversion_tool.py
   @author Lukas Gerstlauer
   @email lukas.gerstlauer@de.bosch.com
   @date 21.06.24
   @version 1.0
"""

import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from glob import glob
import os
import sys
import re
from datetime import datetime
from pandas import DataFrame
from scipy.io import savemat
from ai_utils.Mdf_transformer import mdf_transformer
import asammdf
from PIL import Image, ImageTk

import profile_manager


JSON_PATH = "profiles.json"      # Path to the json file
LOG_FILE_PATH = "logfile.log"    # Path to the log file
ICON_PATH  = "icon.ico"          # Path to the icon



class MeasurementGUI(tk.Tk):
    """Class for the main window of the tool
    """

    def __init__(self):
        """Initialize function of the class MeasurementGUI
        """
        super().__init__()
        self.all_profiles = profile_manager.load_profiles()
        self.profile_names = self.extract_profile_names(self.all_profiles)
        self.output_paths = [""]
        self.output_paths = []

        try:
            icon = Image.open(ICON_PATH)
            icon = ImageTk.PhotoImage(icon)
            self.iconphoto(True, icon)
        except:
            pass

        self.deiconify()
        self.title("Conversion Tool")
        self.geometry("1250x570")
        self.lift()
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(13, weight=1)
        self.grid_rowconfigure(7, minsize=35)

        title_label = tk.Label(self, text="Conversion Tool", font=((), 12))
        title_label.grid(row=1, column=1, columnspan=3)

        measurement_path_label = tk.Label(self, text="Measurement Files", justify="left")
        measurement_path_label.grid(row=2, column=1, sticky="nw", pady=5)

        self.meas_path = []
        self.measurement_path_text = tk.Text(self, height=5, font=("TkDefaultFont",))
        self.measurement_path_text.bind("<KeyRelease>", self.event_measurement_path)
        self.measurement_path_text.grid(row=2, column=2, sticky="nsew", padx=7, pady=(5, 20))

        scrollbar_meas = tk.Scrollbar(self)
        scrollbar_meas.grid(row=2, column=3, sticky="nsw", pady=(5, 20), padx=5)

        self.measurement_path_text.config(yscrollcommand=scrollbar_meas.set)
        scrollbar_meas.config(command=self.measurement_path_text.yview)

        meas_browse_button = tk.Button(self, text="...", command=self.browse_measurement_path)
        meas_browse_button.grid(row=2, column=4, columnspan=2, sticky="nsew", padx=5, pady=(5, 20))

        profile_label = tk.Label(self, text="Select Profile", justify="left")
        profile_label.grid(row=3, column=1, sticky="w")

        self.profile = tk.StringVar()
        self.profile.set(self.profile_names[0])
        self.profile_dropdown = ttk.Combobox(self, values=self.profile_names, textvariable=self.profile)
        self.profile_dropdown.grid(row=3, column=2, columnspan=2, sticky="nsew", padx=5, pady=5)

        edit_profile_button = tk.Button(self, text="Edit", command=self.open_edit_profile_window)
        edit_profile_button.grid(row=3, column=4, padx=5, pady=5)

        new_profile_button = tk.Button(self, text="New", command=self.open_new_profile_window)
        new_profile_button.grid(row=3, column=5, padx=5, pady=5)

        self.export_all_checkbutton_var = tk.IntVar()
        export_all_checkbutton = ttk.Checkbutton(self, text="Export all Labels in Measurement (Takes a long time > 5 min!)", variable=self.export_all_checkbutton_var, command=self.all_label_checkbox_change)
        export_all_checkbutton.grid(row=4, column=2, sticky="wn", padx=5, pady=(5, 20))

        output_path_label = tk.Label(self, text="Output Path", justify="left")
        output_path_label.grid(row=5, column=1, sticky="w")

        self.output_path_entry = tk.Entry(self)
        self.output_path_entry.bind("<KeyRelease>", self.check_enable_export_button)
        self.output_path_entry.bind("<KeyRelease>", self.update_outpath, add="+")
        self.output_path_entry.grid(row=5, column=2, columnspan=2, sticky="nsew", padx=7, pady=7)

        self.output_browse_button = tk.Button(self, text="...", command=self.browse_output_path)
        self.output_browse_button.grid(row=5, column=4, columnspan=2, sticky="nsew", padx=5, pady=5)

        self.grid_rowconfigure(5, minsize=35)
        self.same_path_checkbox_var = tk.IntVar()
        same_path_checkbox = ttk.Checkbutton(self, text="Same as Measurement Path", variable=self.same_path_checkbox_var, command=self.same_path_checkbox_change)
        same_path_checkbox.grid(row=6, column=2, sticky="wn", padx=5, pady=(5, 20))

        export_format_label = tk.Label(self, text="Export Format", justify="left")
        export_format_label.grid(row=7, column=1, sticky="w")

        self.excel_checkbox_var = tk.IntVar()
        excel_checkbox = ttk.Checkbutton(self, text="Excel", variable=self.excel_checkbox_var, command=self.checkbox_on_change)
        excel_checkbox.grid(row=7, column=2, sticky="w", padx=5, pady=5)
        excel_checkbox.bind("<Button-1>", self.check_enable_export_button)

        self.matlab_checkbox_var = tk.IntVar()
        matlab_checkbox = ttk.Checkbutton(self, text="Matlab", variable=self.matlab_checkbox_var, command=self.checkbox_on_change)
        matlab_checkbox.grid(row=8, column=2, sticky="wn", padx=5, pady=(5, 20))

        raster_label = tk.Label(self, text="Raster", justify="left")
        raster_label.grid(row=9, column=1, sticky="w")

        values = {"1 s": 1,
                  "0.1 s": 0.1,
                  "0.01 s": 0.01,
                  "0.001 s": 0.001}
        self.raster_var = tk.DoubleVar()
        self.raster_var.set(0.1)
        for i, (text, value) in enumerate(values.items()):
            tk.Radiobutton(self, text=text, variable=self.raster_var, value=value, justify="left").grid(row=9+i, column=2, sticky="w")

        self.state_label = tk.Label(self, text="\n\n", wraplength=450)
        self.state_label.grid(row=13, column=2)

        self.export_button = tk.Button(self, text="Export", state="disabled", command=self.start_export)
        self.export_button.grid(row=14, column=4, columnspan=2, sticky="nsew", padx=5, pady=5)

    def extract_profile_names(self, profiles: list) -> list:
        """Extracts the name of all profiles

        Args:
            profiles (list): list of profiles

        Returns:
            list: list of profile names
        """
        return [profil["name"] for profil in profiles.values()]

    def event_measurement_path(self, event):
        """Executed when something happens in the measurement path text widget
        """
        self.meas_path = profile_manager.str_2_list(
            self.measurement_path_text.get("1.0", "end-1c"))
        self.update_outpath("event")
        self.check_enable_export_button("event")

    def browse_measurement_path(self):
        """Opens File dialog to select measurement files an stores them in the text widget
        """
        meas_path = filedialog.askopenfilename(
            filetypes=[("Measurement Files", "*.dat;*.mf4")], multiple=True)
        if len(meas_path) > 0:
            self.measurement_path_text.delete(1.0, tk.END)
            for file in meas_path:
                self.measurement_path_text.insert(tk.END, file + "\n")
            self.event_measurement_path("event")

    def browse_output_path(self):
        """Opens file dialog to select an output folder and stores it in the entry widget
        """
        path = filedialog.askdirectory()
        if len(path) > 0:
            self.output_path_entry.delete(0, tk.END)
            self.output_path_entry.insert(0, path)
        self.update_outpath("event")
        self.check_enable_export_button("event")

    def update_outpath(self, event):
        """Updates the internal output path and generates the output file name

        Args:
            event (_type_): unused
        """
        if self.same_path_checkbox_var.get() == 1:
            self.output_paths = [os.path.dirname(path) for path in profile_manager.str_2_list(self.measurement_path_text.get("1.0", "end-1c"))]
            self.output_path_entry.config(state="normal")
            self.output_path_entry.delete(0, tk.END)
            self.output_path_entry.insert(0, self.output_paths[0])
            self.output_path_entry.config(state="disabled")
        else:
            if len(profile_manager.str_2_list(self.measurement_path_text.get("1.0", "end-1c"))) > 0:
                self.output_paths = [self.output_path_entry.get()] * len(profile_manager.str_2_list(self.measurement_path_text.get("1.0", "end-1c")))
            else:
                self.output_paths = [self.output_path_entry.get()]
            self.output_path_entry.delete(0, tk.END)
            self.output_path_entry.insert(0, self.output_paths[0])
        if len(profile_manager.str_2_list(self.measurement_path_text.get("1.0", "end-1c"))) > 0:
            self.output_files = [os.path.splitext(os.path.basename(path))[0] + "_export" for path in profile_manager.str_2_list(self.measurement_path_text.get("1.0", "end-1c"))]


    def all_label_checkbox_change(self):
        """Disables the profile dropdown menu if all labels should be exported
        """
        if self.export_all_checkbutton_var.get() == 1:
            self.profile_dropdown.config(state="disabled")
        else:
            self.profile_dropdown.config(state="normal")

    def same_path_checkbox_change(self):
        """Disables the output path extry widget if the output path should correspond to the input path
        """
        self.update_outpath("event")
        if self.same_path_checkbox_var.get() == 1:
            self.output_path_entry.delete(0, tk.END)
            self.output_path_entry.insert(0, self.output_paths[0])
            self.output_browse_button.config(state="disabled")
            self.output_path_entry.config(state="disabled")
        else:
            self.output_browse_button.config(state="normal")
            self.output_path_entry.config(state="normal")
        self.check_enable_export_button("event")

    def checkbox_on_change(self):
        """start the check_enable_export_button function if an output filetype is selected
        """
        self.check_enable_export_button("event")

    def check_enable_export_button(self, event):
        """Check if an input path, output path and a file type is selected to enable the export button

        Args:
            event (_type_): unused
        """
        flg_disbl = False
        if self.output_path_entry.cget("state") == "disabled":
            self.output_path_entry.config(state="normal")
            flg_disbl = True
        path = profile_manager.str_2_list(
            self.measurement_path_text.get("1.0", "end-1c"))
        if bool(self.matlab_checkbox_var.get() or self.excel_checkbox_var.get()) and any(os.path.exists(datei) for datei in path) and len(self.output_path_entry.get()) > 0:
            self.export_button.config(state="normal")
        else:
            self.export_button.config(state="disabled")
        if flg_disbl:
            self.output_path_entry.config(state="disabled")

    def delete_temp_files(self):
        """Deletes temporary files which were created during execution
        """
        for meas in self.meas_path:
            files_to_delete = glob("C:/Temp/" + os.path.splitext(os.path.basename(meas))[0] + "*.mf4")
            for file in files_to_delete:
                os.remove(file)

    def open_new_profile_window(self):
        """Starts the class ProfileNew to create a new profile
        """
        ProfileNew(self)

    def open_edit_profile_window(self):
        """Starts the class ProfileEdit to edit a profile
        """
        ProfileEdit(self, self.profile.get(),self.all_profiles[self.profile.get()]["labels"])

    def update_profiles_dropdown(self, option: str):
        """Updates the profiles in the dropdown menu

        Args:
            option (list): string which should be displayed
        """
        self.profile_names = self.extract_profile_names(self.all_profiles)
        self.profile.set(option)
        self.profile_dropdown['values'] = self.profile_names

    def extract_signal_labels(self, measurement: str) -> list:
        """Extracts all labels in the measurement to a list

        Args:
            measurement (str): Path to measurement

        Returns:
            list: All signals present in the measurement
        """
        mdf = asammdf.MDF(measurement)
        all_channels = []

        for group in mdf.groups:
            for channel in group['channels']:
                if 'time' not in channel.name.split('\\')[0] and '$' not in channel.name.split('\\')[0]:
                    all_channels.append(channel.name.split('\\')[0])
        return all_channels

    def start_export(self):
        """Starts the main part of the tool, the export of the measurements and handles occuring errors
        """
        if self.profile.get() in self.profile_names:
            self.grab_set()
            for i, measurement in enumerate(self.meas_path):
                write_log_timestamp()
                if self.excel_checkbox_var.get():
                    self.update_state_label('Running Meas ' + str(i + 1) + ': ' + ' Excel Export')
                    try:
                        data = self.signals_to_dataframe(measurement)
                        data.to_excel((self.output_paths[i] + "/" + self.output_files[i] + ".xlsx"), index=False)
                        self.update_state_label('Finished')
                    except AttributeError as e:
                        self.update_state_label('Error Meas ' + str(i+1) + ': ' + 'There are no labels available for export.\n' + str(e))
                    except OSError as e:
                        if e.errno == 13:
                            self.update_state_label("Error Meas " + str(i+1) + ": " + "An Excel file with the same name is already opened. Please close the file.")
                        else:
                            self.update_state_label(['Error Meas ' + str(i+1) + ': ' + str(e)])
                    except IndexError as e:
                        self.update_state_label('Error Meas ' + str(i+1) + ': ' + 'The path to the measurement does not exist.\n' + str(e))
                    except ValueError as e:
                        self.update_state_label('Error Meas ' + str(i+1) + ': ' + 'There are no labels available for export.\n' + str(e))
                    except Exception as e:
                        self.update_state_label(['Error Meas ' + str(i+1) + ': ' + str(e)])

                if self.matlab_checkbox_var.get():
                    self.update_state_label('Running Meas ' + str(i + 1) + ': ' + ' Matlab Export')
                    try:
                        data = self.signals_to_dataframe(measurement)
                        data_dict = {}
                        for column in data.columns:
                            data_dict[column] = data[column].values.reshape(-1, 1)
                        savemat(self.output_paths[i] + "/" + self.output_files[i] + ".mat", data_dict, do_compression=False)
                        self.update_state_label('Finished')
                    except AttributeError as e:
                        self.update_state_label('Error Meas ' + str(i+1) + ': ' + 'There are no labels available for export.\n' + str(e))
                    except IndexError as e:
                        self.update_state_label('Error Meas ' + str(i+1) + ': ' + 'The path to the measurement does not exist.\n' + str(e))
                    except ValueError as e:
                        self.update_state_label('Error Meas ' + str(i+1) + ': ' + 'There are no labels available for export.\n' + str(e))
                    except Exception as e:
                        self.update_state_label(['Error Meas ' + str(i+1) + ': ' + str(e)])
            self.delete_temp_files()
            self.grab_release()
        else:
            tk.messagebox.showwarning(
                "Warning", "Unknown extraction profile. Please select a valid one")
            return

    def signals_to_dataframe(self, meas: str) -> DataFrame:
        """Converts the input signals of the measurement to a pandas DataFrame

        Args:
            meas (str): Path to measurement

        Returns:
            DataFrame: All values of the selected signals
        """
        if self.export_all_checkbutton_var.get() == 1:
            imp_sgnl = self.extract_signal_labels(meas)
        else:
            imp_sgnl = self.all_profiles[self.profile.get()]["labels"]

        dataset = mdf_transformer.MdfTransformer(meas_paths=meas, interpol_raster=self.raster_var.get(), signals=imp_sgnl)

        df_data = dataset.process(out_path=r"C:\temp", single_export=["DataFrame"], multiple_export=["MDF"])

        df_data = df_data.droplevel(0)
        df_data.reset_index(inplace=True)
        df_data.rename(columns={'timestamps': 'time'}, inplace=True)
        return df_data

    def update_state_label(self, input_text: str):
        """Updates the state label widget to the input string

        Args:
            input_text (str): Text for the label
        """
        self.grab_release()
        self.state_label.config(text=input_text)
        self.update()
        self.grab_set()


class ProfileNew(tk.Toplevel):
    """Class for the window to create a new profile 

    Args:
        tk (tk.Toplevel): Inherited from the class tk.toplevel
    """
    instance = None
    def __init__(self, root):
        """Initial function for the class ProfileNew
        """
        if ProfileNew.instance:
            return
        ProfileNew.instance = self
        
        super().__init__(root)
        self.title("New Profile")
        self.iconbitmap(root.iconbitmap())

        self.update_idletasks()
        self.width = 570
        self.height = 600
        x = self.winfo_x() + (self.winfo_width() - self.winfo_reqwidth()) / 2
        y = self.winfo_y() + (self.winfo_height() - self.winfo_reqheight()) / 2
        self.geometry("%dx%d+%d+%d" % (self.width, self.heigth, x/2, y/2))
        self.transient(root)

        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(5, minsize=63)

        self.title_label = tk.Label(self, text="Create New Profile", font=((), 12))
        self.title_label.grid(row=0, column=2, columnspan=4)

        name_label = tk.Label(self, text="Name of the profile:")
        name_label.grid(row=1, column=2, sticky="nw", padx=5, pady=5)

        self.name_entry = tk.Entry(self)
        self.name_entry.grid(row=2, column=2, columnspan=4, sticky="nsew", padx=5, pady=5)
        self.name_entry.bind("<KeyRelease>", self.enable_safe_button)

        signals_label = tk.Label(self, text="Signals:")
        signals_label.grid(row=3, column=2, sticky="nw", padx=5, pady=5)

        self.signals_text = tk.Text(self, width=20, font=("TkDefaultFont",))
        self.signals_text.grid(row=4, column=2, columnspan=4, sticky="nsew", padx=5, pady=5)
        self.signals_text.bind("<KeyRelease-Return>", self.check_double_label)
        self.signals_text.tag_configure("yellow", background="yellow")
        self.signals_text.tag_configure("red", background="red")

        scrollbar = tk.Scrollbar(self)
        scrollbar.grid(row=4, column=6, sticky="nsw", pady=5, padx=(0, 5))

        self.signals_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.signals_text.yview)

        warning_label = tk.Label(self,  justify="left", text="!!! The signal names must correspond to the signal names in the measurement !!!")
        warning_label.grid(row=5, column=2, sticky="w", columnspan=4, padx=5, pady=(5, 0))
        warning2_label = tk.Label(self,  justify="left", text="Each label must be placed in a new line.")
        warning2_label.grid(row=6, column=2, sticky="w", columnspan=4, padx=5, pady=(0, 5))

        load_from_meas_button = tk.Button(self, text="From Meas", command=self.load_signals_from_meas, width=10)
        load_from_meas_button.grid(row=7, column=3, padx=5, pady=5, sticky="e")

        cancel_button = tk.Button(self, text="Cancel", command=self.destroy, width=10)
        cancel_button.grid(row=7, column=4, padx=5, pady=5, sticky="e")

        self.save_button = tk.Button(self, text="Save", width=10, command=self.save_data)
        self.save_button.grid(row=7, column=5, columnspan=2,padx=5, pady=5, sticky="we")

        self.enable_safe_button("event")

            
    def check_double_label(self, event):
        """Check for doubled labels in text widget

        Args:
            event (_type_): unused
        """
        cursor_pos = self.signals_text.index(tk.INSERT)
        unique_values = []
        seen = set()
        for x in self.signals_text.get("1.0", "end-1c").split("\n"):
            if x not in seen:
                unique_values.append(x)
                if x != '':
                    seen.add(x)

        text = profile_manager.str_comma_2_newLine(profile_manager.list_2_str(unique_values))
        self.signals_text.delete("1.0", "end-1c")
        self.signals_text.insert("1.0", text)
        self.signals_text.mark_set(tk.INSERT, cursor_pos)


    def enable_safe_button(self, event):
        """Enable the safe button if a name is entered

        Args:
            event (_type_): unused
        """
        if len(self.name_entry.get()) > 0:
            self.save_button.config(state="normal")
        else:
            self.save_button.config(state="disabled")

    def save_data(self):
        """Save the entered data of the profile to the .json file. Checks if a profile already exists
        """
        if not self.name_entry.get() in app.profile_names:
            profile_manager.new_profile(self.name_entry.get(), profile_manager.str_2_list(self.signals_text.get("1.0", "end-1c")))
            app.update_profiles_dropdown(self.name_entry.get())
            self.destroy()
        elif self.name_entry.get() in app.profile_names:
            self.update_idletasks()
            tk.messagebox.showwarning("Warning", "The Profile " + self.name_entry.get() + " already exists!")

    def load_signals_from_meas(self):
        """Opens the left part of the window to select the labels present in the measurement
        """
        if app.meas_path:
            self.geometry("%dx%d" % (self.width*2, self.height))
            self.grid_columnconfigure(0, weight=4)
            
            self.title_label.grid(row=0, column=0, columnspan=7, padx=5, pady=5)
            text_label = tk.Label(self, text="Search for signals in the measurement:")
            text_label.grid(row=1, column=0, columnspan=2, sticky="nw", padx=5, pady=5)

            self.search_entry = tk.Entry(self)
            self.search_entry.grid(row=2, column=0, sticky="nwse", padx=5, pady=5)
            self.search_entry.bind("<KeyRelease>", self.search_label)

            label_lists = []
            for measurement in app.meas_path:
                label_lists.append(app.extract_signal_labels(measurement))

            merged_list = []
            for sublist in label_lists:
                merged_list.extend(sublist)

            self.labels = sorted(list(set(merged_list)), key=str.lower)
            self.marking_labels = []
            self.marking_labels = self.get_non_common_items(label_lists)

            self.listbox = tk.Listbox(self, selectmode='extended')
            self.listbox.grid(row=4, column=0,sticky="nwse", padx=5, pady=5)
            for label in self.labels:
                self.listbox.insert(tk.END, label)
            self.listbox.bind("<Double-Button-1>", self.select_label)
            self.listbox.bind("<Return>", self.select_label, add="+")

            self.signals_text.bind("<KeyRelease-Return>", self.mark_labels, add="+")
            self.mark_labels("event")

            scrollbar = tk.Scrollbar(self)
            scrollbar.grid(row=4, column=1,sticky="nsw", pady=5, padx=(0, 45))

            self.listbox.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=self.listbox.yview)

            hint_label = tk.Label(self, text="All red marked signals are not included in any measurement.", bg='red', justify="left")
            hint_label.grid(row=5, column=0, columnspan=2, sticky="w",  padx=5, pady=(5, 0))

            if len(self.marking_labels) > 0:
                hint2_label = tk.Label(self, text="All yellow marked signals are not included in all measurements.", bg='yellow', justify="left")
                hint2_label.grid(row=6, column=0, columnspan=2, sticky="w",  padx=5, pady=(0, 5))

            add_button = tk.Button(self, text="Add Signal -->")
            add_button.grid(row=7, column=0, columnspan=2, sticky="nwse", padx=(5, 45), pady=5)
            add_button.bind("<Button-1>", self.select_label)
        else:
            tk.messagebox.showwarning("Warning", "No measurement file has been selected. Please enter a measurement file first")

    def get_non_common_items(self, lists: list) -> list:
        """Get all labels which are not included in all measurements

        Args:
            lists (list): List of lists of labels from the measurement

        Returns:
            list: List with all relevant labels
        """
        all_items = [item for sublist in lists for item in sublist]
        non_common_items = [
            item for item in all_items if all_items.count(item) != len(lists)]
        return list(set(non_common_items))

    def mark_labels(self, event):
        """Marks all labels in the master list as well as in the profile list.
           labels which are not included in all measurements are marked yellow,
           lables which are not included in any measurement are marked red.

        Args:
            event (_type_): unused
        """
        for i in range(self.listbox.size()):
            if self.listbox.get(i) in self.marking_labels:
                self.listbox.itemconfig(i, {'bg': 'yellow'})
        self.mark_profile_labels("yellow", self.marking_labels, False)
        self.mark_profile_labels("red", self.labels, True)

    def mark_profile_labels(self, marking_profile: str, marking_labels: list, invert: bool):
        """Mark the labels in the profile list

        Args:
            marking_profile (str): marking_profile specified in the load_signals_from_meas function
            marking_labels (list): list of labels to mark
            invert (bool): bool to indicate whether all labels in the list should be marked, or all labels that are not included in the list 
        """
        self.signals_text.tag_remove(marking_profile, "1.0", "end")
        text_content = self.signals_text.get("1.0", "end-1c")
        lines = text_content.split("\n")
        if not invert:
            for word in marking_labels:
                if word in lines:
                    start = "1.0"
                    while True:
                        pos = self.signals_text.search(word, start, stopindex="end", nocase=1, regexp=False, elide=False)
                        if not pos:
                            break
                        start = pos + "+1c"
                        end = pos + f"+{len(word)}c"
                        line_number = pos.split('.', maxsplit=1)[0]
                        if lines[int(line_number)-1].find(word) != -1:
                            self.signals_text.tag_add(marking_profile, pos, end)
        if invert:
            for word in lines:
                if word not in marking_labels:
                    start = "1.0"
                    while True:
                        pos = self.signals_text.search((word+"\n"), start, stopindex="end", nocase=1, regexp=False, elide=False)
                        if not pos:
                            break
                        start = pos + "+1c"
                        end = pos + f"+{len(word)}c"
                        line_number = pos.split('.', maxsplit=1)[0]
                        if lines[int(line_number)-1].find(word) != -1:
                            self.signals_text.tag_add(marking_profile, pos, end)

    def search_label(self, event):
        """searches for labels with the pattern from the entry widget in the list widget

        Args:
            event (_type_): unused
        """
        search_text = self.search_entry.get().replace("*", ".*").replace("[", "\[").replace("]", "\]")
        self.listbox.delete(0, tk.END)
        for label in self.labels:
            if re.search(search_text, label, re.IGNORECASE):
                self.listbox.insert(tk.END, label)
        self.mark_labels("event")

    def select_label(self, event):
        """copies a selected label from the master list to the profile list

        Args:
            event (_type_): unused
        """
        selected_indices = self.listbox.curselection()
        selected_label = [self.listbox.get(index)for index in selected_indices]
        new_text = ()
        for label in selected_label:
            if label not in self.signals_text.get("1.0", "end-1c"):
                if self.signals_text.get("1.0", "end-1c"):
                    new_text = self.signals_text.get(
                        "1.0", "end-1c") + "\n" + label
                else:
                    new_text = label
                self.signals_text.delete("1.0", "end")
                self.signals_text.insert("1.0", new_text)
                self.signals_text.see("end")
        self.mark_profile_labels("yellow", self.marking_labels, False)
        self.mark_profile_labels("red", self.labels, True)

    def destroy(self):
        ProfileNew.instance = None
        super().destroy()


class ProfileEdit(ProfileNew):
    """Class for window to edit the profile. Inherits from the ProfileNew class

    Args:
        ProfileNew (_type_): parent class ProfileNew
    """
    def __init__(self, root, name: str, labels: list):
        if ProfileNew.instance:
            return

        super().__init__(root)
        ProfileNew.instance = self

        self.title("Edit Profile")
        self.title_label.config(text='Edit profile')
        self.old_name = name
        self.name_entry.insert(0, self.old_name)
        self.enable_safe_button("event")
        self.signals_text.insert("1.0", profile_manager.str_comma_2_newLine(profile_manager.list_2_str(labels)))
        self.delete_button = tk.Button(self, text="Delete", width=10, command=self.delete_data)
        self.delete_button.grid(row=7, column=2, padx=5, pady=5, columnspan=2, sticky='w')

    def save_data(self):
        """Updates the data of the profile in the .json file
        """
        profile_manager.edit_profile(self.old_name, self.name_entry.get(
        ), profile_manager.str_2_list(self.signals_text.get("1.0", "end-1c")),  app.profile_names)
        app.all_profiles = profile_manager.load_profiles()
        app.profile_names = app.extract_profile_names(app.all_profiles)
        app.update_profiles_dropdown(self.name_entry.get())
        self.destroy()

    def delete_data(self):
        """Delete the profile from the .json file
        """
        confirmed = tk.messagebox.askokcancel("Delete", "Do you really want to delete the profile?")
        if confirmed:
            profile_manager.del_profile(self.name_entry.get())
            app.update_profiles_dropdown(app.profile_names[0])
            self.destroy()


def check_json_file():
    """Checks if a profiles.json file exists, otherwise creates a new file with a default profile

    Args:
        root (tk.Tk): Tkinter object for the message box window
    """
    if not os.path.exists(JSON_PATH):
        write_log_timestamp()
        root = tk.Tk()
        root.withdraw()
        response = tk.messagebox.askyesno("Warning", "The json file with the export profiles was not found.\nShould a new file be created?\n\n")
        root.grab_set() 
        if response:
            sys.stdout.write(f"\nNo profiles.json file found. Created a new one.")
            profile_manager.profile_data = {}
            neues_profile = {
                "name": "Default",
                "labels": [
                    "VehV_v"
                ]
            }
            profile_manager.PROFILE_DATA['Default'] = neues_profile
            with open(JSON_PATH, 'w') as file:
                profile_manager.json.dump(profile_manager.PROFILE_DATA, file, indent=4)
            root.destroy()
        else:
            sys.stdout.write(f"No profiles.json file found. Exit execution.")
            root.destroy()
            sys.exit()


def limit_lines(file_path: str, max_lines: int):
    """Limitate the logfile to a maximum number of lines.

    Args:
        file_path (str): Path to logfile
        max_lines (int): maximum number of lines
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()
    with open(file_path, 'w') as file:
        file.writelines(lines[-max_lines:])

def write_log_timestamp():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sys.stdout.write(f"\n{timestamp}")


if __name__ == "__main__":
    log_file = open(LOG_FILE_PATH, 'a', encoding="utf-8")
    sys.stdout = log_file
    sys.stderr = log_file

    check_json_file()

    app = MeasurementGUI()
    app.mainloop()

    if log_file:
        log_file.close()
    limit_lines(LOG_FILE_PATH, max_lines=500)
