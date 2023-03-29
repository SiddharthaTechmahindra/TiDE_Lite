import os
import subprocess
import pandas as pd
import multiprocessing

process_list=[]

def show_device(dev_id):
    print("Start for device "+dev_id)
    subprocess.run(["scrcpy", "--serial", dev_id])
    print("End for device " + dev_id)



def show_screen(path):

    dev_df = pd.read_excel(os.path.join(path, 'devices.xlsx'))
    serial = list(dev_df['Serial no.'])
    pool = multiprocessing.Pool()
    #print(pool)
    process_list.append(pool)
    screen = pool.map_async(show_device, serial)
    screens = screen.get()
    print("Output: {}".format(screens))



