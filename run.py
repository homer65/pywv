# coding: latin-1
import sys
from tile import BildController
from PyQt5.QtWidgets import QApplication

def init(pfad,config):
    """ Lies Configuration aus ini Datei """
    print(pfad)
    with open(pfad,"r") as f:
        for zeile in f:
            worte = zeile.split("=")
            if len(worte) > 1:
                key = worte[0]
                wert = worte[1]
                if key == "x":
                    wert = str(float(wert) - 0.5)
                if key == "y":
                    wert = str(float(wert) - 0.5)
                config[key] = wert

def main():
    app = QApplication(sys.argv)
    config = {}
    # Setze Default Werte für Konfiguration
    config["temphtml"] = "C:\\Downloads\\MyOpenStreetMap.html"
    config["osmxml"] = "C:\\Downloads\\MyOpenStreetMap.xml"
    config["pdfFile"] = "C:\\Downloads\\MyOpenStreetMap.pdf"
    config["tileCache"] = "C:\\Downloads\\TileCache"
    config["x"] = "21802"
    config["y"] = "34084"
    config["zoom"] = "16"
    config["adjustment"] = "9"
    config["tileserver"] = "thunderforest"
    config["filter1"] = "bar"
    config["filter2"] = "bbq"
    config["filter3"] = "biergarten"
    config["filter4"] = "cafe"
    config["filter5"] = "fast_food"
    config["filter6"] = "ice_cream"
    config["filter7"] = "pub"
    config["filter8"] = "restaurant"
    config["filter9"] = "charging_station"
    config["filter10"] = "fuel"
    config["node_filter1"] = "shop"
    config["node_filter2"] = "leisure"
    config["node_filter3"] = "place"
    config["node_filter4"] = "operator"
    config["node_filter5"] = "public_transport"
    config["node_filter6"] = "wheelchair"
    config["node_filter7"] = "website"
    config["node_filter8"] = "office"
    config["node_filter9"] = "tourism"
    config["node_filter10"] = "brand"
    # ini Datei wird normalerweise über Argument beim Aufruf angegeben
    # Wenn keine ini Datei im Aufruf angegeben wird nehme run.ini
    if len(sys.argv) > 1:
        init(sys.argv[1],config)
    else:
        init("run.ini",config)
    x = float(config["x"])
    y = float(config["y"])
    zoom = int(config["zoom"])
    # Aufruf des GUI
    panel = BildController(x,y,zoom,config)
    panel.show()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main()