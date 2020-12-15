# coding: latin-1
import os
import sys
import math
import platform
from pathlib import Path
from datetime import datetime
from xml.dom import minidom
from urllib import request
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtGui import QImage,QPainter,QPixmap,qRgba
from PyQt5.QtWidgets import QWidget,QGridLayout,QMenuBar,QAction,QMainWindow,QSizePolicy,QFileDialog
from PyQt5.QtCore import Qt

def printNextAmenity(lat,lon,amenities,amenity_typ):
    """ Drucke die nächstgelegene Amenity an """
    minAmenity = None
    minAbstand = 1000000000.0
    for amenity in amenities:
        typ = amenity["amenity"]
        alat = amenity["lat"]
        alon = amenity["lon"]
        abstand = (alat-lat)*(alat-lat) + (alon-lon)*(alon-lon)
        ok = False
        if amenity_typ == None:
            ok = True
        elif amenity_typ == typ:
            ok = True
        if ok:
            if abstand < minAbstand:
                minAbstand = abstand
                minAmenity = amenity
    if not (minAmenity == None):
        keylist = list(minAmenity)
        for key in keylist:
            wert = minAmenity[key]
            print(key,wert)

def readGPX():
    """ Lese GPX Track aus Datei und gebe die enthaltenen Trackpoints zurück """
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
        except:
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])
    return gpxtrackpoint
        
def saveGPX(gpxtrackpoint):
    """ Speichere die Trackpoints in Datei (GPX Track) """
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
def parseAmenity(config):
    """
    Parse OpenStreetMap XML Daten und extrahiere alle dort eingetragenen amenity
    """
    amenities = []
    xmldoc = minidom.parse(config["osmxml"])
    itemlist = xmldoc.getElementsByTagName('node')
    for item in itemlist:
        amenity = {}
        lat = item.attributes['lat'].value
        lon = item.attributes['lon'].value
        amenity["lat"] = float(lat)
        amenity["lon"] = float(lon)
        tags = item.getElementsByTagName('tag')
        isAmenity = False
        for tag in tags:
            k = tag.attributes['k'].value
            v = tag.attributes['v'].value
            amenity[k] = v
            if k == "amenity": isAmenity = True
        if isAmenity: amenities.append(amenity)
    return amenities
                    
def parseOSMXml(config):
    """
    Parse OpenStreetMap XML Daten und extrahiere alle dort eingetragenen Webseiten
    Starte dann einen Webbrowser mit den extrahierten Daten
    """
    websiteList = []
    xmldoc = minidom.parse(config["osmxml"])
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
    f = open(config["temphtml"],'w')
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
        cmd = "firefox " + config["temphtml"]
    if ossystem == "Windows":
        cmd = "start " + config["temphtml"]
    erg = os.system(cmd)
    print(erg)
    
def downloadOSMData(x,y,zoom,config):
    """
    Lese XML Daten von Openstreetmap für ein kleines Gebiet
    Speichere diese Daten in einer Datei
    """
    latlon = calculateLatLon(x+0.5,y+0.5,zoom)
    lat = latlon[0]
    lon = latlon[1]
    minlat = str(lat - 0.005)
    minlon = str(lon - 0.005) 
    maxlat = str(lat + 0.005)
    maxlon = str(lon + 0.005)
    sUrl = "https://api.openstreetmap.org/api/0.6/map?bbox="+minlon+","+minlat+","+maxlon+","+maxlat
    rc = request.urlopen(sUrl)
    inhalt = rc.read()
    with open(config["osmxml"],"wb") as f:
        f.write(inhalt)
    
def downloadTile(x,y,zoom,config):
    """ Lese eine Kachel von Thunderforest oder OpenStreetMap und speichere diese im Tile Cache Directory """
    sUrl = "https://tile.thunderforest.com/cycle/"+zoom+"/"+y+"/"+x+".png?apikey="+config["apiKey"]
    if config["tileserver"] == "openstreetmap":
        sUrl = "https://a.tile.openstreetmap.de/"+zoom+"/"+y+"/"+x+".png"
    rc = request.urlopen(sUrl)
    print(rc.code)
    inhalt = rc.read()
    tileFileName = os.path.join(config["tileCache"],"tile."+x+"."+y+"."+zoom+".png")
    with open(tileFileName,"wb") as f:
        f.write(inhalt)
      
def get_tile(x, y, zoom, config):
    """ Lese ein Thunderforest/Openstreetmap Kachel """
    path = Path(config["tileCache"]) / f"tile.{x}.{y}.{zoom}.png"
    if not path.is_file():
        downloadTile(str(x), str(y), str(zoom), config)
    return QImage(str(path))

def calculateXY(lat,lon,zoom):
    """ Berechne X und Y Koordinate aus Latitude und Longitude bei vorgegebener Zoom Stufe Z """
    fz = 1.0;
    for i in range(0,zoom):
        fz = 2.0 * fz;
    ytile = (lon + 180) / 360 * fz 
    xtile = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * fz
    return (xtile,ytile)
    
def calculateLatLon(y,x,zoom):
    """ Berechne Latitude und Longitude aus X un Y Koordinate per Zoomstufe zoom """
    x = float(x)
    y = float(y)
    pi = math.pi
    fz = 1.0
    for i in range(0,zoom):
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
    """ Zeigt ein QImage an """
    
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
    """ Baut das anzuzeigende Bild auf """
    
    def __init__(self,x,y,zoom,config,gpxtrackpoint,amenities,amenity_typ):
        self.x = x # X Koordinate
        self.y = y # Y Koordinate
        self.zoom = zoom # Zoom stufe
        self.gpxtrackpoint = gpxtrackpoint
        self.amenities = amenities
        self.amenity_typ = amenity_typ
        flagge = QImage("flagge.png") # Bild um Amenity anzuzeigen
        # Teile Koordinaten in Ganzahl Anteil und Nachkomma Stellen
        # Da Kacheln von Thunderforest immer bei ganzzahligen Koordinaten beginnen
        x = math.trunc(x) 
        y = math.trunc(y)
        self.p = math.trunc((self.x - x) * 255.0)
        self.q = math.trunc((self.y - y) * 255.0)
        QWidget.__init__(self)
        self.cluster = QImage(765,765,QImage.Format_RGB32) # Das anzuzeigen 3X3 Bild
        temporaer = QImage(1020,1020,QImage.Format_RGB32) # Ein temporäres 4x4 Bild
        # Es ist einfacher zunächst ein 4x4 Bild aufzubauen und daraus das 3x3 Bild auszuschneiden
        tiles = []
        # Lese zunächst die Kachel von Thunderforest/OpenStreetMap ein
        for i in range(0,4):
            tiles1 = []
            for j in range(0,4):
                tile = get_tile((x-1+j), (y-1+i), (zoom), config)
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
                (gpx_x,gpx_y) = calculateXY(lat,lon,zoom)
                deltay = (gpx_x - self.x + 1.0) * 255.0
                deltax = (gpx_y - self.y + 1.0) * 255.0
                # Ist der Track Point auf dem 3x3 Bild dann zeichne dort 9 rote Pixel
                if 0 < deltax < 765 and 0 < deltay < 765:
                    color = qRgba(255,0,0,0)
                    for i in range(0,3):
                        for j in range(0,3):
                            self.cluster.setPixel(math.trunc(deltax)-1+i,math.trunc(deltay)-1+j,color)
        # Wenn Amenities vorhanden sind, zeichne entsprechende Flaggen
        if len(self.amenities) > 0:
            for amenity in self.amenities:
                typ = amenity["amenity"]
                lat = amenity["lat"]
                lon = amenity["lon"]
                (amenity_x,amenity_y) = calculateXY(lat,lon,zoom)
                deltay = (amenity_x - self.x + 1.0) * 255.0
                deltax = (amenity_y - self.y + 1.0) * 255.0
                ok = False
                if self.amenity_typ == None:
                    ok = True
                elif self.amenity_typ == typ:
                    ok = True
                # Ist die Amenity nicht gefiltert und auf dem 3x3 Bild dann zeichne dort eine Flagge
                if 0 < deltax < 765 and 0 < deltay < 765 and ok:                
                    for i in range(0,16):
                        for j in range(0,16):
                            color = flagge.pixel(i,j)
                            if not color == 0:
                                posx = deltax + i 
                                posy = deltay + j
                                if 0 < posx < 765 and 0 < posy < 765:  
                                    self.cluster.setPixel(posx,posy,color)                            
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
    """ Die GUI für den Benutzer """
    
    def __init__(self,x,y,zoom,config):
        QMainWindow.__init__(self)
        self.x = x # X Koordinate
        self.y = y # Y Koordinate
        self.zoom = zoom # Zoom stufe
        self.config = config # Konfiguration aus der ini Datei
        self.gpxtrackpoint = [] # Alle Track Points eines GPX Tracks
        self.amenities = [] # In OpenStreetMap eingetragene Amenities (Einrichtungen)
        self.amenity_typ = None # Filter welche Amenity angezeigt werden
        self.gpxmodus = "normal"
        self.gpxDeletePoint1 = (0.0,0.0) # Ecke eines Rechtecks
        self.gpxDeletePoint2 = (0.0,0.0) # Gegenüberliegende Ecke des Rechtecks
        self.setGeometry(100,100,765,765)
        self.bild = BildPanel(x,y,zoom,config,self.gpxtrackpoint,self.amenities,self.amenity_typ) # Baue das Bild auf
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
        self.ShowAmenitiesAction = self.file_menu.addAction("Show Amenities")
        self.HideAmenitiesAction = self.file_menu.addAction("Hide Amenities")
        self.filter_menu = self.menu.addMenu("Filter")
        self.ResetFilterAction = self.filter_menu.addAction("Reset Filter")
        self.RestaurantAction = self.filter_menu.addAction("Restaurant")
        self.FuelAction = self.filter_menu.addAction("Fuel")
        self.PubAction = self.filter_menu.addAction("Pub")
        self.DoctorsAction = self.filter_menu.addAction("Doctors")
        self.DentistAction = self.filter_menu.addAction("Dentist")
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
        printer.setOutputFileName(self.config["pdfFile"])
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
            self.gpxDeletePoint2 = (0.0,0.0) # Gegenüberliegender Eckpunkt des Rechtecks
        if quelle == self.PrintAction:
            self.myprint()
        if quelle == self.ZoomUpAction:
            # Zoom Stufe herabsetzen bis zur minimalen Zoom Stufe 2
            if self.zoom > 2:
                self.zoom = self.zoom - 1
                self.x = (self.x / 2) - 0.25
                self.y = (self.y / 2) - 0.25
        if quelle == self.ZoomDownAction:
            # Zoom Stufe heraufsetzen bis zur maximalen Zoom Stufe 18
            if self.zoom < 18:
                self.zoom = self.zoom + 1
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
                    downloadTile(str(x-1+i),str(y-1+j),str(self.zoom),self.config)
        if quelle == self.ShowWebsitesAction:
            downloadOSMData(round(self.x),round(self.y),self.zoom,self.config)
            parseOSMXml(self.config)
        if quelle == self.ShowAmenitiesAction:
            downloadOSMData(round(self.x),round(self.y),self.zoom,self.config)
            self.amenities = parseAmenity(self.config)
        if quelle == self.HideAmenitiesAction:
            self.amenities = []
        if quelle == self.ResetFilterAction:
            self.amenity_typ = None
        if quelle == self.RestaurantAction:
            self.amenity_typ = "restaurant"
        if quelle == self.FuelAction:
            self.amenity_typ = "fuel"
        if quelle == self.PubAction:
            self.amenity_typ = "pub"
        if quelle == self.DoctorsAction:
            self.amenity_typ = "doctors"
        if quelle == self.DentistAction:
            self.amenity_typ = "dentist"
        if quelle == self.PositionToGPXAction:
            # Positioniere die Karte so, das íhr Mittelpunkt mit dem Mittelpunkt des GPX Track übereinstimmt
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
                self.zoom = 12
                (self.x,self.y) = calculateXY(dlat,dlon,self.zoom)
                self.x = self.x - 0.5
                self.y = self.y - 0.5
        if quelle == self.ReadGPXAction:
            # Lese einen GPX Track ein und füge diesen zum bestehen GPX Track hinzu
            newgpxtrackpoint = readGPX()
            for trackpoint in newgpxtrackpoint:
                self.gpxtrackpoint.append(trackpoint)
        if quelle == self.SaveGPXAction:
            saveGPX(self.gpxtrackpoint)
        self.bild = BildPanel(self.x,self.y,self.zoom,self.config,self.gpxtrackpoint,self.amenities,self.amenity_typ)
        self.bild.addMouseListener(self)
        self.setCentralWidget(self.bild)
        self.update()
    
    def mousePressed(self,ev):
        if ev.button() == Qt.LeftButton:
            # Mache den links angeklickten Punkt zum Kartenmittelpunkt
            pos = ev.pos()
            a = pos.x()
            b = pos.y()
            delta = 383 + int(self.config["adjustment"])
            deltax = (float(b-delta) / 255.0) 
            deltay = (float(a-delta) / 255.0)
            print(">>>",a,b)
            self.x = float(self.x) + deltax
            self.y = float(self.y) + deltay
            print(self.x+0.5,self.y+0.5,self.zoom)
            (lat,lon) = calculateLatLon(self.x+0.5,self.y+0.5,self.zoom)
            print(lat,lon)
            printNextAmenity(lat,lon,self.amenities,self.amenity_typ)
            self.bild = BildPanel(self.x,self.y,self.zoom,self.config,self.gpxtrackpoint,self.amenities,self.amenity_typ)
            self.bild.addMouseListener(self)
            self.setCentralWidget(self.bild)
            self.update()
        if ev.button() == Qt.RightButton:
            if self.gpxmodus == "addPoint":
                # Füge den rechts angeklickten Punkt zum GPX Track hinzu
                pos = ev.pos()
                a = pos.x()
                b = pos.y()
                delta = 383 + int(self.config["adjustment"])
                deltax = (float(b-delta) / 255.0) 
                deltay = (float(a-delta) / 255.0)
                print(">>>",a,b)
                self.x = float(self.x) + deltax
                self.y = float(self.y) + deltay
                print(self.x+0.5,self.y+0.5,self.zoom)
                (lat,lon) = calculateLatLon(self.x+0.5,self.y+0.5,self.zoom)
                ele = "0.0"
                tim = datetime.today().isoformat()
                worte = tim.split(".")
                worte[-1] = "000Z"
                tim = worte[0]
                for wort in worte:
                    if wort != worte[0]:
                        tim = tim + "." + wort
                self.gpxtrackpoint.append((lat,lon,ele,tim))
                self.bild = BildPanel(self.x,self.y,self.zoom,self.config,self.gpxtrackpoint,self.amenities,self.amenity_typ)
                self.bild.addMouseListener(self)
                self.setCentralWidget(self.bild)
                self.update()
            if self.gpxmodus == "deleteRectangle":
                # Lösche alle Track Points, die sich im ausgewhlten Rechteck befinden
                pos = ev.pos()
                a = pos.x()
                b = pos.y()
                delta = 383 + int(self.config["adjustment"])
                deltax = (float(b-delta) / 255.0) 
                deltay = (float(a-delta) / 255.0)
                print(">>>",a,b)
                self.x = float(self.x) + deltax
                self.y = float(self.y) + deltay
                print(self.x+0.5,self.y+0.5,self.zoom)
                (lat,lon) = calculateLatLon(self.x+0.5,self.y+0.5,self.zoom)
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
                self.bild = BildPanel(self.x,self.y,self.zoom,self.config,self.gpxtrackpoint,self.amenities,self.amenity_typ)
                self.bild.addMouseListener(self)
                self.setCentralWidget(self.bild)
                self.update()
    