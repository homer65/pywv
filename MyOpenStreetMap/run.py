import sys
from Parameter import Parameter
from Tile import BildController
from PyQt5.QtWidgets import QApplication
parameter = Parameter()
def myinit(pfad):
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
            parameter.setParm(key,wert)
        #print(satz)
    f.close()
    return
app = QApplication(sys.argv)
parameter.setParm("temphtml","C:\\Downloads\\MyOpenStreetMap.html")
parameter.setParm("osmxml","C:\\Downloads\\MyOpenStreetMap.xml")
parameter.setParm("pdfFile","C:\\Downloads\\MyOpenStreetMap.pdf")
parameter.setParm("tileCache","C:\\Downloads\\TileCache")
parameter.setParm("x","21802")
parameter.setParm("y","34084")
parameter.setParm("z","16")
parameter.setParm("adjustment","9")
if len(sys.argv) > 1:
    myinit(sys.argv[1])
else:
    myinit("run.ini")
x = float(parameter.getParm("x"))
y = float(parameter.getParm("y"))
z = int(parameter.getParm("z"))
panel = BildController(x,y,z)
panel.show()
sys.exit(app.exec_())