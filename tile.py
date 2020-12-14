# coding: latin-1
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
    # Lese GPX Track aus Datei und gebe die enthaltenen Trackpoints zur�ck
    gpxtrackpoint = []
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
                    gpxtrackpoint.append((float(lat),float(lon),ele,tim))
                    #print(lat,lon,ele,tim)
        except:
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])
    return gpxtrackpoint
        
def saveGPX(gpxtrackpoint):
    # Speichere die Trackpoints in Datei (GPX Track)
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
    for (flat,flon,ele,tim) in gpxtrackpoint:
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
    # Parse OpenStreetMap XML Daten und extrahiere alle dort eingetragenen Webseiten
    # Starte dann einen Webbrowser mit den extrahierten Daten
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
    # Lese XML Daten von Openstreetmap f�r ein kleines Gebiet
    # Speichere diese Daten in einer Datei
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
    with open(parameter["osmxml"],"wb") as f:
        f.write(inhalt)
    
def downloadTile(x,y,z,parameter):
    # Lese eine Kachel von Thunderforest und speichere diese im Tile Cache Directory
    sUrl = "https://tile.thunderforest.com/cycle/"+z+"/"+y+"/"+x+".png?apikey="+parameter["apiKey"]
    #print(sUrl)
    rc = request.urlopen(sUrl)
    print(rc.code)
    inhalt = rc.read()
    tileFileName = os.path.join(parameter["tileCache"],"tile."+x+"."+y+"."+z+".png")
    with open(tileFileName,"wb") as f:
        f.write(inhalt)
        
def getTile(x,y,z,parameter):
    # Lese ein Thunderforest Kachel
    # Schaue aber vorher, ob diese schon heruntergeladen wurde
    pfad = os.path.join(parameter["tileCache"],"tile."+x+"."+y+"."+z+".png")
    #pfad = parameter["tileCache"] + "\\tile."+x+"."+y+"."+z+".png"
    if not os.path.isfile(pfad):
        downloadTile(x,y,z,parameter)
    return QImage(pfad)

def calculateXY(lat,lon,z):
    # Berechne X und Y Koordinate aus Latitude und Longitude bei vorgegebener Zoom Stufe Z
    fz = 1.0;
    for i in range(0,z):
        fz = 2.0 * fz;
    ytile = (lon + 180) / 360 * fz 
    xtile = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * fz
    return (xtile,ytile)
    
def calculateLatLon(y,x,z):
    # Berechne Latitude und Longitude aus X un Y Koordinate per Zoomstufe Z
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
    # Zeigt ein QImage an
    
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
    # Baut das anzuzeigende Bild auf
    
    def __init__(self,x,y,z,parameter,gpxtrackpoint):
        self.x = x # X Koordinate
        self.y = y # Y Koordinate
        self.z = z # Zoom stufe
        self.gpxtrackpoint = gpxtrackpoint
        # Teile Koordinaten in Ganzahl Anteil und Nachkomma Stellen
        # Da Kacheln von Thunderforest immer bei ganzzahligen Koordinaten beginnen
        x = math.trunc(x) 
        y = math.trunc(y)
        self.p = math.trunc((self.x - x) * 255.0)
        self.q = math.trunc((self.y - y) * 255.0)
        QWidget.__init__(self)
        self.cluster = QImage(765,765,QImage.Format_RGB32) # Das anzuzeigen 3X3 Bild
        temporaer = QImage(1020,1020,QImage.Format_RGB32) # Ein tempor�res 4x4 Bild
        # Es ist einfacher zun�chst ein 4x4 Bild aufzubauen und daraus das 3x3 Bild auszuschneiden
        tiles = []
        # Lese zun�chst die Kachel von Thunderforest ein
        for i in range(0,4):
            tiles1 = []
            for j in range(0,4):
                tile = getTile(str(x-1+j), str(y-1+i), str(z), parameter)
                tiles1.append(tile)
            tiles.append(tiles1)
        # Baue das 4x4 Bild aus den Kacheln auf
        for i in range(0,4):
            for j in range(0,4):
                tile = tiles[i][j] 
                for a in range(0,255):
                    for b in range(0,255):
                        color = tile.pixel(a,b)
                        temporaer.setPixel(i*255+a,j*255+b,color)
        # Zeichne ein Gitternetz ins 4x4 Bild 
        for i in range(0,4):
            x = i * 255
            for y in range(0,1020):
                temporaer.setPixel(x,y,1020)
        for j in range(0,4):
            y = j * 255
            for x in range(0,1020):
                temporaer.setPixel(x,y,1020)
        # Schneide nun das 3x3 Bild aus dem 4x4 Bild aus
        for x in range(0,765):
            for y in range(0,765):
                color = temporaer.pixel(x+self.q,y+self.p) 
                self.cluster.setPixel(x,y,color)
        # Zeichne ein Kreuz im Kartenmittelpunkt
        for x in range(358,408):
            y = 383
            color = qRgba(255,0,0,0)
            self.cluster.setPixel(x,y,color)
        for y in range(358,408):
            x = 383
            color = qRgba(255,0,0,0)
            self.cluster.setPixel(x,y,color)
        # Wenn ein GPX Track vorhanden ist, zeichne diesen
        if len(self.gpxtrackpoint) > 0:
            for trackpoint in self.gpxtrackpoint:
                lat = trackpoint[0]
                lon = trackpoint[1]
                (gpx_x,gpx_y) = calculateXY(lat,lon,z)
                deltay = (gpx_x - self.x + 1.0) * 255.0
                deltax = (gpx_y - self.y + 1.0) * 255.0
                # Ist der Track Point auf dem 3x3 Bild dann zeichne dort 9 rote Pixel
                if 0 < deltax < 765 and 0 < deltay < 765:
                    color = qRgba(255,0,0,0)
                    for i in range(0,3):
                        for j in range(0,3):
                            self.cluster.setPixel(math.trunc(deltax)-1+i,math.trunc(deltay)-1+j,color)
        # Zeige das Bild
        pan = TilePanel(self.cluster)
        grid=QGridLayout()
        grid.addWidget(pan,0,0)
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
    # Die GUI f�r den Benutzer
    
    def __init__(self,x,y,z,parameter):
        QMainWindow.__init__(self)
        self.x = x # X Koordinate
        self.y = y # Y Koordinate
        self.z = z # Zoom stufe
        self.parameter = parameter # Parameter aus der ini Datei
        self.gpxtrackpoint = [] # Alle Track Points eines GPX Tracks
        self.gpxmodus = "normal"
        self.gpxDeletePoint1 = (0.0,0.0) # Ecke eines Rechtecks
        self.gpxDeletePoint2 = (0.0,0.0) # Gegen�berliegende Ecke des Rechtecks
        self.setGeometry(100,100,765,765)
        self.bild = BildPanel(x,y,z,parameter,self.gpxtrackpoint) # Baue das Bild auf
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
        self.PositionToGPXAction = self.gpx_menu.addAction("Position to GPX Track")
        self.normalModusAction = self.gpx_menu.addAction("Set Normal Modus to GPX")
        self.addPointAction = self.gpx_menu.addAction("Set Add Point Modus to GPX")
        self.deleteRectangleAction = self.gpx_menu.addAction("Set Delete Rectangle Modus from GPX")
        self.menu.triggered[QAction].connect(self.triggered)
        self.setMenuBar(self.menu)
        
    def myprint(self):
        # Gebe PDF aus
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
            self.gpxDeletePoint1 = (0.0,0.0) # Eckpunkt eines Rechtecks
            self.gpxDeletePoint2 = (0.0,0.0) # Gegen�berliegender Eckpunkt des Rechtecks
        if quelle == self.PrintAction:
            self.myprint()
        if quelle == self.ZoomUpAction:
            # Zoom Stufe herabsetzen bis zur minimalen Zoom Stufe 2
            if self.z > 2:
                self.z = self.z - 1
                self.x = (self.x / 2) - 0.25
                self.y = (self.y / 2) - 0.25
        if quelle == self.ZoomDownAction:
            # Zoom Stufe heraufsetzen bis zur maximalen Zoom Stufe 18
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
            # Lade Kacheln nochmal von Tunderforest in den Cache, auch wenn sie da schon vorhandenen sind
            x = math.trunc(self.x)
            y = math.trunc(self.y)
            for i in range(0,4):
                for j in range(0,4):
                    downloadTile(str(x-1+i),str(y-1+j),str(self.z),self.parameter)
        if quelle == self.ShowWebsitesAction:
            downloadOSMData(round(self.x),round(self.y),self.z,self.parameter)
            parseOSMXml(self.parameter)
        if quelle == self.PositionToGPXAction:
            # Positioniere die Karte so, das �hr Mittelpunkt mit dem Mittelpunkt des GPX Track �bereinstimmt
            if len(self.gpxtrackpoint) > 0:
                dlat = 0.0
                dlon = 0.0
                anzahl = 0
                for trackpoint in self.gpxtrackpoint:
                    lat = trackpoint[0]
                    lon = trackpoint[1]
                    dlat += lat
                    dlon += lon
                    anzahl = anzahl + 1
                dlat = dlat / anzahl
                dlon = dlon / anzahl
                self.z = 12
                (self.x,self.y) = calculateXY(dlat,dlon,self.z)
                self.x = self.x - 0.5
                self.y = self.y - 0.5
        if quelle == self.ReadGPXAction:
            # Lese einen GPX Track ein und f�ge diesen zum bestehen GPX Track hinzu
            newgpxtrackpoint = readGPX()
            for trackpoint in newgpxtrackpoint:
                self.gpxtrackpoint.append(trackpoint)
        if quelle == self.SaveGPXAction:
            saveGPX(self.gpxtrackpoint)
        self.bild = BildPanel(self.x,self.y,self.z,self.parameter,self.gpxtrackpoint)
        self.bild.addMouseListener(self)
        self.setCentralWidget(self.bild)
        self.update()
    
    def mousePressed(self,ev):
        if ev.button() == Qt.LeftButton:
            # Mache den links angeklickten Punkt zum Kartenmittelpunkt
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
            self.bild = BildPanel(self.x,self.y,self.z,self.parameter,self.gpxtrackpoint)
            self.bild.addMouseListener(self)
            self.setCentralWidget(self.bild)
            self.update()
        if ev.button() == Qt.RightButton:
            if self.gpxmodus == "addPoint":
                # F�ge den rechts angeklickten Punkt zum GPX Track hinzu
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
                self.gpxtrackpoint.append((lat,lon,ele,tim))
                self.bild = BildPanel(self.x,self.y,self.z,self.parameter,self.gpxtrackpoint)
                self.bild.addMouseListener(self)
                self.setCentralWidget(self.bild)
                self.update()
            if self.gpxmodus == "deleteRectangle":
                # L�sche alle Track Points, die sich im ausgewhlten Rechteck befinden
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
                    newgpxtrackpoint = []
                    for trackpoint in self.gpxtrackpoint:
                        lat = trackpoint[0]
                        lon = trackpoint[1]
                        inRectangle = True
                        if lat < lat1: inRectangle = False
                        if lat > lat2: inRectangle = False
                        if lon < lon1: inRectangle = False
                        if lon > lon2: inRectangle = False
                        if inRectangle:
                            pass
                        else:
                            newgpxtrackpoint.append(trackpoint)
                    self.gpxtrackpoint = newgpxtrackpoint
                    self.gpxmodus = "normal"
                self.bild = BildPanel(self.x,self.y,self.z,self.parameter,self.gpxtrackpoint)
                self.bild.addMouseListener(self)
                self.setCentralWidget(self.bild)
                self.update()
    