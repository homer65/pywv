import sys
from MyOpenStreetMap.tile import BildController
from PyQt5.QtWidgets import QApplication

def init(pfad,parameter):
    print(pfad)
    f = open(pfad,"r")
    for zeile in f:
        satz = zeile[:-1] 
        worte = satz.split("=")
        if len(worte) > 1:
            key = worte[0]
            wert = worte[1]
            if key == "x":
                wert = str(float(wert) - 0.5)
            if key == "y":
                wert = str(float(wert) - 0.5)
            parameter[key] = wert
    f.close()
    return parameter

def main():
    app = QApplication(sys.argv)
    parameter = {}
    parameter["temphtml"] = "C:\\Downloads\\MyOpenStreetMap.html"
    parameter["osmxml"] = "C:\\Downloads\\MyOpenStreetMap.xml"
    parameter["pdfFile"] = "C:\\Downloads\\MyOpenStreetMap.pdf"
    parameter["tileCache"] = "C:\\Downloads\\TileCache"
    parameter["x"] = "21802"
    parameter["y"] = "34084"
    parameter["z"] = "16"
    parameter["adjustment"] = "9"
    if len(sys.argv) > 1:
        parameter = init(sys.argv[1],parameter)
    else:
        parameter = init("run.ini",parameter)
    x = float(parameter["x"])
    y = float(parameter["y"])
    z = int(parameter["z"])
    panel = BildController(x,y,z,parameter)
    panel.show()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main()