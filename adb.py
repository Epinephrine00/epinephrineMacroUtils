from __future__ import annotations

from ppadb.client import Client as AdbClient

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
    
    def deviceInfo(self):
        model = self.device.shell('getprop ro.product.model').strip()
        serial = self.device.serial
        return (model, serial)
                
    def device_screen_capture(self, filename = 'screen.png'):
        result = self.device.screencap()
        with open(filename, 'wb') as fp:
            fp.write(result)
        print('adb : screen captured')
        
    def work_start(self):
        self.connect()
        #device, client = self.connect()
        #self.device = device
        self.device_screen_capture()
        
    def click(self, x:int|tuple, y:int = 0):
        if type(x)==type(tuple()):
            cmd = 'input touchscreen tap '+str(x[0])+' '+str(x[1])
            self.device.shell(cmd)
            print('adb : clicked on : ('+str(x[0])+', '+str(x[1])+')')
        else:
            cmd = 'input touchscreen tap '+str(x)+' '+str(y)
            self.device.shell(cmd)
            print('adb : clicked on : ('+str(x)+', '+str(y)+')')
    def swipe(self, x1, y1, x2, y2, dur = 100):
        cmd = 'input swipe '+str(x1)+' '+str(y1)+' '+str(x2)+' '+str(y2)+' '+str(int(dur))
        self.device.shell(cmd)
        print('adb : swiped from : ('+str(x1)+', '+str(y1)+') to : ('+str(x2)+', '+str(y2)+') while : '+str(int(dur)))

if __name__ == "__main__":
    ADBbot = ADBDevice()
    ADBbot.work_start()
    ADBbot.device_screen_capture()
    print(ADBbot.deviceInfo())
    exit()

    