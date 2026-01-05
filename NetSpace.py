import time
from collections import deque
TICK_TIME = 1
deviceRegistry = {}
def ipObj(IP):
    return deviceRegistry.get(IP)
def tick():
    devices = deviceRegistry.values()
    for device in devices:
        device.process()
    for device in devices:
        device.queue = device.incoming
        device.incoming = []
#device behavours
def endPointBehaviour(device):
    if not hasattr(device, "ARPTable"):
            device.ARPTable = {}
    while device.queue:
        origin, frame = device.queue.pop(0)
        if frame.etherType == "0x0800":
            packet = frame.payload
            print(f"Device {device.IP} received IP packet from {packet.src}: {packet.content}")
        elif frame.etherType == "0x0806":
            ARP = frame.payload
            if ARP.op == 1:
                device.ARPTable[ARP.senderIP] = ARP.senderMAC
                if ARP.targetIP == device.IP:
                    packet = ARPPacket(2, device.MAC, device.IP, ARP.senderMAC, ARP.senderIP)
                    sendFrame = Frame(device.MAC, ARP.senderMAC, "0x0806", packet)
                    device.send(origin, sendFrame)
            elif ARP.op == 2:
                device.ARPTable[ARP.senderIP] = ARP.senderMAC


def hubBehaviour(device):
    while device.queue:
        origin, frame = device.queue.pop(0)
        for portName, port in device.ports.items():
            if portName != origin and port.linkTo != None:
                port.linkTo.parent.incoming.append((port.linkTo.name, frame))

def switchBehaviour(device):
    if not hasattr(device, "CAMTable"):
            device.CAMTable = {}
    while device.queue:
        origin, frame = device.queue.pop(0)
        device.CAMTable[frame.srcMAC] = origin
        if frame.destMAC == "FF:FF:FF:FF:FF:FF" or frame.destMAC not in device.CAMTable:
            for port in device.ports.values():
                if port.name != origin and port.linkTo != None:
                    port.linkTo.parent.incoming.append((port.linkTo.name, frame))
        else:
            outName = device.CAMTable[frame.destMAC]
            outPort = device.ports.get(outName)
            if outPort and outPort.linkTo:
                outPort.linkTo.parent.incoming.append((outPort.linkTo.name, frame))

class Device:
    def __init__(self, IP, MAC, device_type):
        self.type = device_type
        self.ports = {}
        self.IP = IP
        self.MAC = MAC
        self.incoming = []
        self.queue = []
        deviceRegistry[IP] = self
    
    def addPort(self, name):
        self.ports[name] = Port(self, name)
    
    def connect(self, startName, device, endName):
        start = self.ports.get(startName)
        end = device.ports.get(endName)
        if start is None or end is None:
            print("Error: Port not found")
            return
        start.link(end)
        end.link(start)
    
    def disconnect(self, startName, device, endName):
        start = self.ports.get(startName)
        end = device.ports.get(endName)
        if start is None or end is None:
            print("Error: Port not found")
            return
        start.link(None)
        end.link(None)
    
    def send(self, name, frame):
        port = self.ports.get(name)
        if port is None:
            print("Error: Port not found")
            return
        if port.linkTo is None:
            print("Error: Port not connected")
            return
        port.linkTo.parent.incoming.append((port.linkTo.name, frame))

    def process(self):
        self.send("p1", Frame(self.MAC, "FF:FF:FF:FF:FF:FF", "0x0800", IPPacket(self.IP, None, "Who has IP?")))


        
class Port:
    def __init__(self, parent, name):
        self.parent = parent
        self.linkTo = None
        self.name = name
    def link(self, port):
        self.linkTo = port
class Frame:
    def __init__(self, srcMAC, destMAC, etherType, payload):
        self.srcMAC = srcMAC
        self.destMAC = destMAC
        self.etherType = etherType
        self.payload = payload
class IPPacket:
    def __init__(self, src, dest, content):
        self.src = src
        self.dest = dest
        self.content = content
class ARPPacket:
    def __init__(self, op, senderMAC, senderIP, targetMAC, targetIP):
        self.op = op
        self.senderMAC = senderMAC
        self.senderIP = senderIP
        self.targetMAC = targetMAC
        self.targetIP = targetIP
#command managing code yaya fun
def newDevice(IP, MAC, device_type):
    Device(IP, MAC, device_type)
def addPort(IP, name):
    ipObj(IP).addPort(name)
def connect(IP1, port1, IP2, port2):
    ipObj(IP1).connect(port1, ipObj(IP2), port2)
def disconnect(IP1, port1, IP2, port2):
    ipObj(IP1).disconnect(port1, ipObj(IP2), port2)
def sendIP(IP, port, frame):
    ipObj(IP).send(port, frame)

newDevice(1234, "01:23", "router")
addPort(1234, "p1")
newDevice(5678, "45:67", "router")
addPort(5678, "p1")
connect(1234, "p1", 5678, "p1")
sendIP(1234, "p1", Frame(None, None, "0x0800", IPPacket(None, None, "hiiiiiii!")))

while True:
    start = time.perf_counter()
    tick()
    elapsed = time.perf_counter() - start
    sleepTime = TICK_TIME - elapsed
    if sleepTime > 0:
        time.sleep(sleepTime)