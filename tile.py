import os
import sys
import math
import platform
from datetime import datetime
from xml.dom import minidom
from urllib import request
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtGui import QImage,QPainter,QPixmap,qRgba
from PyQt5.QtWidgets import QWidget,QGridLayout,QMenuBar,QAction,QMainWindow,QSizePolicy,QFileDialog
from PyQt5.QtCore import Qt

def readGPX():
    gpxtrkpt = []
    dlg = QFileDialog()
    dlg.setFileMode(QFileDialog.ExistingFile)
    if dlg.exec_():
        filenames = dlg.selectedFiles()
        try:
            for file in filenames:
                xmldoc = minidom.parse(file)
                #
                itemlst = xmldoc.getElementsByTagName("trkpt")
                for item in itemlst:
                    ele = "0.0"
                    elevations = item.getElementsByTagName("ele")
                    for elevation in elevations:
                        ele = elevation.firstChild.data
                    tim = ""
                    times = item.getElementsByTagName("time")
                    for time in times:
                        tim = time.firstChild.data
                    lat = item.attributes['lat'].value
                    lon = item.attributes['lon'].value
                    gpxtrkpt.append((float(lat),float(lon),ele,tim))
                    #print(lat,lon,ele,tim)
        except:
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])
    return gpxtrkpt
        
def saveGPX(gpxtrkpt):
    gpxdoc = "<?xml version='1.0' encoding='UTF-8'?>" + "\n"
    gpxdoc += "<gpx version=\"1.1\" creator=\"http://www.myoggradio.org\"" + "\n"
    gpxdoc += "xmlns=\"http://www.topografix.com/GPX/1/1\"" + "\n"
    gpxdoc += "xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"" + "\n"
    gpxdoc += "xsi:schemaLocation=\"http://www.topografix.com/GPX/1/1" + "\n"
    gpxdoc += "http://www.topografix.com/GPX/1/1/gpx.xsd\">" + "\n"
    gpxdoc += " <metadata>" + "\n"
    gpxdoc += "  <name>Ein GPX Track pywv Pre Alpha Test</name>" + "\n"
    gpxdoc += " </metadata>" + "\n"
    gpxdoc += " <trk>" + "\n"
    gpxdoc += "  <trkseg>" + "\n"
    for (flat,flon,ele,tim) in gpxtrkpt:
        lat = str(flat)
        lon = str(flon)
        gpxdoc += "   <trkpt lat=\"" + lat + "\" lon=\"" + lon + "\">" + "\n"
        gpxdoc += "    <ele>" + ele + "</ele>" + "\n"
        gpxdoc += "    <time>" + tim + "</time>" + "\n"
        gpxdoc += "   </trkpt>" + "\n"
    gpxdoc += "  </trkseg>" + "\n"
    gpxdoc += " </trk>" + "\n"
    gpxdoc += "</gpx>" + "\n"
    dlg = QFileDialog()
    dlg.setFileMode(QFileDialog.AnyFile)
    if dlg.exec_():
        filenames = dlg.selectedFiles()
        try:
            for file in filenames:
                with open(file,"w") as datei:
                    datei.write(gpxdoc)
        except:
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])
            
def parseOSMXml(parameter):
    websiteList = []
    xmldoc = minidom.parse(parameter["osmxml"])
    itemlist = xmldoc.getElementsByTagName('tag')
    for item in itemlist:
        k = item.attributes['k'].value
        if k == "contact:website":
            v = item.attributes['v'].value
            websiteList.append(v)
        if k == "website":
            v = item.attributes['v'].value
            websiteList.append(v)
        if k == "url":
            v = item.attributes['v'].value
            websiteList.append(v)
        if k == "link":
            v = item.attributes['v'].value
            websiteList.append(v)
    f = open(parameter["temphtml"],'w')
    f.write("<html>" + "\n")
    f.write("<body>" + "\n")
    for website in websiteList:
        satz = "<a href=\"" + website + "\">" + website + "</a><br/>"
        f.write(satz + "\n")
    f.write("</body>" + "\n")
    f.write("</html>" + "\n")
    f.close()
    ossystem = platform.system()
    cmd = ""
    if ossystem == "Linux":
        cmd = "firefox " + parameter["temphtml"]
    if ossystem == "Windows":
        cmd = "start " + parameter["temphtml"]
    erg = os.system(cmd)
    print(erg)
    
def downloadOSMData(x,y,z,parameter):
    latlon = calculateLatLon(x+0.5,y+0.5,z)
    lat = latlon[0]
    lon = latlon[1]
    minlat = str(lat - 0.005)
    minlon = str(lon - 0.005) 
    maxlat = str(lat + 0.005)
    maxlon = str(lon + 0.005)
    sUrl = "https://api.openstreetmap.org/api/0.6/map?bbox="+minlon+","+minlat+","+maxlon+","+maxlat
    rc = request.urlopen(sUrl)
    inhalt = rc.read()
    open(parameter["osmxml"], 'wb').write(inhalt)
    
def downloadTile(x,y,z,parameter):
    sUrl = "https://tile.thunderforest.com/cycle/"+z+"/"+y+"/"+x+".png?apikey="+parameter["apiKey"]
    #print(sUrl)
    rc = request.urlopen(sUrl)
    print(rc.code)
    inhalt = rc.read()
    open(parameter["tileCache"] + "\\tile."+x+"."+y+"."+z+".png", 'wb').write(inhalt)

def getTile(x,y,z,parameter):
    pfad = parameter["tileCache"] + "\\tile."+x+"."+y+"."+z+".png"
    if not os.path.isfile(pfad):
        downloadTile(x,y,z,parameter)
    return QImage(pfad)

def calculateXY(lat,lon,z):
        fz = 1.0;
        for i in range(0,z):
            fz = 2.0 * fz;
        ytile = (lon + 180) / 360 * fz ;
        xtile = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * fz
        return (xtile,ytile)
    
def calculateLatLon(y,x,z):
    x = float(x)
    y = float(y)
    pi = math.pi
    fz = 1.0
    for i in range(0,z):
        fz = fz * 2.0
    lon = ((360.0 * float(x))/float(fz)) - 180.0
    lat = pi - 2.0 * pi * (float(y)/float(fz))
    lat = math.sinh(lat)
    lat = math.atan(lat) * 180.0 / pi
    lat = math.trunc(lat * 1000000.0) / 1000000.0
    lon = math.trunc(lon * 1000000.0) / 1000000.0
    erg = [lat,lon]
    return erg


class TilePanel(QWidget):
    
    def __init__(self,image):
        QWidget.__init__(self)
        self.image = image
        width = self.image.width()
        height = self.image.height()
        self.setGeometry(100,100,width,height)
    
    def paintEvent(self,event):
        qp = QPainter()
        qp.begin(self)
        qp.drawPixmap(0,0,QPixmap.fromImage(self.image))
        qp.end()
    
    
class BildPanel(QWidget):
    
    def __init__(self,x,y,z,parameter,gpxtrkpt):
        self.x = x
        self.y = y
        self.z = z
        self.gpxtrkpt = gpxtrkpt
        x = math.trunc(x) 
        y = math.trunc(y)
        self.p = math.trunc((self.x - x) * 255.0)
        self.q = math.trunc((self.y - y) * 255.0)
        QWidget.__init__(self)
        self.cluster = QImage(765,765,QImage.Format_RGB32)
        temp = QImage(1020,1020,QImage.Format_RGB32)
        tiles = []
        for i in range(0,4):
            tiles1 = []
            for j in range(0,4):
                tile = getTile(str(x-1+j),str(y-1+i),str(z),parameter)
                tiles1.append(tile)
            tiles.append(tiles1)
        for i in range(0,4):
            for j in range(0,4):
                tile = tiles[i][j] 
                for a in range(0,255):
                    for b in range(0,255):
                        color = tile.pixel(a,b)
                        temp.setPixel(i*255+a,j*255+b,color) 
        color = qRgba(0,255,0,0)
        x = 255
        for y in range(0,1020):
            temp.setPixel(x,y,1020)
        x = 510
        for y in range(0,1020):
            temp.setPixel(x,y,1020)            
        x = 765
        for y in range(0,1020):
            temp.setPixel(x,y,1020)
        y = 255
        for x in range(0,1020):
            temp.setPixel(x,y,1020)
        y = 510
        for x in range(0,1020):
            temp.setPixel(x,y,1020)            
        y = 765
        for x in range(0,1020):
            temp.setPixel(x,y,1020)
        for x in range(0,765):
            for y in range(0,765):
                color = temp.pixel(x+self.q,y+self.p) 
                self.cluster.setPixel(x,y,color)
        for x in range(358,408):
            y = 383
            color = qRgba(255,0,0,0)
            self.cluster.setPixel(x,y,color)
        for y in range(358,408):
            x = 383
            color = qRgba(255,0,0,0)
            self.cluster.setPixel(x,y,color)
        if len(self.gpxtrkpt) > 0:
            for trkpt in self.gpxtrkpt:
                lat = trkpt[0]
                lon = trkpt[1]
                # print(lat,lon)
                (gpx_x,gpx_y) = calculateXY(lat,lon,z)
                deltay = (gpx_x - self.x + 1.0) * 255.0
                deltax = (gpx_y - self.y + 1.0) * 255.0
                ok = True
                if deltax < 0.0: ok = False
                if deltay < 0.0: ok = False
                if deltax > 765.0: ok = False
                if deltay > 765.0: ok = False
                if ok:
                    color = qRgba(255,0,0,0)
                    self.cluster.setPixel(math.trunc(deltax)-1,math.trunc(deltay)-1,color)
                    self.cluster.setPixel(math.trunc(deltax)-0,math.trunc(deltay)-1,color)
                    self.cluster.setPixel(math.trunc(deltax)+1,math.trunc(deltay)-1,color)
                    self.cluster.setPixel(math.trunc(deltax)-1,math.trunc(deltay)-0,color)
                    self.cluster.setPixel(math.trunc(deltax)-0,math.trunc(deltay)-0,color)
                    self.cluster.setPixel(math.trunc(deltax)+1,math.trunc(deltay)-0,color)
                    self.cluster.setPixel(math.trunc(deltax)-1,math.trunc(deltay)+1,color)
                    self.cluster.setPixel(math.trunc(deltax)-0,math.trunc(deltay)+1,color)
                    self.cluster.setPixel(math.trunc(deltax)+1,math.trunc(deltay)+1,color)
        pan = TilePanel(self.cluster)
        grid=QGridLayout()
        grid.addWidget(pan,0,0)
        #self.setGeometry(0,0,765,765)
        self.setMinimumSize(765,765)
        self.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
        self.setLayout(grid)
        self.alListener = []
        
    def mousePressEvent(self,ev):
        for listener in self.alListener:
            listener.mousePressed(ev)
    
    def addMouseListener(self,listener):
        self.alListener.append(listener)
    
    
class BildController(QMainWindow):
    
    def __init__(self,x,y,z,parameter):
        QMainWindow.__init__(self)
        self.x = x 
        self.y = y 
        self.z = z
        self.parameter = parameter
        self.gpxtrkpt = []
        self.gpxmodus = "normal"
        self.gpxDeletePoint1 = (0.0,0.0)
        self.gpxDeletePoint2 = (0.0,0.0)
        self.setGeometry(100,100,765,765)
        self.bild = BildPanel(x,y,z,parameter,self.gpxtrkpt)
        self.setCentralWidget(self.bild)
        self.bild.addMouseListener(self)
        self.menu = QMenuBar()
        self.position_menu = self.menu.addMenu("Position")
        self.ZoomUpAction = self.position_menu.addAction("Zoom Up")   
        self.ZoomDownAction = self.position_menu.addAction("Zoom Down")
        self.WestAction = self.position_menu.addAction("West")
        self.EastAction = self.position_menu.addAction("East")
        self.NorthAction = self.position_menu.addAction("North")
        self.SouthAction = self.position_menu.addAction("South")
        self.file_menu = self.menu.addMenu("File")
        self.PrintAction = self.file_menu.addAction("Print to PDF")
        self.DownloadTileAction = self.file_menu.addAction("Download Tile")
        self.ShowWebsitesAction = self.file_menu.addAction("Show Websites")
        self.gpx_menu = self.menu.addMenu("GPX")
        self.ReadGPXAction = self.gpx_menu.addAction("Read GPX Track")
        self.SaveGPXAction = self.gpx_menu.addAction("Save GPX Track as")
        self.normalModusAction = self.gpx_menu.addAction("Set Normal Modus to GPX")
        self.addPointAction = self.gpx_menu.addAction("Set Add Point Modus to GPX")
        self.deleteRectangleAction = self.gpx_menu.addAction("Set Delete Rectangle Modus from GPX")
        self.menu.triggered[QAction].connect(self.triggered)
        self.setMenuBar(self.menu)
        
    def myprint(self):
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(self.parameter["pdfFile"])
        qp = QPainter()
        qp.begin(printer)
        qp.drawPixmap(0,0,QPixmap.fromImage(self.bild.cluster))
        qp.end()
    
    def triggered(self,quelle):
        if quelle == self.normalModusAction:
            self.gpxmodus = "normal"
        if quelle == self.addPointAction:
            self.gpxmodus = "addPoint"
        if quelle == self.deleteRectangleAction:
            self.gpxmodus = "deleteRectangle"
            self.gpxDeletePoint1 = (0.0,0.0)
            self.gpxDeletePoint2 = (0.0,0.0)
        if quelle == self.PrintAction:
            self.myprint()
        if quelle == self.ZoomUpAction:
            if self.z > 2:
                self.z = self.z - 1
                self.x = (self.x / 2) - 0.25
                self.y = (self.y / 2) - 0.25
        if quelle == self.ZoomDownAction:
            if self.z < 18:
                self.z = self.z + 1
                self.x = (2 * self.x) + 0.5
                self.y = (2 * self.y) + 0.5
        if quelle == self.WestAction:
            self.y = self.y + 1.0
        if quelle == self.EastAction:
            self.y = self.y - 1.0
        if quelle == self.NorthAction:
            self.x = self.x + 1.0
        if quelle == self.SouthAction:
            self.x = self.x - 1.0
        if quelle == self.DownloadTileAction:
            x = math.trunc(self.x)
            y = math.trunc(self.y)
            for i in range(0,4):
                for j in range(0,4):
                    downloadTile(str(x-1+i),str(y-1+j),str(self.z),self.parameter)
        if quelle == self.ShowWebsitesAction:
            downloadOSMData(round(self.x),round(self.y),self.z,self.parameter)
            parseOSMXml(self.parameter)
        if quelle == self.ReadGPXAction:
            newgpxtrkpt = readGPX()
            for trkpt in newgpxtrkpt:
                self.gpxtrkpt.append(trkpt)
        if quelle == self.SaveGPXAction:
            saveGPX(self.gpxtrkpt)
        self.bild = BildPanel(self.x,self.y,self.z,self.parameter,self.gpxtrkpt)
        self.bild.addMouseListener(self)
        self.setCentralWidget(self.bild)
        self.update()
    
    def mousePressed(self,ev):
        if ev.button() == Qt.LeftButton:
            pos = ev.pos()
            a = pos.x()
            b = pos.y()
            delta = 383 + int(self.parameter["adjustment"])
            deltax = (float(b-delta) / 255.0) 
            deltay = (float(a-delta) / 255.0)
            print(">>>",a,b)
            self.x = float(self.x) + deltax
            self.y = float(self.y) + deltay
            print(self.x+0.5,self.y+0.5,self.z)
            print(calculateLatLon(self.x+0.5,self.y+0.5,self.z))
            self.bild = BildPanel(self.x,self.y,self.z,self.parameter,self.gpxtrkpt)
            self.bild.addMouseListener(self)
            self.setCentralWidget(self.bild)
            self.update()
        if ev.button() == Qt.RightButton:
            if self.gpxmodus == "addPoint":
                pos = ev.pos()
                a = pos.x()
                b = pos.y()
                delta = 383 + int(self.parameter["adjustment"])
                deltax = (float(b-delta) / 255.0) 
                deltay = (float(a-delta) / 255.0)
                print(">>>",a,b)
                self.x = float(self.x) + deltax
                self.y = float(self.y) + deltay
                print(self.x+0.5,self.y+0.5,self.z)
                (lat,lon) = calculateLatLon(self.x+0.5,self.y+0.5,self.z)
                ele = "0.0"
                tim = datetime.today().isoformat()
                worte = tim.split(".")
                worte[-1] = "000Z"
                tim = worte[0]
                for wort in worte:
                    if wort != worte[0]:
                        tim = tim + "." + wort
                self.gpxtrkpt.append((lat,lon,ele,tim))
                self.bild = BildPanel(self.x,self.y,self.z,self.parameter,self.gpxtrkpt)
                self.bild.addMouseListener(self)
                self.setCentralWidget(self.bild)
                self.update()
            if self.gpxmodus == "deleteRectangle":
                pos = ev.pos()
                a = pos.x()
                b = pos.y()
                delta = 383 + int(self.parameter["adjustment"])
                deltax = (float(b-delta) / 255.0) 
                deltay = (float(a-delta) / 255.0)
                print(">>>",a,b)
                self.x = float(self.x) + deltax
                self.y = float(self.y) + deltay
                print(self.x+0.5,self.y+0.5,self.z)
                (lat,lon) = calculateLatLon(self.x+0.5,self.y+0.5,self.z)
                if self.gpxDeletePoint1 == (0.0,0.0):
                    self.gpxDeletePoint1 = (lat,lon)
                else:
                    self.gpxDeletePoint2 = (lat,lon)
                    (lat1,lon1) = self.gpxDeletePoint1
                    (lat2,lon2) = self.gpxDeletePoint2
                    if (lat1 > lat2):
                        lat3 = lat2
                        lat2 = lat1
                        lat1 = lat3
                    if (lon1 > lon2):
                        lon3 = lon2
                        lon2 = lon1
                        lon1 = lon3
                    newgpxtrkpt = []
                    for trkpt in self.gpxtrkpt:
                        lat = trkpt[0]
                        lon = trkpt[1]
                        inRectangle = True
                        if lat < lat1: inRectangle = False
                        if lat > lat2: inRectangle = False
                        if lon < lon1: inRectangle = False
                        if lon > lon2: inRectangle = False
                        if inRectangle:
                            pass
                        else:
                            newgpxtrkpt.append(trkpt)
                    self.gpxtrkpt = newgpxtrkpt
                    self.gpxmodus = "normal"
                self.bild = BildPanel(self.x,self.y,self.z,self.parameter,self.gpxtrkpt)
                self.bild.addMouseListener(self)
                self.setCentralWidget(self.bild)
                self.update()
    