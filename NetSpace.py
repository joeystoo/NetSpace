# netspace - a gamified network simulator
# by Joey S. (https://github.com/joeystoo)
# copyrighted 2026 ©

# IMPORTS
import time
import random
import pygame
import sys
deviceRegistry = {}
gameLog = []
# ESSENTIAL FUNCTIONS
def ipObj(IP):
    return deviceRegistry.get(IP)
def gameTick():
    devices = deviceRegistry.values()
    for device in devices:
        device.process()
    for device in devices:
        device.queue = device.incoming
        device.incoming = []
def log(string, var):
    var.append(string)
    if len(var) > 10:
        var.pop(0)


# DEVICE BEHAVIOURS
def endPointBehaviour(device):
    if not hasattr(device, "ARPTable"):
           device.ARPTable = {}
    while device.queue:
        origin, frame = device.queue.pop(0)
        if frame.etherType == "0x0800":
            packet = frame.payload
            log(f"Device {device.IP} received IP packet from {packet.src}: {packet.content}", gameLog)
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
    if not hasattr(device, "ARPWait"):
        device.ARPWait = []
    randomIP = random.randint(1234, 1235)
    if randomIP != device.IP:
        if randomIP not in device.ARPTable:
            sendingPacket = IPPacket(device.IP, randomIP, "helllo!")
            sendingFrame = Frame(device.MAC, "FF:FF:FF:FF:FF:FF" , "0x0800", sendingPacket)
            device.ARPWait.append(sendingFrame)
            ARPreq = ARPPacket(1, device.MAC, device.IP, None, randomIP)
            ARP = Frame(device.MAC, "FF:FF:FF:FF:FF:FF" , "0x0806", ARPreq)
            for port in device.ports.values():
                device.send(port.name, ARP)
        else:
            sendingPacket = IPPacket(device.IP, randomIP, "helllo!")
            destMAC = device.ARPTable[randomIP]
            sendingFrame = Frame(device.MAC, destMAC, "0x0800", sendingPacket)
            for port in device.ports.values():
                device.send(port.name, sendingFrame)
    for waiting in device.ARPWait[:]:
        if waiting.payload.dest in device.ARPTable:
            destMAC = device.ARPTable[waiting.payload.dest]
            waiting.destMAC = destMAC
            for port in device.ports.values():
                device.send(port.name, waiting)
                break
            device.ARPWait.remove(waiting)

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
# NET SIMULATION
class Device:
    def __init__(self, IP, MAC, devType):
        self.type = devType
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
        self.type(self)

class Port:
    def __init__(self, parent, name):
        self.parent = parent
        self.linkTo = None
        self.name = name
    def link(self, port):
        self.linkTo = port
# PACKET STRUCTURES
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
# HELPER FUNCTIONS
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

newDevice(1234, "01:23", endPointBehaviour)
addPort(1234, "p1")
newDevice(1235, "45:67", endPointBehaviour)
addPort(1235, "p1")
connect(1235, "p1", 1234, "p1")

# INIT
pygame.init()
displayInf = pygame.display.Info()
screen_width = displayInf.current_w
screen_height = displayInf.current_h
width = 800
height = 800
screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
font = pygame.font.SysFont(None, 24)
pygame.display.set_caption("NetSpace")
clock = pygame.time.Clock()
# TIMING SETUP
framerate = 60
tickrate = 5
frameCount = 0

running = True

# MAIN LOOP
while running:
    frameCount = frameCount + 1
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            width, height = event.size
            screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
    # logic
    if frameCount >= framerate/tickrate:
        frameCount = 0
        gameTick()
    screen.fill((0, 0, 0))
    # drawing
    padding = 10
    y = padding
    for line in gameLog[:]:
        surf = font.render(str(line), True, (255, 255, 255))
        screen.blit(surf, (padding, y))
        y += surf.get_height() + 2
    pygame.display.flip()
    clock.tick(framerate)

pygame.quit()
sys.exit()