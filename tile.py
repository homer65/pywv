# coding: latin-1
import os
import sys
import math
import platform
from pathlib import Path
from datetime import datetime
from xml.dom import minidom
from urllib import request
from operator import itemgetter
from functools import partial
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtGui import QImage,QPainter,QPixmap,qRgba
from PyQt5.QtWidgets import QWidget,QMenuBar,QAction,QMainWindow,QSizePolicy,QFormLayout,QGridLayout
from PyQt5.QtWidgets import QFileDialog,QHBoxLayout,QVBoxLayout,QPushButton,QLabel,QTabWidget,QDialog,QLineEdit,QScrollArea
from PyQt5.QtCore import Qt

def printNextAmenity(lat,lon,zoom,amenities,amenity_typ):
    """ Drucke die nahegelegenen Amenity an """
    print("---------------------------------------------------------------------------- Start Amenities")
    minAmenity = []
    minAbstand = 0.00005 * (2 ** (18 - zoom))
    for amenity in amenities:
        typ = amenity["amenity"]
        alat = amenity["lat"]
        alon = amenity["lon"]
        abstand = math.sqrt((alat-lat)*(alat-lat) + (alon-lon)*(alon-lon))
        ok = False
        if amenity_typ == None:
            ok = True
        elif amenity_typ in typ:
            ok = True
        if ok:
            if abstand < minAbstand:
                minAmenity.append(amenity)
    for amenity in minAmenity:
        keylist = list(amenity)
        print("----------------------------------------------------------------------------")
        for key in keylist:
            wert = amenity[key]
            print(key,wert)
    print("---------------------------------------------------------------------------- End Amenities")
    return minAmenity

def printNextNode(lat,lon,zoom,nodes,node_typ,node_value):
    """ Drucke die nahegelegenen Node an """
    print("---------------------------------------------------------------------------- Start Nodes")
    minNode = []
    minAbstand = 0.00005 * (2 ** (18 - zoom))
    for node in nodes:
        alat = node["lat"]
        alon = node["lon"]
        abstand = math.sqrt((alat-lat)*(alat-lat) + (alon-lon)*(alon-lon))
        if abstand < minAbstand:
            ok = False
            if node_typ == None: ok = True
            else:
                keylist = list(node)
                for key in keylist:
                    if node_typ in str(key):
                        if node_value == None: ok = True
                        else: 
                            wert = node[key]
                            if node_value in wert: ok = True
            if ok:
                minNode.append(node)
    for node in minNode:
        keylist = list(node)
        print("----------------------------------------------------------------------------")
        for key in keylist:
            wert = node[key]
            print(key,wert)
    print("---------------------------------------------------------------------------- End Nodes")
    return minNode

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

def kategorisiereAmenity(config):
    """
    Parse OpenStreetMap XML Daten und extrahiere alle dort eingetragenen amenity
    Fuer jeden Amenity Typ wird die Anzahl zurueckgegeben
    """
    amenity_typen = {}
    xmldoc = minidom.parse(config["osmxml"])
    itemlist = xmldoc.getElementsByTagName('node')
    for item in itemlist:
        tags = item.getElementsByTagName('tag')
        for tag in tags:
            k = tag.attributes['k'].value
            v = tag.attributes['v'].value
            if k == "amenity": 
                if v in amenity_typen:
                    anzahl = amenity_typen[v] + 1
                    amenity_typen[v] = anzahl
                else:
                    amenity_typen[v] = 1
    return amenity_typen

def kategorisiereNode(config):
    """
    Parse OpenStreetMap XML Daten und extrahiere alle dort eingetragenen getaggten Node
    Fuer jeden Node Typ wird die Anzahl zurueckgegeben
    """
    node_typen = {}
    xmldoc = minidom.parse(config["osmxml"])
    itemlist = xmldoc.getElementsByTagName('node')
    for item in itemlist:
        tags = item.getElementsByTagName('tag')
        for tag in tags:
            k = tag.attributes['k'].value
            if k in node_typen:
                anzahl = node_typen[k] + 1
                node_typen[k] = anzahl
            else:
                node_typen[k] = 1
    return node_typen

def kategorisiereNodeValue(config,node_typ):
    """
    Parse OpenStreetMap XML Daten und extrahiere alle dort eingetragenen getaggten Node Value eines bestimmten Typ
    Fuer jeden Node Value wird die Anzahl zurueckgegeben
    """
    node_values = {}
    xmldoc = minidom.parse(config["osmxml"])
    itemlist = xmldoc.getElementsByTagName('node')
    for item in itemlist:
        tags = item.getElementsByTagName('tag')
        for tag in tags:
            k = tag.attributes['k'].value
            v = tag.attributes['v'].value
            if node_typ in str(k):
                if v in node_values:
                    anzahl = node_values[v] + 1
                    node_values[v] = anzahl
                else:
                    node_values[v] = 1
    return node_values

def parseNode(config):
    """
    Parse OpenStreetMap XML Daten und extrahiere alle dort eingetragenen und getaggte Nodes
    """
    nodes = []
    xmldoc = minidom.parse(config["osmxml"])
    itemlist = xmldoc.getElementsByTagName('node')
    for item in itemlist:
        node = {}
        lat = item.attributes['lat'].value
        lon = item.attributes['lon'].value
        node["lat"] = float(lat)
        node["lon"] = float(lon)
        tags = item.getElementsByTagName('tag')
        isGetaggt = False
        for tag in tags:
            k = tag.attributes['k'].value
            v = tag.attributes['v'].value
            node[k] = v
            isGetaggt = True
        if isGetaggt: nodes.append(node)
    return nodes
                    
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
    minlat = str(lat - 0.003)
    minlon = str(lon - 0.003) 
    maxlat = str(lat + 0.003)
    maxlon = str(lon + 0.003)
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
    if not rc.code == 200: print("downloadTile: Http Response Code: ", rc.code)
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
    fz = 2.0 ** zoom
    ytile = (lon + 180) / 360 * fz 
    xtile = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * fz
    return (xtile,ytile)
    
def calculateLatLon(y,x,zoom):
    """ Berechne Latitude und Longitude aus X un Y Koordinate per Zoomstufe zoom """
    x = float(x)
    y = float(y)
    pi = math.pi
    fz = 2.0 ** zoom
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
    
    def __init__(self,x,y,zoom,config,gpxtrackpoint,amenities,amenity_typ,nodes,node_typ,node_value):
        self.x = x # X Koordinate
        self.y = y # Y Koordinate
        self.zoom = zoom # Zoom stufe
        self.gpxtrackpoint = gpxtrackpoint
        self.amenities = amenities
        self.amenity_typ = amenity_typ
        self.nodes = nodes
        self.node_typ = node_typ
        self.node_value = node_value
        flagge = QImage("flagge.png") # Bild um Amenity anzuzeigen
        node_flagge = QImage("node.png") # Bild um Node anzuzeigen
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
                        posx = i*255+a 
                        posy = j*255+b 
                        if 0 < posx < 1020 and 0 < posy < 1020:
                            temporaer.setPixel(posx,posy,color)
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
                            posx = math.trunc(deltax) - 1 + i 
                            posy = math.trunc(deltay) - 1 + j 
                            if 0 < posx < 765 and 0 < posy < 765:
                                self.cluster.setPixel(posx,posy,color)
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
                elif self.amenity_typ in typ:
                    ok = True
                # Ist die Amenity nicht gefiltert und auf dem 3x3 Bild dann zeichne dort eine Flagge
                if 0 < deltax < 765 and 0 < deltay < 765 and ok:                
                    for i in range(0,12):
                        for j in range(0,12):
                            color = flagge.pixel(i,j)
                            if not color == 0:
                                posx = deltax + i 
                                posy = deltay + j
                                if 0 < posx < 765 and 0 < posy < 765:  
                                    self.cluster.setPixel(posx,posy,color)
                                    
        # Wenn Nodes vorhanden sind, zeichne entsprechende Flaggen
        if len(self.nodes) > 0:
            for node in self.nodes:
                lat = node["lat"]
                lon = node["lon"]
                (node_x,node_y) = calculateXY(lat,lon,zoom)
                deltay = (node_x - self.x + 1.0) * 255.0
                deltax = (node_y - self.y + 1.0) * 255.0
                ok = False
                if self.node_typ == None:
                    ok = True
                else:
                    keylist = list(node)
                    for key in keylist:
                        if self.node_typ in str(key):
                            if self.node_value == None: ok = True
                            else: 
                                wert = node[key]
                                if self.node_value in str(wert): ok = True
                # Ist der Node nicht gefiltert und auf dem 3x3 Bild dann zeichne dort eine entsprechende Flagge
                if 0 < deltax < 765 and 0 < deltay < 765 and ok:                
                    for i in range(0,12):
                        for j in range(0,12):
                            color = node_flagge.pixel(i,j)
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
        self.minAmenity = [] # Amenity nahe Kartenmittelpunkt
        self.amenities = [] # In OpenStreetMap eingetragene Amenities (Einrichtungen)
        self.amenity_typ = None # Filter welche Amenity angezeigt werden       
        self.minNode = [] # Node nahe Kartenmittelpunkt
        self.nodes = [] # In OpenStreetMap eingetragene Nodes, die getagged sind
        self.node_typ = None # Filter welche Node angezeigt werden   
        self.node_value = None # Filer welche Node angezeigt werden     
        self.gpxmodus = "normal"
        self.gpxDeletePoint1 = (0.0,0.0) # Ecke eines Rechtecks
        self.gpxDeletePoint2 = (0.0,0.0) # Gegenüberliegende Ecke des Rechtecks
        self.setGeometry(100,100,800,765)
        self.setWindowTitle("OpenStreetMap / Thunderforest")
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
        self.ShowNodesAction = self.file_menu.addAction("Show Nodes")
        self.HideNodesAction = self.file_menu.addAction("Hide Nodes")
        self.filter_menu = self.menu.addMenu("Amenity Filter")
        self.ResetFilterAction = self.filter_menu.addAction("Reset Filter")
        self.Filter1Action = self.filter_menu.addAction(self.config["filter1"])
        self.Filter2Action = self.filter_menu.addAction(self.config["filter2"])
        self.Filter3Action = self.filter_menu.addAction(self.config["filter3"])
        self.Filter4Action = self.filter_menu.addAction(self.config["filter4"])
        self.Filter5Action = self.filter_menu.addAction(self.config["filter5"])
        self.Filter6Action = self.filter_menu.addAction(self.config["filter6"])
        self.Filter7Action = self.filter_menu.addAction(self.config["filter7"])
        self.Filter8Action = self.filter_menu.addAction(self.config["filter8"])
        self.Filter9Action = self.filter_menu.addAction(self.config["filter9"])
        self.Filter10Action = self.filter_menu.addAction(self.config["filter10"])
        self.AuswahlFilterAction = self.filter_menu.addAction("Auswahl Filter")
        self.node_filter_menu = self.menu.addMenu("Node Filter")
        self.NodeFilerResetAction = self.node_filter_menu.addAction("Reset Node Filter")
        self.NodeFilter1Action = self.node_filter_menu.addAction(self.config["node_filter1"])
        self.NodeFilter2Action = self.node_filter_menu.addAction(self.config["node_filter2"])
        self.NodeFilter3Action = self.node_filter_menu.addAction(self.config["node_filter3"])
        self.NodeFilter4Action = self.node_filter_menu.addAction(self.config["node_filter4"])
        self.NodeFilter5Action = self.node_filter_menu.addAction(self.config["node_filter5"])
        self.NodeFilter6Action = self.node_filter_menu.addAction(self.config["node_filter6"])
        self.NodeFilter7Action = self.node_filter_menu.addAction(self.config["node_filter7"])
        self.NodeFilter8Action = self.node_filter_menu.addAction(self.config["node_filter8"])
        self.NodeFilter9Action = self.node_filter_menu.addAction(self.config["node_filter9"])
        self.NodeFilter10Action = self.node_filter_menu.addAction(self.config["node_filter10"])
        self.NodeFilterAction = self.node_filter_menu.addAction("Setze Node Filter")
        self.gpx_menu = self.menu.addMenu("GPX")
        self.ReadGPXAction = self.gpx_menu.addAction("Read GPX Track")
        self.SaveGPXAction = self.gpx_menu.addAction("Save GPX Track as")
        self.PositionToGPXAction = self.gpx_menu.addAction("Position to GPX Track")
        self.normalModusAction = self.gpx_menu.addAction("Set Normal Modus to GPX")
        self.addPointAction = self.gpx_menu.addAction("Set Add Point Modus to GPX")
        self.deleteRectangleAction = self.gpx_menu.addAction("Set Delete Rectangle Modus from GPX")
        self.menu.triggered[QAction].connect(self.triggered)
        self.setMenuBar(self.menu)
        self.initUICount = 0
        self.initUI()
    
    def initUI(self):
        self.initUICount = self.initUICount + 1
        self.bild = BildPanel(self.x,self.y,self.zoom,self.config,self.gpxtrackpoint,self.amenities,self.amenity_typ,self.nodes,self.node_typ,self.node_value)
        self.bild.addMouseListener(self)
        widget = QWidget()
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        cbox = QHBoxLayout()
        self.butt1 = QPushButton("Zoom Up")
        self.butt2 = QPushButton("Zoom Down")
        (lat, lon) = calculateLatLon(self.x+0.5, self.y+0.5, self.zoom)
        flat = math.trunc(100000.0 * lat) / 100000.0
        flon = math.trunc(100000.0 * lon) / 100000.0
        fx = math.trunc(1000.0 * (self.x + 0.5)) / 1000.0
        fy = math.trunc(1000.0 * (self.y + 0.5)) / 1000.0
        info = str(self.amenity_typ) + " / " + str(self.node_typ) + ":" + str(self.node_value) + " / " + str(flat) + " : " + str(flon) + " # " + str(fx) + " : " + str(fy)  + " :: " + str(self.zoom)
        self.lab1 = QLabel(info);
        self.butt1.clicked.connect(lambda:self.triggered(self.butt1))
        self.butt2.clicked.connect(lambda:self.triggered(self.butt2))
        hbox.addWidget(self.butt1)
        hbox.addWidget(self.butt2)
        hbox.addStretch(1)
        hbox.addWidget(self.lab1)
        vbox.addLayout(hbox)
        vbox.addWidget(self.bild)
        cbox.addLayout(vbox)
        if len(self.minAmenity) > 0:
            tab = QTabWidget()
            anzahl = 0
            for amenity in self.minAmenity:
                anzahl = anzahl + 1
                if anzahl < 10:
                    amenityPanel = AmenityPanel(amenity)
                    tab.addTab(amenityPanel,"Amenity" + str(anzahl))
            cbox.addWidget(tab)
            self.setGeometry(50,50,1165,785)
        else:
            self.setGeometry(50,50,765,785)
        if len(self.minNode) > 0:
            tab = QTabWidget()
            anzahl = 0
            for node in self.minNode:
                anzahl = anzahl + 1
                if anzahl < 10:
                    amenityPanel = AmenityPanel(node) # Eine Amenity ist ein spezieller Node
                    tab.addTab(amenityPanel,"Node" + str(anzahl))
            cbox.addWidget(tab)
            self.setGeometry(50,50,1165,785)
        else:
            self.setGeometry(50,50,765,785)

        widget.setLayout(cbox)
        self.setCentralWidget(widget)
        if self.initUICount > 1: self.update()            
    
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
        if quelle == self.ZoomUpAction or quelle == self.butt1:
            # Zoom Stufe herabsetzen bis zur minimalen Zoom Stufe 2
            if self.zoom > 2:
                self.zoom = self.zoom - 1
                self.x = (self.x / 2) - 0.25
                self.y = (self.y / 2) - 0.25
        if quelle == self.ZoomDownAction or quelle == self.butt2:
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
            downloadOSMData(self.x,self.y,self.zoom,self.config)
            parseOSMXml(self.config)
        if quelle == self.ShowAmenitiesAction:
            self.nodes = []
            self.minNode = []
            downloadOSMData(self.x,self.y,self.zoom,self.config)
            self.amenities = parseAmenity(self.config)
        if quelle == self.HideAmenitiesAction:
            self.amenities = []
            self.minAmenity = []
        if quelle == self.ShowNodesAction:
            self.amenities = []
            self.minAmenity = []
            downloadOSMData(self.x,self.y,self.zoom,self.config)
            self.nodes = parseNode(self.config)
        if quelle == self.HideNodesAction:
            self.nodes = []
            self.minNodes = []
        if quelle == self.ResetFilterAction:
            self.amenity_typ = None
        if quelle == self.Filter1Action:
            self.amenity_typ = self.config["filter1"]
        if quelle == self.Filter2Action:
            self.amenity_typ = self.config["filter2"]
        if quelle == self.Filter3Action:
            self.amenity_typ = self.config["filter3"]
        if quelle == self.Filter4Action:
            self.amenity_typ = self.config["filter4"]
        if quelle == self.Filter5Action:
            self.amenity_typ = self.config["filter5"]            
        if quelle == self.Filter6Action:
            self.amenity_typ = self.config["filter6"]
        if quelle == self.Filter7Action:
            self.amenity_typ = self.config["filter7"]
        if quelle == self.Filter8Action:
            self.amenity_typ = self.config["filter8"]
        if quelle == self.Filter9Action:
            self.amenity_typ = self.config["filter9"]
        if quelle == self.Filter10Action:
            self.amenity_typ = self.config["filter10"]  
        if quelle == self.AuswahlFilterAction:
            self.afd = AuswahlFilterDialog(self.config)   
            self.afd.exec_()
            self.amenity_typ = self.afd.getText() 
        if quelle == self.NodeFilerResetAction:
            self.node_typ = None
            self.node_value = None
        if quelle == self.NodeFilter1Action:
            self.node_typ = self.config["node_filter1"]
            self.node_value = None
        if quelle == self.NodeFilter2Action:
            self.node_typ = self.config["node_filter2"]
            self.node_value = None
        if quelle == self.NodeFilter3Action:
            self.node_typ = self.config["node_filter3"]
            self.node_value = None
        if quelle == self.NodeFilter4Action:
            self.node_typ = self.config["node_filter4"]
            self.node_value = None
        if quelle == self.NodeFilter5Action:
            self.node_typ = self.config["node_filter5"] 
            self.node_value = None  
        if quelle == self.NodeFilter6Action:
            self.node_typ = self.config["node_filter6"]
            self.node_value = None
        if quelle == self.NodeFilter7Action:
            self.node_typ = self.config["node_filter7"]
            self.node_value = None
        if quelle == self.NodeFilter8Action:
            self.node_typ = self.config["node_filter8"]
            self.node_value = None
        if quelle == self.NodeFilter9Action:
            self.node_typ = self.config["node_filter9"]
            self.node_value = None
        if quelle == self.NodeFilter10Action:
            self.node_typ = self.config["node_filter10"]
            self.node_value = None           
        if quelle == self.NodeFilterAction:
            self.nfd = NodeAuswahlFilterDialog(self.config)   
            self.nfd.exec_()
            (self.node_typ,self.node_value) = self.nfd.getTexte() 
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
        self.initUI()
    
    def mousePressed(self,ev):
        if ev.button() == Qt.LeftButton:
            # Mache den links angeklickten Punkt zum Kartenmittelpunkt
            pos = ev.pos()
            a = pos.x()
            b = pos.y()
            delta = 383 + int(self.config["adjustment"])
            deltax = (float(b-delta) / 255.0) 
            deltay = (float(a-delta) / 255.0)
            self.x = float(self.x) + deltax
            self.y = float(self.y) + deltay
            print(self.x+0.5,self.y+0.5,self.zoom)
            (lat,lon) = calculateLatLon(self.x+0.5,self.y+0.5,self.zoom)
            print(lat,lon)
            print(">>>Vor Amenity")
            # Wenn Amenity vorhanden, dann lade um den neuen Kartenmittelpunkt nach und drcuke die naechstgelegenen
            self.minAmenity = []
            if len(self.amenities) > 0:
                downloadOSMData(self.x,self.y,self.zoom,self.config)
                self.amenities = parseAmenity(self.config)
                self.minAmenity = printNextAmenity(lat,lon,self.zoom,self.amenities,self.amenity_typ)
            print(">>>Nach Amenity")
            # Wenn Node vorhanden, dann lade um den neuen Kartenmittelpunkt nach und drcuke die naechstgelegenen
            print(">>>Vor Nodes")
            self.minNode = []
            if len(self.nodes) > 0:
                print(">>>Vor downloadOSMData")
                downloadOSMData(self.x,self.y,self.zoom,self.config)
                print(">>>Vor parseNode")
                self.nodes = parseNode(self.config)
                print(">>>Vor printNextNode")
                self.minNode = printNextNode(lat,lon,self.zoom,self.nodes,self.node_typ,self.node_value)
            print(">>>Nach Nodes")
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
                self.initUI()
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
        self.initUI()


class AmenityPanel(QWidget):
    """ Anzeige einer Amenity """
    
    def __init__(self,amenity):
        QWidget.__init__(self)
        self.amenity = amenity
        layout = QFormLayout()
        keylist = list(amenity)
        for key in keylist:
            wert = amenity[key]
            label1 = QLabel(key)
            label2 = QLabel(str(wert))
            layout.addRow(label1,label2)
        self.setLayout(layout)
        self.setMinimumSize(400,785)
        self.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
    
    
class NodeAuswahlFilterDialog(QDialog):
    """ Auswahl Dialog fuer Node Filter - grid Layout"""
    
    def __init__(self,config):
        QDialog.__init__(self)
        self.config = config
        self.node_typ = None
        self.node_value = None
        node_typen = kategorisiereNode(config)
        grid = QGridLayout()
        keylist = list(node_typen)
        typen_liste = []
        for key in keylist:
            typen_liste.append((key,node_typen[key]))
        typen_liste.sort()
        i = 0
        j = 0
        for (key,anzahl) in typen_liste:
            butt = QPushButton(self)
            butt.setText(str(key))
            label2 = QLabel(self)
            label2.setText(str(anzahl))
            grid.addWidget(butt,i,j)
            j = j + 1
            grid.addWidget(label2,i,j) 
            j = j + 1
            if j > 7:
                j = 0
                i = i + 1
            butt.clicked.connect(partial(self.butt_clicked, str(key)))
        j = 0
        i = i + 1
        label = QLabel(self)
        label.setText("Auswahl: ")
        self.line_edit = QLineEdit()
        grid.addWidget(label,i,j)
        j = j + 1
        grid.addWidget(self.line_edit,i,j)
        j = j + 1
        if j > 7:
            j = 0
            i = i + 1
        butt1 = QPushButton(self)
        butt1.setText("ok")
        butt2 = QPushButton(self)
        butt2.setText("cancel")
        grid.addWidget(butt1,i,j)
        j = j + 1
        grid.addWidget(butt2,i,j)
        j = j + 1
        if j > 7:
            j = 0
            i = i + 1
        self.setLayout(grid)
        dialog = QDialog()
        dialog.setLayout(grid)
        scrollArea = QScrollArea()    
        scrollArea.setWidget(dialog)
        layout = QVBoxLayout(self)
        layout.addWidget(scrollArea)
        self.setLayout(layout)
        self.setMinimumSize(1000,600)
        butt1.clicked.connect(lambda:self.butt1_clicked())
        butt2.clicked.connect(lambda:self.butt2_clicked())

    def butt_clicked(self,key):
        self.line_edit.setText(key)
             
    def butt1_clicked(self):
        self.node_typ = self.line_edit.text()
        self.nvfd = NodeValueFilterDialog(self.config,self.node_typ)   
        self.nvfd.exec_()
        self.node_value = self.nvfd.getText() 
        self.close()
        
    def butt2_clicked(self):
        self.node_typ = None
        self.close()
        
    def getTexte(self):
        return (self.node_typ,self.node_value)
    
    
class AuswahlFilterDialog(QDialog):
    """ Auswahl Dialog fuer Amenity Filter - grid Layout"""
    
    def __init__(self,config):
        QDialog.__init__(self)
        amenity_typen = kategorisiereAmenity(config)
        grid = QGridLayout()
        keylist = list(amenity_typen)
        typen_liste = []
        for key in keylist:
            typen_liste.append((key,amenity_typen[key]))
        typen_liste.sort(key=itemgetter(1),reverse=True)
        i = 0
        j = 0
        for (key,anzahl) in typen_liste:
            butt = QPushButton(self)
            butt.setText(str(key))
            label2 = QLabel(self)
            label2.setText(str(anzahl))
            grid.addWidget(butt,i,j)
            j = j + 1
            grid.addWidget(label2,i,j) 
            j = j + 1
            if j > 3:
                j = 0
                i = i + 1
            butt.clicked.connect(partial(self.butt_clicked, str(key)))
        j = 0
        i = i + 1
        label = QLabel(self)
        label.setText("Auswahl: ")
        self.line_edit = QLineEdit()
        grid.addWidget(label,i,j)
        j = j + 1
        grid.addWidget(self.line_edit,i,j)
        j = j + 1
        if j > 3:
            j = 0
            i = i + 1
        butt1 = QPushButton(self)
        butt1.setText("ok")
        butt2 = QPushButton(self)
        butt2.setText("cancel")
        grid.addWidget(butt1,i,j)
        j = j + 1
        grid.addWidget(butt2,i,j)
        j = j + 1
        if j > 3:
            j = 0
            i = i + 1
        self.setLayout(grid)
        butt1.clicked.connect(lambda:self.butt1_clicked())
        butt2.clicked.connect(lambda:self.butt2_clicked())

    def butt_clicked(self,key):
        self.line_edit.setText(key)
           
    def butt1_clicked(self):
        self.amenity_typ = self.line_edit.text()
        self.close()
        
    def butt2_clicked(self):
        self.amenity_typ = None
        self.close()
        
    def getText(self):
        return self.amenity_typ



class NodeValueFilterDialog(QDialog):
    """ Auswahl Dialog fuer Node Value - grid Layout"""
    
    def __init__(self,config,node_typ):
        QDialog.__init__(self)
        node_values = kategorisiereNodeValue(config,node_typ)
        grid = QGridLayout()
        keylist = list(node_values)
        value_liste = []
        for key in keylist:
            value_liste.append((key,node_values[key]))
        value_liste.sort(key=itemgetter(1),reverse=True)
        i = 0
        j = 0
        for (key,anzahl) in value_liste:
            butt = QPushButton(self)
            butt.setText(str(key))
            butt.setObjectName(str(key))
            label2 = QLabel(self)
            label2.setText(str(anzahl))
            grid.addWidget(butt,i,j)
            j = j + 1
            grid.addWidget(label2,i,j) 
            j = j + 1
            if j > 3:
                j = 0
                i = i + 1
            butt.clicked.connect(partial(self.butt_clicked, str(key)))
        j = 0
        i = i + 1
        label = QLabel(self)
        label.setText("Auswahl: ")
        self.line_edit = QLineEdit()
        grid.addWidget(label,i,j)
        j = j + 1
        grid.addWidget(self.line_edit,i,j)
        j = j + 1
        if j > 3:
            j = 0
            i = i + 1
        butt1 = QPushButton(self)
        butt1.setText("ok")
        butt2 = QPushButton(self)
        butt2.setText("cancel")
        grid.addWidget(butt1,i,j)
        j = j + 1
        grid.addWidget(butt2,i,j)
        j = j + 1
        if j > 3:
            j = 0
            i = i + 1
        self.setLayout(grid)
        butt1.clicked.connect(lambda:self.butt1_clicked())
        butt2.clicked.connect(lambda:self.butt2_clicked())
           
    def butt_clicked(self,key):
        self.line_edit.setText(key)
  
    def butt1_clicked(self):
        self.node_value = self.line_edit.text()
        self.close()
        
    def butt2_clicked(self):
        self.node_value = None
        self.close()
        
    def getText(self):
        return self.node_value

