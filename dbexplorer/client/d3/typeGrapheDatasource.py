# -*- coding: utf-8 -*-
import sys
from PySide import QtCore, QtGui, QtWebKit
from dbexplorer.server.service import Service
import simplejson as json

        
class TypeService(QtCore.QObject):
    def __init__(self,typageView,bytype):
        QtCore.QObject.__init__(self)        
        
        self.typageView = typageView
        
        self.bytype = bytype
        
    @QtCore.Slot(str)
    def click(self,col):
              
        
        [colname,colnatiftype,coltype,count] = self.typageView.getCol(col,self.typageView.cols)
        self.currentCol = col 
        self.typageView.label.setText("Colonne <b>%s</b>, Type natif <i>%s</i>, Nouveau Type :"%(col,colnatiftype))
        
        self.typageView.label.setEnabled(True)
        self.typageView.typeChoice.setEnabled(True)
        self.typageView.exampleData.setEnabled(True)
        
        
        sampleData = self.typageView.service.getSampleData(self.typageView.datasourceId,self.typageView.tableName,col)
        self.typageView.exampleData.clear()
        self.typageView.exampleData.addItems(sampleData)
        
        self.typageView.typeChoice.blockSignals(True)
        self.typageView.typeChoice.setCurrentIndex(self.typageView.typeModel.index(coltype))        
        self.typageView.typeChoice.blockSignals(False)
    
        
            
    def readPP(self):
        return self.ppval
 
    def setPP(self,val):
        self.ppval = val
        
    dataset = QtCore.Property(str, readPP, setPP)    

class WebPage(QtWebKit.QWebPage):
    def javaScriptConsoleMessage(self, msg, line, source):
        print '%s line %d: %s' % (source, line, msg)
        pass

class MyTable(QtGui.QTableView):
    def __init__(self):
        QtGui.QTableView.__init__(self)
        
    def sizeHintForColumn(self,column):
        i = super(QtGui.QTableView, self).sizeHintForColumn(column)                
        
        return i
    
    
class TypageView(QtGui.QWidget):
    def __init__(self,transtypageView,datasourceId,service,tables):
        QtGui.QWidget.__init__(self)                
        self.layout  = QtGui.QGridLayout()
        self.setLayout(self.layout)
        
        self.webView = QtWebKit.QWebView()
        self.webView.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self.layout.addWidget(self.webView,0,0,1,2) #3,2                
        self.webView.loadFinished.connect(self.loadFinished)        
        self.label = QtGui.QLabel("Colonne <b>%s</b>, Type natif <i>%s</i>, Nouveau Type :"%("--","--"))
        
        self.typeChoice = QtGui.QComboBox()
        self.typeModel = ['INT','DEC','STR','BOOL','DATE','TIME','DATETIME']
        self.typeChoice.addItems(self.typeModel)
        self.typeChoice.currentIndexChanged.connect(self.validClick)
        
        
        
        self.exampleData = QtGui.QListWidget()
        self.exampleData.setMaximumHeight(50)
        self.exampleData.setAlternatingRowColors(True)                
        
        self.label.setEnabled(False)
        self.typeChoice.setEnabled(False)
        self.exampleData.setEnabled(False)
        
        
        self.layout.addWidget(self.label,1,0)
        self.layout.addWidget(self.typeChoice,1,1)
        self.layout.addWidget(self.exampleData,2,0,2,2)
        
        
        self.transtypageView = transtypageView
        self.service = service
        self.datasourceId = datasourceId
        self.tables = tables
        
        
    def getCol(self,colname,cols):
        for c in cols:
            if c[0] == colname:
                return c
            
        return None
    
            
    def validClick(self):
        if not hasattr(self.typeService,'currentCol') or self.typeService.currentCol is None:
            return
        
        
        index = self.typeChoice.currentIndex()
        newtype = self.typeModel[index]
        colname = self.typeService.currentCol
        
        
        isNewTypeValid,notvalids = self.service.isNewTypeValid(self.datasourceId,self.tableName,colname,newtype)
        
        if not isNewTypeValid:
            errorMessageDialog = QtGui.QErrorMessage(self)
            errorMessageDialog.setWindowTitle(_(u'Erreur Transtypage'))
            error = _(u"Attention : certaines valeurs de la colonne ne sont pas compatibles avec le nouveau type choisi : ")
            msg=[error]       
            for i in notvalids:
                msg.append("<b>%s</b>"%(i,))
            
            errorMessageDialog.resize(500,500)        
            errorMessageDialog.raise_()          
            errorMessageDialog.setModal(True)               
            errorMessageDialog.showMessage(('<br/>'.join(msg)))
        
        newcols = []
        for c in self.cols:
            if c[0] == colname :
                c[2] = newtype
                newcols.append(c)
            else:
                newcols.append(c)
        
        
        
        
        self.render(self.tableName,newcols)
        self.transtypageView.newTypes[self.tableName] = newcols
        
        
        
    def render(self,tableName,cols) :
        #format de cols : [[colname,typenatif,type],[],...]                    
        self.tableName = tableName
        self.cols = cols
        
        
        d = {}
        d['name'] = self.tableName
        d['children'] = []
        bytype={}
        for col in cols:
            [colname,typenatif,type,count] = col
            try:
                tab = bytype[type] # get 
            except:
                tab = []
                bytype[type] = tab
                
            tab.append(col)
        
        for t in bytype:
            typechild = {}
            typechild['name'] = t
            typechild['children'] = []
            
            for col in bytype[t]:
                el={}
                el['name'] = '%s'%(col[0])
                el['size'] = col[3]
                typechild['children'].append(el)
                
            d['children'].append(typechild)
        
        
        from json import dumps           
        self.dataset = dumps(d)
        
        self.typeService = TypeService(self,bytype)
        self.typeService.dataset = self.dataset
        
        self.typeChoice.blockSignals(True)
        self.label.setText("Colonne <b>%s</b>, Type natif <i>%s</i>, Nouveau Type :"%("",""))        
        self.exampleData.clear()
        self.label.setEnabled(False)        
        self.typeChoice.setEnabled(False)
        self.exampleData.setEnabled(False)
        
        
        self.typeChoice.setCurrentIndex(0)        
        self.typeChoice.blockSignals(False)
                
        
        page = WebPage()
        page.mainFrame().addToJavaScriptWindowObject("typeService", self.typeService)
        
        self.webView.setPage(page)
        

        
        self.webView.load(QtCore.QUrl("./resources/typeTreemap.html"))

        
    def loadFinished(self):               
        self.webView.page().mainFrame().evaluateJavaScript('drawChartFromPython()');
        
   

class TranstypageView(QtGui.QWidget):
    def __init__(self,mainWidget,datasourceId,service,tables):
        QtGui.QWidget.__init__(self)        
        self.layout  = QtGui.QGridLayout()
        self.setLayout(self.layout)
        self.mainWidget = mainWidget
        self.datasourceId = datasourceId
        self.service = service
        self.tables = tables
        self.comboTables = QtGui.QComboBox()                
        self.comboTables.currentIndexChanged.connect(self.changeTable)
        self.typeview = TypageView(self,datasourceId,service,tables)
        self.newTypes={}
        
        self.layout.addWidget(self.comboTables)
        self.layout.addWidget(self.typeview)
    
    def result(self):
        return self.newTypes    
    def render(self) :
        self.listeTables=[]
        for name in self.tables:
            self.listeTables.append(name)
        
        self.comboTables.clear()    
        self.comboTables.addItems(self.listeTables)   
            
        self.comboTables.setCurrentIndex(0)
        
    
    def changeTable(self):
        index = self.comboTables.currentIndex()
        
        tableName = self.tables[index]
        tableSchema = self.service.getTableSchema(self.datasourceId,tableName)
        
        cols=[]
        for c in tableSchema['cols']:
            col = []
            col.append(c['name'])
            col.append(c['typenatif'])
            col.append(c['type'])
            col.append(c['count'])
            cols.append(col)
            
        
        self.typeview.render(tableName,cols)
        
        pass
    
