#
# OWScatterPlotGraph.py
#
# the base for scatterplot

from OWVisGraph import *


###########################################################################################
##### CLASS : OWSCATTERPLOTGRAPH
###########################################################################################
class OWScatterPlotGraph(OWVisGraph):
    def __init__(self, parent = None, name = None):
        "Constructs the graph"
        OWVisGraph.__init__(self, parent, name)

        self.jitterContinuous = 0
        
        self.enabledLegend = 0

    def enableGraphLegend(self, enable):
        self.enabledLegend = enable

    def setJitterContinuous(self, enable):
        self.jitterContinuous = enable

    def setShowFilledSymbols(self, filled):
        self.showFilledSymbols = filled
        
    #
    # scale data at index index to the interval 0 - 1
    #
    def scaleData(self, data, index):
        attr = data.domain[index]
        temp = [];
        # is the attribute discrete
        if attr.varType == orange.VarTypes.Discrete:
            # we create a hash table of variable values and their indices
            variableValueIndices = self.getVariableValueIndices(data, index)

            count = float(len(attr.values))
            for i in range(len(data)):
                #val = (1.0 + 2.0*float(variableValueIndices[data[i][index].value])) / float(2*count)
                val = float(variableValueIndices[data[i][index].value]) / float(count)
                temp.append(val)
            return (temp, (0, count-1))

                    
        # is the attribute continuous
        else:
            # first find min and max value
            i = 0
            while data[i][attr].isSpecial() == 1: i+=1
            min = data[i][attr].value
            max = data[i][attr].value
            for item in data:
                if item[attr].isSpecial() == 1: continue
                if item[attr].value < min:
                    min = item[attr].value
                elif item[attr].value > max:
                    max = item[attr].value

            diff = max - min
            # create new list with values scaled from 0 to 1
            for i in range(len(data)):
                temp.append((data[i][attr].value - min) / diff)

            return (temp, (min, max))

    #
    # set new data and scale its values
    #
    def setData(self, data):

        self.rawdata = data
        self.scaledData = []
        self.scaledDataAttributes = []
        
        if data == None: return

        self.attrVariance = []
        for index in range(len(data.domain)):
            attr = data.domain[index]
            self.scaledDataAttributes.append(attr.name)
            (scaled, variance)= self.scaleData(data, index)
            self.scaledData.append(scaled)
            self.attrVariance.append(variance)


    #
    # update shown data. Set labels, coloring by className ....
    #
    def updateData(self, xAttr, yAttr, colorAttr, shapeAttr, sizeShapeAttr, showColorLegend, statusBar):
        self.clear()
        self.enableLegend(0)
        self.statusBar = statusBar

        (xVarMin, xVarMax) = self.attrVariance[self.scaledDataAttributes.index(xAttr)]
        (yVarMin, yVarMax) = self.attrVariance[self.scaledDataAttributes.index(yAttr)]
        xVar = xVarMax - xVarMin
        yVar = yVarMax - yVarMin
        MAX_HUE_VAL = 300           # hue value can go to 360, but at 360 it produces the same color as at 0 so we make the interval shorter
        MIN_SHAPE_SIZE = 10
        MAX_SHAPE_DIFF = 10

        if len(self.scaledData) == 0: self.updateLayout(); return

        if self.rawdata.domain[xAttr].varType == orange.VarTypes.Continuous:
            self.setXlabels(None)
        else:
            self.setXlabels(self.getVariableValuesSorted(self.rawdata, xAttr))
            self.setAxisScale(QwtPlot.xBottom, xVarMin - (self.jitterSize * xVar / 80.0), xVarMax + (self.jitterSize * xVar / 80.0) + showColorLegend * xVar/20, 1)            

        if self.rawdata.domain[yAttr].varType == orange.VarTypes.Continuous: self.setYLlabels(None)
        else:
            self.setYLlabels(self.getVariableValuesSorted(self.rawdata, yAttr))
            self.setAxisScale(QwtPlot.yLeft, yVarMin - (self.jitterSize * yVar / 80.0), yVarMax + (self.jitterSize * yVar / 80.0), 1)

        if self.showXaxisTitle == 1: self.setXaxisTitle(xAttr)
        if self.showYLaxisTitle == 1: self.setYLaxisTitle(yAttr)
        
        colorIndex = -1
        if colorAttr != "" and colorAttr != "(One color)":
            colorIndex = self.scaledDataAttributes.index(colorAttr)
            if self.rawdata.domain[colorAttr].varType == orange.VarTypes.Discrete: MAX_HUE_VAL = 360

        shapeIndex = -1
        shapeIndices = {}
        if shapeAttr != "" and shapeAttr != "(One shape)" and len(self.rawdata.domain[shapeAttr].values) < 11:
            shapeIndex = self.scaledDataAttributes.index(shapeAttr)
            shapeIndices = self.getVariableValueIndices(self.rawdata, shapeAttr)

        sizeShapeIndex = -1
        if sizeShapeAttr != "" and sizeShapeAttr != "(One size)":
            sizeShapeIndex = self.scaledDataAttributes.index(sizeShapeAttr)

        shapeList = [QwtSymbol.Ellipse, QwtSymbol.Rect, QwtSymbol.Diamond, QwtSymbol.Triangle, QwtSymbol.DTriangle, QwtSymbol.UTriangle, QwtSymbol.LTriangle, QwtSymbol.RTriangle, QwtSymbol.Cross, QwtSymbol.XCross, QwtSymbol.StyleCnt]

        # create hash tables in case of discrete X axis attribute
        attrXIndices = {}
        discreteX = 0
        if self.rawdata.domain[xAttr].varType == orange.VarTypes.Discrete:
            discreteX = 1
            attrXIndices = self.getVariableValueIndices(self.rawdata, xAttr)

        # create hash tables in case of discrete Y axis attribute
        attrYIndices = {}
        discreteY = 0
        if self.rawdata.domain[yAttr].varType == orange.VarTypes.Discrete:
            discreteY = 1
            attrYIndices = self.getVariableValueIndices(self.rawdata, yAttr)
        
        self.curveKeys = []
        for i in range(len(self.rawdata)):
            if discreteX == 1:
                x = attrXIndices[self.rawdata[i][xAttr].value] + self.rndCorrection(float(self.jitterSize * xVar) / 100.0)
            elif self.jitterContinuous == 1:
                x = self.rawdata[i][xAttr].value + self.rndCorrection(float(self.jitterSize * xVar) / 100.0)
            else:
                x = self.rawdata[i][xAttr].value

            if discreteY == 1:
                y = attrYIndices[self.rawdata[i][yAttr].value] + self.rndCorrection(float(self.jitterSize * yVar) / 100.0)
            elif self.jitterContinuous == 1:
                y = self.rawdata[i][yAttr].value + self.rndCorrection(float(self.jitterSize * yVar) / 100.0)
            else:
                y = self.rawdata[i][yAttr].value

            newColor = QColor(0,0,0)
            if colorIndex != -1:
                newColor.setHsv(self.scaledData[colorIndex][i]*MAX_HUE_VAL, 255, 255)

            symbol = shapeList[0]
            if shapeIndex != -1:
                symbol = shapeList[shapeIndices[self.rawdata[i][shapeIndex].value]]

            size = self.pointWidth
            if sizeShapeIndex != -1:
                size = MIN_SHAPE_SIZE + round(self.scaledData[sizeShapeIndex][i] * MAX_SHAPE_DIFF)

            newCurveKey = self.insertCurve(str(i))

            symbolBrush = QBrush(QBrush.NoBrush)
            if self.showFilledSymbols == 1:
                symbolBrush = QBrush(newColor)
            newSymbol = QwtSymbol(symbol, symbolBrush, QPen(newColor), QSize(size, size))
            self.setCurveSymbol(newCurveKey, newSymbol)
            self.setCurveData(newCurveKey, [x], [y])
            self.curveKeys.append(newCurveKey)

            ##########
            # we add a tooltip for this point
            r = QRectFloat(x-xVar/100.0, y-yVar/100.0, xVar/50.0, yVar/50.0)
            text= self.getExampleText(self.rawdata, self.rawdata[i])
            self.tips.addToolTip(r, text)
            ##########
            

        # show legend if necessary
        if self.enabledLegend == 1:
            if colorIndex != -1 and self.rawdata.domain[colorIndex].varType == orange.VarTypes.Discrete:
                varName = self.rawdata.domain[colorIndex].name
                varValues = self.getVariableValuesSorted(self.rawdata, colorIndex)
                numColors = len(self.rawdata.domain[colorIndex].values)
                for ind in range(numColors):
                    newColor = QColor()
                    newColor.setHsv(float(ind) / float(numColors) * MAX_HUE_VAL, 255, 255)
                    self.addCurve(varName + "=" + varValues[ind], newColor, newColor, self.pointWidth, enableLegend = 1)

            if shapeIndex != -1 and self.rawdata.domain[shapeIndex].varType == orange.VarTypes.Discrete:
                varName = self.rawdata.domain[shapeIndex].name
                varValues = self.getVariableValuesSorted(self.rawdata, shapeIndex)
                for ind in range(len(self.rawdata.domain[shapeIndex].values)):
                    self.addCurve(varName + "=" + varValues[ind], QColor(0,0,0), QColor(0,0,0), self.pointWidth, symbol = shapeList[ind], enableLegend = 1)

            if sizeShapeIndex != -1 and self.rawdata.domain[sizeShapeIndex].varType == orange.VarTypes.Discrete:
                varName = self.rawdata.domain[sizeShapeIndex].name
                varValues = self.getVariableValuesSorted(self.rawdata, sizeShapeIndex)
                for ind in range(len(varValues)):
                    self.addCurve(varName + "=" + varValues[ind], QColor(0,0,0), QColor(0,0,0), MIN_SHAPE_SIZE + round(ind*MAX_SHAPE_DIFF/len(varValues)), enableLegend = 1)


        if colorAttr != "" and showColorLegend == 1:
            for i in range(1000):
                x0 = xVarMax + xVar/100
                x1 = x0 + xVar/20
                y = yVarMin + i*yVar/1000
                newCurveKey = self.insertCurve(str(i))
                newColor = QColor()
                newColor.setHsv(float(i*MAX_HUE_VAL)/1000.0, 255, 255)
                self.setCurvePen(newCurveKey, QPen(newColor))
                self.setCurveData(newCurveKey, [x0,x1], [y,y])
        # -----------------------------------------------------------
        # -----------------------------------------------------------
        
    
if __name__== "__main__":
    #Draw a simple graph
    a = QApplication(sys.argv)        
    c = OWScatterPlotGraph()
        
    a.setMainWidget(c)
    c.show()
    a.exec_loop()
