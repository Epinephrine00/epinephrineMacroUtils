from __future__ import annotations

from ppadb.client import Client as AdbClient
from ppadb.device import Device
from PIL import Image
import numpy as np
import io


class ADBDevice:
    
    def __init__(self) :
        print('ADBTest ready')
        self.deviceSelector = 0

        self.work_start()

    def connect(self):
        print('ADB : : Connect Method Called!\n\n====================================================================')
        self.client = AdbClient(host="127.0.0.1", port=5037) # Default is "127.0.0.1" and 5037

        self.setDevice()
        print(f'device: {self.device}')
        print(f'client: {self.client}')
        return self.device, self.client
    def setDevice(self):
        self.devices = self.client.devices()
        if len(self.devices) == 0:
            print('No devices')
            quit()
        self.device = self.devices[self.deviceSelector]
    
    def deviceInfo(self, deviceSelector = 0):
        model = self.devices[deviceSelector%len(self.devices)].shell('getprop ro.product.model').strip()
        serial = self.devices[deviceSelector%len(self.devices)].serial
        return (model, serial)
    

    #20240607 수정 : 갤럭시 폴드 5에서 발생하는 멀티스크린 오류를 해결하였음
    def screencap(self, device, displayId):
        conn = device.create_connection()

        with conn:
            cmd = f"shell:/system/bin/screencap -p -d {displayId}"
            conn.send(cmd)
            result = conn.read_all()

        if result and len(result) > 5 and result[5] == 0x0d:
            return result.replace(b'\r\n', b'\n')
        else:
            return result
                
    def device_screen_capture(self, deviceSelector = 0, filename = 'screen.png'):
        getids = self.devices[deviceSelector%len(self.devices)].shell('dumpsys SurfaceFlinger --display-id').strip().split('\n')
        ids = []
        for i in range(len(getids)):
            ids.append(getids[i].split()[1])

        if len(ids)<2:
            result = self.devices[deviceSelector%len(self.devices)].screencap()
        else:
            print('adb : multiscreen detected!')
            maxval = 0
            for i in range(len(ids)):
                result_ = self.screencap(self.devices[deviceSelector%len(self.devices)], ids[i])
                byte_stream = io.BytesIO(result_)
                image = Image.open(byte_stream)
                image_array = np.array(image)
                mean_pixel_value = np.mean(image_array)
                print('adb : screen mean value - screen',i, ':', mean_pixel_value)
                if mean_pixel_value>maxval:
                    maxval = mean_pixel_value
                    result = result_
        with open(filename, 'wb') as fp:
            fp.write(result)
        print('adb : screen captured')
        
    def work_start(self):
        self.connect()
        #device, client = self.connect()
        #self.device = device
        self.device_screen_capture()
        
    def click(self, x:int|tuple, y:int = 0, deviceSelector = 0):
        if type(x)==type(tuple()):
            cmd = 'input touchscreen tap '+str(x[0])+' '+str(x[1])
            self.devices[deviceSelector%len(self.devices)].shell(cmd)
            print('adb : clicked on : ('+str(x[0])+', '+str(x[1])+')')
        else:
            cmd = 'input touchscreen tap '+str(x)+' '+str(y)
            self.devices[deviceSelector%len(self.devices)].shell(cmd)
            print('adb : clicked on : ('+str(x)+', '+str(y)+')')
    def swipe(self, x1, y1, x2, y2, dur = 100, deviceSelector = 0):
        cmd = 'input swipe '+str(x1)+' '+str(y1)+' '+str(x2)+' '+str(y2)+' '+str(int(dur))
        self.devices[deviceSelector%len(self.devices)].shell(cmd)
        print('adb : swiped from : ('+str(x1)+', '+str(y1)+') to : ('+str(x2)+', '+str(y2)+') while : '+str(int(dur)))

    def typing(self, key:int|str, deviceSelector = 0):
        '''typing for othre keyboards...(legacy)'''
        if type(key)==type(int()):
            cmd = 'input keyevent '+str(key)
        else:
            cmd = 'input text '+key
        self.devices[deviceSelector%len(self.devices)].shell(cmd)
        print('adb : (legacytyping) typed : '+str(key))
    
    def getRecentMesseges(self, count = 5, deviceSelector = 0):
        result = self.devices[deviceSelector%len(self.devices)].shell('content query --uri content://sms/inbox --projection "_id, address, date, body"')
        messages = []

        print(result[:10])
        #for line in result.splitlines()[:count]:
        i= 1
        while i<count+1:
            line = result.strip().split('Row: ')[i]
            print('line :' ,line)
            messages.append(line)
            #messages.append(line.split(', body=')[1])
            i+=1


        return messages
    

    def getLayoutXML(self, deviceSelector = 0):
        self.devices[deviceSelector%len(self.devices)].shell('uiautomator dump /sdcard/ui_dump.xml')
        self.devices[deviceSelector%len(self.devices)].pull('/sdcard/ui_dump.xml', 'ui_dump.xml')

    def isInstalled(self, packageName:str, deviceSelector=0) -> bool:
        if packageName in self.devices[deviceSelector%len(self.devices)].shell("pm list packages"):
            return True
        else:
            return False




if __name__ == "__main__":
    ADBbot = ADBDevice()
    ADBbot.work_start()
    serial = ADBbot.deviceInfo()[1]
    import uiautomator2 as ua
    automator = ua.connect(serial)
    #ADBbot.device_screen_capture()
    #print(ADBbot.deviceInfo())
    #print(ADBbot.getRecentMesseges())
    import time
    from tqdm import tqdm
    s = []
    for i in tqdm(range(100)):
        a = time.time()
        #b = automator.dump_hierarchy(True)
        #automator.click(100, 100)
        automator.touch.down(100, 100)
        automator.touch.up(100, 100)
        s.append(time.time()-a)
    #print(b)
    print(sum(s)/len(s))
    exit()

# A30 : 0.30358870029449464
# fold3 : 0.2740490412712097
# fold3_comp : 0.18860352516174317
    
# click
# click 0.20617069482803344
# down_up 0.14834624290466308