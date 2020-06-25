# -*- coding: utf-8 -*-
"""
Created on Tue Jun  9 16:37:40 2020

@author: SALLEJAUNE
"""

from PyQt5.QtWidgets import QGridLayout,QVBoxLayout,QWidget,QApplication,QGroupBox,QTabWidget,QMainWindow,QHBoxLayout
from PyQt5.QtWidgets import QSizePolicy,QDockWidget,QLabel,QSpinBox,QDoubleSpinBox,QPushButton,QTableWidget,QTableWidgetItem,QAbstractItemView,QComboBox
from pyqtgraph.Qt import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import sys,time
import pathlib,os
import qdarkstyle
import camera
from PyQt5 import QtGui 
import numpy as np
import deap # pip install deap https://github.com/DEAP/deap
import random

from deap import creator
from deap import tools
from deap import base



class WIDGETDM(QWidget):
    
        #additionnal widget to show and control DM
        def __init__(self,parent):
            
            super(WIDGETDM, self).__init__()
            self.parent=parent
            p = pathlib.Path(__file__)
            sepa=os.sep
            self.icon=str(p.parent) + sepa+'icons'+sepa
            self.setWindowIcon(QIcon(self.icon+'LOA.png'))
            self.isWinOpen=False
            self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
            self.setup()
            self.actionButton()
            
        def setup(self):   
            print('i')
            vlayout=QVBoxLayout()
            hlayout=QHBoxLayout()
            self.setDMButton=QPushButton('Set DM Value')
            self.saveDMButton=QPushButton('Save DM Value')
            self.loadDMButton=QPushButton('Load DM Value')
            self.readDMButton=QPushButton('read DM Value')
            hlayout.addWidget(self.setDMButton)
            hlayout.addWidget(self.saveDMButton)
            hlayout.addWidget(self.loadDMButton)
            hlayout.addWidget(self.readDMButton)
            vlayout.addLayout(hlayout)
            self.table=QTableWidget()
            
            self.table.setHorizontalHeaderLabels(('Actuator n:','Position'))
            self.table.setColumnCount(37)
            self.table.setRowCount(1)
            self.table.horizontalHeader().setVisible(True)
            self.table.setAlternatingRowColors(True)
            self.table.resizeColumnsToContents()
            # self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)# no modifiable
            vlayout.addWidget(self.table)
            self.setLayout(vlayout)
            self.setWindowTitle('Deformable Control')
            self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        
        def actionButton(self):
            self.setDMButton.clicked.connect(self.setDMvalue)
            self.saveDMButton.clicked.connect(self.saveDMvalue)
            self.loadDMButton.clicked.connect(self.loadDMvalue)
            self.readDMButton.clicked.connect(self.readDMvalue)
        def setDMvalueonTable(self,individu) :
            for i in range (0,len(individu)):
                self.table.setItem(0, i, QTableWidgetItem(str(round(individu[i],2))))
               
        def setDMvalue(self):
            print('set DM ')
            time.sleep(1)
            return 'ok'
        def saveDMvalue(self ):
            self.TableSauv=[]
            print('save dm parameters')
            fname=QtGui.QFileDialog.getSaveFileName(self,"Save Measurements as txt file")
            for col in range (0,self.parent.nbIndParameters):
                print('col',col)
                val=self.table.item(0,col).text().strip()
                self.TableSauv.append(val)
            
            f=open(str(fname[0])+'.txt','w')
            f.write("\n".join(self.TableSauv))
            f.close()
        
        def loadDMvalue(self):
            fname=QtGui.QFileDialog.getOpenFileName(self,"Open DM File")
            fichier=fname[0]
            ext=os.path.splitext(fichier)[1]
        
            if ext=='.txt': # text file
                Table=np.loadtxt(str(fichier))
                for i in range (0,len(Table)):
                    self.table.setItem(0, i, QTableWidgetItem(str(round(Table[i],2))))
            
        def readDMvalue(self): 
            print('read DM value')
            Table=[1,2,3,4,5]
            for i in range (0,len(Table)):
                    self.table.setItem(0, i, QTableWidgetItem(str(round(Table[i],2))))
        def closeEvent(self, event):
            """ when closing the window
            """
            self.isWinOpen=False  


class WIDGETRESULT(QWidget):
        #additionnal widget to show result of algo
        def __init__(self,parent):
            
            super(WIDGETRESULT, self).__init__()
            p = pathlib.Path(__file__)
            sepa=os.sep
            self.icon=str(p.parent) + sepa+'icons'+sepa
            self.setWindowIcon(QIcon(self.icon+'LOA.png'))
            self.isWinOpen=False
            self.setup()
            self.actionButton()
            self.parent=parent
            
        def setup(self):   
            
            vlayout=QVBoxLayout()
           
            gridbox=QGridLayout()
            
            self.generationLabel=QLabel("Generation n° :")
            self.generation=QComboBox()
            self.generation.setMaximumWidth(80)
            self.generation.addItem('0')
            gridbox.addWidget(self.generationLabel,0,0)
            gridbox.addWidget(self.generation,0,1)
            
            
            
            vlayout.addLayout(gridbox)
            
            self.tableResult=QTableWidget()
            self.tableResult.setHorizontalHeaderLabels(('Actuator n:','Position'))
            
            self.tableResult.setColumnCount(40)
            self.tableResult.setRowCount(1)
            self.tableResult.horizontalHeader().setVisible(True)
            self.tableResult.verticalHeader().setVisible(True)
            self.tableResult.setAlternatingRowColors(True)
            self.tableResult.resizeColumnsToContents()
            self.tableResult.setEditTriggers(QAbstractItemView.NoEditTriggers)# no modifiable
            vlayout.addWidget(self.tableResult)
            
            self.setLayout(vlayout)
            self.setWindowTitle('RESULTS')
            self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
            
            
        def actionButton(self):
            self.generation.currentIndexChanged.connect(self.actionGeneration)
            
        def initTab(self):
            self.generation.clear()
           
            for f in range (0,self.parent.gmax+1):
                self.generation.addItem(str(f))
                
        def actionGeneration(self)   :
            
            gene=str(self.generation.currentIndex())
            
            if int(gene)>=0:
                            
                popGene=self.parent.populationTotale['generation'+gene]
                nbParameter=len(popGene[0])
                nbIndividu=int(self.parent.popValue)
                print('nb parametre',nbParameter)
                print('nb individu',nbIndividu)
                # print('population generale à la generation: ',gene)
                # print(popGene)
                
                
                
                self.tableResult.setRowCount(nbIndividu+2)
                for k in range(0,nbIndividu):
                    valueIndividu=self.parent.fitnessesTot['generation'+str(gene)][k][0]
                    itemTable= QTableWidgetItem(str(valueIndividu))
                    itemTable.setBackground(QtGui.QColor(255,125,125))
                    self.tableResult.setItem(k,nbParameter+1,itemTable)
                    for i in range (0,nbParameter): 
                        self.tableResult.setItem(k, i, QTableWidgetItem(str(round(popGene[k][i],2))))
                        
            
        def closeEvent(self, event):
            """ when closing the window
            """
            self.isWinOpen=False  




class ALGO(QWidget):
    """
        Qwidget 

    """
     
    
    def __init__(self,cam='cam1',**kwds):
        super(ALGO, self).__init__()
        
        self.kwds=kwds
        self.cam=cam     
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint) # set window on the top   
        
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        p = pathlib.Path(__file__)
        sepa=os.sep
        self.icon=str(p.parent) + sepa + 'icons' +sepa
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.popValue=10
        self.geneValueMax=1
        self.nbIndParameters=5#37 # number of gene 
        self.dmMax=10
        self.setup()
        self.actionButton()
        self.populationTotale=dict()
        self.fitnessesTot=dict()
        
        self.iniDone=False
        
        
        ## init parameter for genetic algorithm
        
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))

        creator.create("Individual", list, fitness=creator.FitnessMax)


        self.toolbox = base.Toolbox()
        # Attribute generator 
        self.toolbox.register("attr_bool", random.randint, -self.dmMax, self.dmMax) # nombre entier entre 0 et 10 uniform
        self.toolbox.register("evaluate", self.evalOneMax)
        self.toolbox.register("mate", tools.cxTwoPoint) #crossOver operator 
        self.toolbox.register("mutate", tools.mutFlipBit, indpb=0.05) # mutation 

        # operator for selecting individuals for breeding the next
        # generation: each individual of the current generation
        # is replaced by the 'fittest' (best) of three individuals
        # drawn randomly from the current generation :
        self.toolbox.register("select", tools.selTournament, tournsize=3)
        self.toolbox.register("individual", tools.initRepeat, creator.Individual,self.toolbox.attr_bool, self.nbIndParameters) # =nombre de genes de l'individu
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
         #CXPB  is the probability with which two individuals
    #       are crossed
    #
        # MUTPB is the probability for mutating an individual
        self.CXPB= 0.5
        self.MUTPB= 0.2
        
        
        
    def setup(self):
        # windows setup : 
            
        windowLayout=QVBoxLayout()
        hLayout=QHBoxLayout()  
        gridbox=QGridLayout()
        gridbox.setVerticalSpacing(1)
        gridbox.setHorizontalSpacing(3)
        gridbox.setSpacing(10)
        self.maxLabel=QComboBox(self)
        self.maxLabel.addItem('Max')
        self.maxLabel.addItem('Sum')
        self.maxValueBox=QLabel(self)
        
        gridbox.addWidget(self.maxLabel,0,0)
        gridbox.addWidget(self.maxValueBox,0,1)
    
        self.popLabel=QLabel("nb individu :")
        self.popValueBox=QSpinBox(self)
        self.popValueBox.setValue(self.popValue)
        gridbox.addWidget(self.popLabel,1,0)
        gridbox.addWidget(self.popValueBox,1,1)
        
        self.geneLabel=QLabel("nb max de generation")
        self.geneValueBox=QSpinBox(self)
        self.geneValueBox.setValue(self.geneValueMax)
        gridbox.addWidget(self.geneLabel,2,0)
        gridbox.addWidget(self.geneValueBox,2,1)
        
        self.initButton=QPushButton("Init")
        self.showDMButton=QPushButton("DM")
        gridbox.addWidget(self.initButton,3,0)
        gridbox.addWidget(self.showDMButton,3,1)
        
        self.startButton=QPushButton("Start")
        self.stopButton=QPushButton("Stop")
        gridbox.addWidget(self.startButton,4,0)
        gridbox.addWidget(self.stopButton,4,1)
        self.showResultButton=QPushButton("Result")
        gridbox.addWidget(self.showResultButton,5,0)
        
         
        # widget camera
        
        self.widgetCam=camera.CAMERA(cam=self.cam,affLight=False,multi=False,**self.kwds)
        
        # we add algo button to widget camera
        
        self.widgetCam.vbox1.addLayout(gridbox)
        
        
        hLayout.addWidget(self.widgetCam)
        windowLayout.addLayout(hLayout)
        self.setContentsMargins(1,1,1,1)
        self.setLayout(windowLayout)
     
        self.winDM=WIDGETDM(self)
        self.winResult=WIDGETRESULT(self)
        self.winResult.tableResult.setColumnCount(self.nbIndParameters+2)
        
        
    def actionButton(self):
        # button definition action
        
        self.widgetCam.datareceived.connect(self.newData)
        self.popValueBox.valueChanged.connect(self.setPopValue)
        self.geneValueBox.valueChanged.connect(self.setGeneValue)
        self.initButton.clicked.connect(self.iniPop)
        self.showDMButton.clicked.connect(lambda:self.open_widget(self.winDM))
        self.showResultButton.clicked.connect(lambda:self.open_widget(self.winResult))
        self.startButton.clicked.connect(self.startAlgo)
        self.stopButton.clicked.connect(self.stopAlgo)
    
       
    def newData(self):
        
        # calculate the ROI of the newdata received
        interest=self.maxLabel.currentIndex() # if=0 max if 1 sum
        
        if self.widgetCam.visualisation.ite=='cercle' :
            self.widgetCam.visualisation.CercChanged() # update ROI
            if interest==0:
                self.maxInterest=(self.widgetCam.visualisation.cut).max() # take the max
            if interest==1:
                self.maxInterest=(self.widgetCam.visualisation.cut).sum()
        elif self.widgetCam.visualisation.ite=='rect' :
            self.widgetCam.visualisation.RectChanged() # update ROI
            if interest==0:
                self.maxInterest=(self.widgetCam.visualisation.cut).max() # take the max
            if interest==1:
                self.maxInterest=(self.widgetCam.visualisation.cut).sum() 
        else:
            if interest==0:
                self.maxInterest=(self.widgetCam.visualisation.data).max()
            if interest==1:
                self.maxInterest=(self.widgetCam.visualisation.data).sum()
                
        
        self.maxValueBox.setText('%.3e' % self.maxInterest)
        # print(self.widgetCam.data)
        return(self.maxInterest)
    
    
    def evalOneMax(self,individual):
        
        if self.stopAlgo==False:
            
            self.winDM.setDMvalueonTable(individual)
            a=self.winDM.setDMvalue()
            print(a)
            #set value for deformable mirror
            #print('change DM value')
            
            self.wait(0.2)
            
            MAX=[]
            
            for i in range(0,self.widgetCam.nbShot): # take nbShot picture take the mmax and return the mean of nbShot max
                self.widgetCam.acquireOneImage()
                #take a picture
                sh=self.widgetCam.CAM.camParameter["exposureTime"]/1000 # exposure time in second
                self.wait(sh+0.2)
                self.maxInterest=self.newData()
                MAX.append(self.maxInterest)
                
            self.eval=np.mean(MAX)+random.randint(-200,200)
            print('evaluation value',self.eval)
            return (self.eval),
    
    
    def setPopValue(self):
        
        self.popValue=self.popValueBox.value()
        # print('nombre d individu:',self.popValue)
        self.iniDone=False # if nb of individu change we need to do a new init
        
    def setGeneValue(self):
        
        self.geneValueMax=self.geneValueBox.value()
        print('nombre max de generation:',self.geneValueMax)
    
    
    def iniPop(self):
        try :
            self.widgetCam.stopAcq()
        except :
            pass
        
        self.gmax=0
        #inititiate population with self.popValue individu
        g=0
        print('initiate population of ',self.popValue, 'individus each individu have', self.nbIndParameters,'parameters')
       # Structure initializers

        self.pop = self.toolbox.population(n=self.popValue)
        print('initial population : ',self.pop)
        
       # Evaluation de la population initiale : 
        self.fitnesses = list(map(self.toolbox.evaluate, self.pop))
        self.fitnessesTot['0']=self.fitnesses
        self.fitnessesTot['generation'+str(g)]=[]
        for ind, fit in zip(self.pop, self.fitnesses):

            ind.fitness.values = fit
            self.fitnessesTot['generation'+str(g)].append(fit)
        print("  Evaluated initial population :  %i individuals" % len(self.pop))
        
        
        
        pop=list(self.pop)
        
        self.populationTotale['generation'+str(g)]=pop
      
        
        
        
        
        self.wait(0.1)
        
        self.winResult.initTab()
        
        self.iniDone=True
        
        
        
        
    def startAlgo(self):
        try :
            self.widgetCam.stopAcq()
        except :
            pass
        print('start algo ....')
        g=0
       
        
        if self.iniDone==False:
            print('init must be done')
            
        
        self.stopAlgo=False
        #
        
        # Extracting all the fitnesses of initial population
        
        fits = [ind.fitness.values[0] for ind in self.pop]
        # print('value find',fits)
        
        
        # Variable keeping track of the number of generations
        
        
        # Begin the evolution
        while max(fits) < 500 and g < self.geneValueMax and self.stopAlgo==False:
            g+=1
            if self.stopAlgo==True:
                break
            # condition de convergence et nobre max de generation
            
            
            # A new generation
           
            print("-- Generation %i --" % g)
            
            # Select the next generation individuals
            offspring = self.toolbox.select(self.pop, len(self.pop))
            # Clone the selected individuals
            offspring = list(map(self.toolbox.clone, offspring))
            #print(offspring)
        
            # Apply crossover (mating) and mutation on the offspring
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
    
                # cross two individuals with probability CXPB
                if random.random() < self.CXPB:
                    self.toolbox.mate(child1, child2)
    
                    # fitness values of the children
                    # must be recalculated later
                    #The del statement will invalidate the fitness of the modified offspring.
                    del child1.fitness.values
                    del child2.fitness.values
    
            for mutant in offspring:
    
                # mutate an individual with probability MUTPB
                if random.random() < self.MUTPB:
                    self.toolbox.mutate(mutant)
                    del mutant.fitness.values   # set invalid to  fitness value
                    
               
        #The crossover (or mating) and mutation operators, provided within DEAP, 
        #usually take respectively 2 or 1 individual(s) as input and return 2 or 1 modified individual(s). 
        #In addition they modify those individuals within the toolbox container and we do not need to reassign their results.
        #Since the content of some of our offspring changed during the last step, 
        #we now need to re-evaluate their fitnesses. 
        #To save time and resources, we just map those offspring which fitnesses were marked invalid.     
            
            # Evaluate the individuals with an invalid fitness
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            self.fitnesses = map(self.toolbox.evaluate, invalid_ind)
            self.fitnessesTot['generation'+str(g)]=[]
            for ind, fit in zip(invalid_ind, self.fitnesses):
                if self.stopAlgo==True:
                    break
                else :
                    ind.fitness.values = fit
                    self.fitnessesTot['generation'+str(g)].append(fit)
            
        #
        # we replace the old population by the offspring.
        
            self.pop[:] = offspring
            fits = [ind.fitness.values[0] for ind in self.pop]

            
            
            print('population generation',g,list(self.pop))
            
            self.populationTotale['generation'+str(g)]=list(self.pop)
            
            print('list value for generation',g)
            print(self.fitnessesTot['generation'+str(g)])
            self.gmax=g # generation max reached
            
                        
           
         
       
        # print(self.fitnessesTot)
        print("-- End of (successful) evolution --")
        
        best_ind = tools.selBest(self.pop, 1)[0]
        # print("Best individual is %s, %s" % (best_ind, best_ind.fitness.values))
        # print(self.populationTotale)
        
        # set DM with the best value
        # take an image 
        # 
        self.evalOneMax(best_ind)
        self.winResult.initTab() # init result windows
        
        self.wait(0.1)
        
        # print('population toutes les generations :')
        #print(self.populationTotale)
        
        
        
        
        
        
        
    def stopAlgo(self):
        self.stopAlgo=True
        #stop DM mvt
        self.widgetCam.stopAcq()
        
            
    def wait(self,seconds):
        time_end=time.time()+seconds
        while time.time()<time_end:
            QtGui.QApplication.processEvents()            
            
    def open_widget(self,fene):
        """ ouverture widget suplementaire 
        """
        
        if fene.isWinOpen==False:
            
            fene.isWinOpen=True
            #A=self.geometry()
            #fene.setGeometry(A.left()+A.width(),A.top(),500,A.height())
            fene.show()
        else:
            fene.activateWindow()
            fene.raise_()
            fene.showNormal()
            # pass
        
    def closeEvent(self,event):
        ''' closing window event (cross button)
        '''
        if self.widgetCam.isConnected==True:
             self.widgetCam.stopAcq()
             time.sleep(0.1)
             self.widgetCam.close()
             
        # close DM connexion    
             
             
             
if __name__=='__main__':
    
    app=QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    algo=ALGO(cam='cam1') 
    
    algo.show()
    sys.exit(app.exec_() )