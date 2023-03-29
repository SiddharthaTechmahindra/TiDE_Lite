import os
import warnings
import pandas as pd
import streamlit as st
from ppadb.client import Client
from time import strftime, localtime
from st_aggrid import AgGrid, GridUpdateMode
from st_aggrid.grid_options_builder import GridOptionsBuilder
from utilites.Utilities import write_file_contents, clear_files, latest_file, get_file_contents
import robot
import logging
import threading
from showscreen import show_screen
import streamlit.components.v1 as components
warnings.filterwarnings("ignore", category=DeprecationWarning)


class StreamlitUI:
    def __init__(self, path):
        self.__adb_client = None
        self.__host = 'localhost'
        self.__port = 5037
        self.__cur_dir = os.getcwd()
        self.__config_path = os.path.join(self.__cur_dir, 'config', 'temp_folders',path)
        self.__run_path = os.path.join(self.__cur_dir, 'runs')
        self._test_case_data_frame = None
        self.__device_details_data_frame = None
        self.__main_menus = ["Select Device", "Test Run", "Reports"]
        self.__placeholder = st.empty()
        self.__sidebar_placeholder = st.sidebar.empty()
        self.__session_list = []
        self.__thread_list=[]
        self.ui_manager()

    @staticmethod
    def __next_page():
        logging.info("Going To Next Page")
        st.session_state.page += 1

    def __reset(self):
        for driver in self.__session_list:
            st.sidebar.write(driver)
            driver.quit()
        self.__session_list.clear()
        st.session_state.page = 0

    def get_device_details(self):
        logging.info("Fetching Device Details")
        self.__adb_client = Client(host=self.__host, port=self.__port)
        connected_devices = self.__adb_client.devices()
        self.__device_details_data_frame = pd.DataFrame({
            'Device Name': [str(device.get_properties()["ro.product.manufacturer"]) + " " +
                            str(device.get_properties()["ro.product.model"]) for device in connected_devices],
            'Platform': [device.get_properties()["net.bt.name"] for device in connected_devices],
            'Version': [device.get_properties()["ro.build.version.release"] for device in connected_devices],
            'Serial no.': [device.get_serial_no() for device in connected_devices]})

    def __confirm_device_manager(self, **grid_table):

        if len(grid_table["table"]["selected_rows"]) == 0:
            logging.error("No Devices Selected")
            st.sidebar.warning("Select least 1 device")

        else:
            logging.info("In device manager")
            selected_row = pd.DataFrame(grid_table["table"]["selected_rows"])[["Device Name", "Platform", 'Version','Serial no.']]
            device = [sel_item.strip() for sel_item in selected_row["Device Name"]]
            st.sidebar.write("#")
            st.sidebar.success("Selected devices are " + ",".join(device))
            to_str = "Select Device\n"  # the names are supposed to be consistent with main_menus
            to_str += "\n".join(device)
            devices_info_file = os.path.join(self.__config_path, 'devices.txt')
            write_file_contents(devices_info_file, to_str)
            mode = 0o777
            time_str = strftime("%e_%m_%G_%H_%M_%S", localtime())
            os.mkdir(os.path.join(self.__run_path, 'run_' + time_str), mode)
            temp_dir = os.path.join(self.__run_path, 'run_' + time_str)
            os.mkdir(os.path.join(temp_dir, 'logs'), mode)
            selected_row.to_excel(os.path.join(temp_dir, "devices.xlsx"), index=False)
            #t1 = threading.Thread(target=show_screen, args=(temp_dir,))
            #t1.start()

            #self.__thread_list.append(t1)
            print(self.__thread_list)
            #show_screen(temp_dir)
            self.__run_path = temp_dir
            self.__next_page()

    def __device_manager(self):
        # temp_dir = latest_file(self.__run_path)
        logging.info("Device Manager")

        st.header("Device Selection")
        self.get_device_details()

        if len(self.__device_details_data_frame) == 0:
            st.error("No Devices found")
            logging.critical("No Devices Found")
        else:
            gd = GridOptionsBuilder.from_dataframe(self.__device_details_data_frame)
            gd.configure_selection(selection_mode='multiple', use_checkbox=True, header_checkbox=True)
            grid_options = gd.build()
            grid_table = AgGrid(self.__device_details_data_frame, height=400, gridOptions=grid_options, width=400,
                                update_mode=GridUpdateMode.SELECTION_CHANGED)
            st.button("Create New Run >> ", on_click=self.__confirm_device_manager, kwargs={"table": grid_table})

    def __confirm_reporter(self):
        logging.info("Reporter Confirmed")
        #print("Reporter confirmed")
        #freeup()

        write_file_contents(os.path.join(self.__config_path, "reports.txt"), "Reports")
        self.__reset()

    def to_html(self,path,height,width):
        logging.info("To HTML")
        HtmlFile = open(path, 'r', encoding='utf-8')
        source_code = HtmlFile.read()
        #print(source_code)
        components.html(source_code, height=height, width=width)

    def __reporter(self):
        logging.info("Reports section")
        st.title("Reports")


        report_columns = ['Output', 'Report', 'Log']
        path = os.path.join(self.__run_path, latest_file(self.__run_path), 'logs')
        folders = os.listdir(path)
        names = [name.replace("_", " ") for name in folders]
        dev_tab=st.tabs(names)
        for tab,folder,name in zip(dev_tab,folders,names):
            with tab:
                output_tab, report_tab, log_tab = st.tabs(report_columns)

                with output_tab:
                    output=get_file_contents(os.path.join(path,folder,"log.txt"))
                    st.code("\n".join(output))

                with report_tab:
                    self.to_html(os.path.join(path,folder,"report.html"),height=500,width=850)

                with log_tab:
                    self.to_html(os.path.join(path, folder, "log.html"), height=2000, width=850)




        st.button("Close", on_click=self.__confirm_reporter)

    def __confirm_test_manager(self, **grid_table):

        if len(grid_table["table"]["selected_rows"]) != 0:
            selected_row = pd.DataFrame(grid_table["table"]["selected_rows"])[['ID', 'Test Case', 'Section','Comments', 'Feasibility']]
            logging.info("Test manager confirmed")
            last = latest_file(self.__run_path)
            run_directory=os.path.join(self.__run_path,last)
            log_directory=os.path.join(run_directory, 'logs')
            to_exec=list(selected_row['Test Case'])
            df_devices=pd.read_excel(os.path.join(run_directory,'devices.xlsx'))
            device_name=list(df_devices['Device Name'])
            device_serial=list(df_devices['Serial no.'])

            for name,serial in zip(device_name,device_serial):
                os.mkdir(os.path.join(log_directory,name.replace(" ","_")))
                temp=os.path.join(log_directory,name.replace(" ","_"))
                log = open(os.path.join(temp,"log.txt"), "w")
                robot.run(os.path.join(os.getcwd(),'robot_files','applaunch.robot'), stdout=log,include=to_exec,outputdir=temp,variable="DeviceID:"+serial)
            path = os.path.join(self.__run_path, last, "test_run.xlsx")
            write_file_contents(os.path.join(self.__config_path, "Run_Info.txt"), "Test Run\n")
            selected_row.to_excel(path, index=False)
            st.sidebar.write("#")
            st.sidebar.success("Run Completed File in " + path)
            self.__sidebar_placeholder.empty()
            self.__next_page()
        else:
            logging.error("No test cases selected")
            st.error("Select At least 1 testcase")

    def __get_test_case_details(self):
        # TODO : Get file path from user using file browser
        file = st.file_uploader("upload Excel file", type=[".xlsx", ".xls"])
        if file:
            logging.info("File Uploaded")
            self._test_case_data_frame = pd.read_excel(file,'goHUNTMobileApp')[['Unnamed: 1', 'Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4', 'Unnamed: 5', 'Unnamed: 6']]
            self._test_case_data_frame = self._test_case_data_frame.drop(index=[0])
            self._test_case_data_frame.rename(columns=self._test_case_data_frame.iloc[0], inplace=True)
            self._test_case_data_frame = self._test_case_data_frame.iloc[1:, :]
            self._test_case_data_frame = self._test_case_data_frame[self._test_case_data_frame['Feasibility'] == "Yes"]
            columns = ['Section']

            tabs = st.sidebar.tabs(columns)
            selected = {}
            option_values = {}
            for tab, column in zip(tabs, columns):
                unique_column_values = [item for item in self._test_case_data_frame[column]
                                        if not (pd.isnull(item)) is True]
                unique_column_values = pd.unique(unique_column_values)
                for option in unique_column_values:
                    option_value = tab.checkbox(option)
                    if option_value is True:
                        option_values[option] = option_value
                selected[column] = option_values

                for tab_selected in selected:
                    for selection in selected[tab_selected]:
                        if selected[tab_selected][selection] is True:
                            opt = list(selected[tab_selected].keys())
                            self._test_case_data_frame = self._test_case_data_frame[
                                self._test_case_data_frame[tab_selected].isin(opt)]

    def __run_manager(self):
        st.title("Test Run")
        logging.info("Run Manager")
        self.__get_test_case_details()
        if self._test_case_data_frame is not None:
            gd = GridOptionsBuilder.from_dataframe(self._test_case_data_frame)
            gd.configure_selection(selection_mode='multiple', use_checkbox=True)
            gd.configure_column("ID", headerCheckboxSelection=True)
            grid_options = gd.build()
            grid_table = AgGrid(self._test_case_data_frame, height=1000, width=600, gridOptions=grid_options,
                                update_mode=GridUpdateMode.SELECTION_CHANGED)
            st.button("Confirm", kwargs={"table": grid_table}, on_click=self.__confirm_test_manager)

    def ui_manager(self):

        logging.info("Main Screen")
        if "page" not in st.session_state:
            st.session_state.page = 0

        if st.session_state.page == 0:
            self.__device_manager()

        if st.session_state.page == 1:
            if "Select Device" in get_file_contents(os.path.join(self.__config_path, "devices.txt")):
                self.__run_manager()

        if st.session_state.page == 2:
            if "Test Run" in get_file_contents(os.path.join(self.__config_path, "Run_Info.txt")):
                self.__reporter()

        for itr in range(14):
            st.sidebar.write("#")

        if st.sidebar.button("Reset", on_click=self.__reset, ):
            clear_files(self.__config_path)
            pass
