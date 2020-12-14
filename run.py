# coding: latin-1
import sys
from tile import BildController
from PyQt5.QtWidgets import QApplication

def init(pfad,config):
    # Lies Configuration aus ini Datei
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
    # Setze Default Werte für Parameter
    config["temphtml"] = "C:\\Downloads\\MyOpenStreetMap.html"
    config["osmxml"] = "C:\\Downloads\\MyOpenStreetMap.xml"
    config["pdfFile"] = "C:\\Downloads\\MyOpenStreetMap.pdf"
    config["tileCache"] = "C:\\Downloads\\TileCache"
    config["x"] = "21802"
    config["y"] = "34084"
    config["z"] = "16"
    config["adjustment"] = "9"
    config["tileserver"] = "thunderforest"
    # ini Datei wird normalerweise über Argument beim Aufruf angegeben
    # Wenn keine ini Datei im Aufruf angegeben wird nehme run.ini
    if len(sys.argv) > 1:
        init(sys.argv[1],config)
    else:
        init("run.ini",config)
    x = float(config["x"])
    y = float(config["y"])
    z = int(config["z"])
    # Aufruf des GUI
    panel = BildController(x,y,z,config)
    panel.show()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main()