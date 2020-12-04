class Parameter():
    parms = {}
    def __init__(self):
        return
    def setParm(self,key,wert):
        self.parms[key] = wert
        return
    def getParm(self,key):
        return self.parms[key]
        