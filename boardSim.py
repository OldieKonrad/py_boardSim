import numpy as np
import random
import sys
from itertools import product

DOCYCLES = 20

SPAWNCHANCE = 5

EMPTY = 0

PLANT = 1
PLSTARTENERGY = 2
PLENERGYCOST = 1
PLENERGYCHANCE = 50
PLENERGYWIN = 3

PLANTEATER = 2
PESTARTENERGY = 10
PEENERGYCOST = 1
PEMOVECOST = 2
PEENERGYDRAIN = sys.maxsize
PESPLITENERGY = PESTARTENERGY * 2

PREDATOR = 4
PRSTARTENERGY = 50
PRENERGYCOST = 1
PRMOVECOST = 2
PRENERGYDRAIN = sys.maxsize
PRSPLITENERGY = PRSTARTENERGY * 3


# D1Neighbours = ((-1,-1),(0,-1),(+1,-1),
#                 (-1,0),        (+1,0),
#                 (-1,+1),(0,+1),(+1,+1))

# neighbours = tuple((x, y) for (x, y) in product(range(distance*-1, distance+1), repeat=2) if (abs(x)==distance or abs(y)==distance))
distance = 1
d1Neighbours = tuple((x, y) for (x, y) in product(range(distance*-1, distance+1), repeat=2) if (abs(x)==distance or abs(y)==distance))
# distance = 2
# d2Neighbours = tuple((x, y) for (x, y) in product(range(distance*-1, distance+1), repeat=2) if (abs(x)==distance or abs(y)==distance))
# distance = 3
# d3Neighbours = tuple((x, y) for (x, y) in product(range(distance*-1, distance+1), repeat=2) if (abs(x)==distance or abs(y)==distance))

def getNeighbour2D(cx: int, cy: int, width: int, height: int, distance: int)->tuple():
    # generator function which returns the surrounding neighbour coordinates one at a time
    # coord(0, 0) is in the left top
    # 
    if distance==1: neighbours = d1Neighbours
    # if distance==2: neighbours = d2Neighbours
    # if distance==3: neighbours = d3Neighbours
    for nx, ny in neighbours:
        yield ((cx+nx+width)%width, (cy+ny+height)%height)


def uniqId():
    cId = 1
    while True:
        yield cId   # yield f'{cId:08X}'
        cId += 1
idGen = uniqId()

class BoardSim():
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

        self.npboard = np.zeros([height, width], np.int32) # height and width exchanged in numpy
        # print(self.npboard)

        self.eDict = dict()
        self.eDictDead = dict()
        self.deadCount = 0
        self.cycle = 1
        return
    
    def placeEntityIdOnBoard(self, xpos: int, ypos: int, entity) -> None:
        self.npboard[ypos, xpos] = entity.id
        entity.onBoard = self
        entity.setBoardPos(xpos, ypos)
        return
    
    def bIter(self):
        for xpos in range(self.width):
            for ypos in range(self.height):
                yield (xpos, ypos, self.npboard[ypos, xpos])

    def doLiveCycle(self):
        # cycle through all boardCells
        self.cycle += 1
        self.seedPlant()                    # do it again every cycle
        bIter = self.bIter()
        for xpos, ypos, id in bIter:        # get next coord
            if not id: continue             # nothing to do

            cEnt = self.eDict[id]
            if cEnt.changedOnCycle >= self.cycle:   # already done
                continue
            cEnt.changedOnCycle = self.cycle        # prevent double handling
            cEnt.age += 1

            # try to eat
            cEnt.eatMove()
            # subtract living cost
            if cEnt.alive: cEnt.subtractCost(cEnt.livingCost)

        return
    
    def nextFood(self, cx, cy, foodType, maxDistance):
        if maxDistance <= 0: return False            # end of recursion
        neighbours = getNeighbour2D(cx, cy, self.width, self.height, 1)
        for nx, ny in neighbours:
            if self.npboard[ny, nx] == EMPTY: continue
            ent = self.eDict[self.npboard[ny, nx]]
            if  ent.eType == foodType: return True
        for nx, ny in neighbours:
            if self.npboard[ny, nx] == EMPTY:
                if self.nextFood(nx, ny, foodType, maxDistance-1): return True
        return False   
    
    def printBoardToTerminal(self):
        print()     # new line
        for ypos in range(self.height):
            for xpos in range(self.width):
                # print(f'({xpos:02d}/{ypos:02d}) ', end='')
                if not self.npboard[ypos, xpos]:
                    print(f'000 ', end='')
                    continue
                eObj = self.eDict[self.npboard[ypos, xpos]]
                print(f'{eObj.eType:03d} ', end='')
            print() # new line
        return

    def printSimData(self):
        # entitys alive
        # average age entitys alive
        # average energy entitys alive
        eAlive = 0
        plants = 0
        planteaters = 0
        predators = 0
        # sumAgeAlive = 0
        # sumEnergyAlive = 0

        eDead = self.deadCount
        for eObj in self.eDict.values():
            eAlive += 1
            # sumAgeAlive = sumAgeAlive + eObj.age
            # sumEnergyAlive = sumEnergyAlive + eObj.energy
            if eObj.eType == PLANT: plants += 1
            if eObj.eType == PLANTEATER: planteaters += 1
            if eObj.eType == PREDATOR: predators += 1

        print('-'*100)
        print(f'Cycle: {self.cycle:6d} | Alive: {eAlive:6d}| Plants: {plants:6d}| Planteaters: {planteaters:6d}| Predators: {predators:6d} | Dead: {eDead:6d}')

        return

    def seedPlant(self):
        bIter = self.bIter()
        for xpos, ypos, id in bIter:        # get next coord
            if not id:                      # empty coord - will be used for reseed every cycle
                if (random.randint(0, 99) < SPAWNCHANCE):
                    newEnt = Plant(self)
                    self.placeEntityIdOnBoard(xpos, ypos, newEnt)
        return
    
    def seedPlantEater(self):
        spawnchance = SPAWNCHANCE
        bIter = self.bIter()
        for xpos, ypos, id in bIter:        # get next coord
            if not id:                      # empty coord - will be used for reseed every cycle
                if (random.randint(0, 99) < spawnchance):
                    newEnt = PlantEater(self)
                    self.placeEntityIdOnBoard(xpos, ypos, newEnt)
        return
    
    def seedPredator(self):
        spawnchance = SPAWNCHANCE / 2
        bIter = self.bIter()
        for xpos, ypos, id in bIter:        # get next coord
            if not id:                      # empty coord - will be used for reseed every cycle
                if (random.randint(0, 99) < spawnchance):
                    newEnt = Predator(self)
                    self.placeEntityIdOnBoard(xpos, ypos, newEnt)
        return

    def seedBoard(self):
        self.seedPlant()
        self.seedPlantEater()
        self.seedPredator()
        self.printSimData()
        return

####################### END CLASS BoardSim ###################################

class Entity():
    def __init__(self, board: BoardSim) -> None:
        self.id = next(idGen)
        
        self.alive = True
        self.energy = 0
        self.maxEnergyDrain = 0
        self.age = 0
        self.eType = 0      
        self.foodType = 0
        self.moveCost = 0
        self.livingCost = 0
        self.splitEnergy = 0

        board.eDict[self.id] = self
        self.changedOnCycle = board.cycle

        self.onBoard = None # should be set with placing
        self.xpos = -1      #to provoke error
        self.ypos = -1      #to provoke error
        return
    
    def setBoardPos(self, xpos: int, ypos: int) -> None:
        self.xpos = xpos
        self.ypos = ypos
        return
    
    def subtractCost(self, cost: int)->None:
        # subtract cost
        self.energy = self.energy - cost
        # if energy <= 0 => dead
        if self.energy <= 0:
            self.alive = False
            self.onBoard.deadCount += 1                         # another one bites the dust...
            # forget the dead self.onBoard.eDictDead[self.id]=self               # store it in dead dict for statistics

            self.onBoard.npboard[self.ypos, self.xpos] = 0     # set board as empty
            del self.onBoard.eDict[self.id]
            self.onBoard = None
            self.xpos = -1                              # set to invalid
            self.ypos = -1                              # set to invalid
        return 

    def eatMove(self):

        if self.eType == PLANT:
            # give chance of energywin
            if (random.randint(0, 99) < PLENERGYCHANCE):
                self.energy = self.energy + PLENERGYWIN
            # no move for plants
            return      # shouldnt be here
        # eat

        neighbourIter = getNeighbour2D(self.xpos, self.ypos, self.onBoard.width, self.onBoard.height, 1)
        neighbours = list(neighbourIter)
        emptyNeighbourCoords = [(xn, yn) for xn, yn in neighbours if not self.onBoard.npboard[yn, xn]]

        if emptyNeighbourCoords:            # decide where to split or move if room = random empty neighbour
            xnew, ynew = emptyNeighbourCoords[random.randint(0, len(emptyNeighbourCoords)-1)]

        # SPLIT if possible energy and room
        if (self.energy >= self.splitEnergy) and emptyNeighbourCoords:
            if self.eType == PLANTEATER: newEnt = PlantEater(self.onBoard)
            if self.eType == PREDATOR:   newEnt = Predator(self.onBoard)           
            self.onBoard.placeEntityIdOnBoard(xnew, ynew, newEnt)
            self.energy -= newEnt.energy
            return

        # EAT if food around
        maxFoodEnt = None
        for xn, yn in neighbours:
            nId = self.onBoard.npboard[yn, xn]
            if not nId: continue                    # empty neighbour
            nEnt = self.onBoard.eDict[nId]
            if not (nEnt.eType == self.foodType): continue  # wrong neighbour
            if not maxFoodEnt:
                maxFoodEnt = nEnt
                continue
            if maxFoodEnt.energy < nEnt.energy:
                maxFoodEnt = nEnt
        if maxFoodEnt:                              # food found - drain it
            self.energy += min(maxFoodEnt.energy, self.maxEnergyDrain)
            maxFoodEnt.subtractCost(self.maxEnergyDrain)
            return                                  # well fed

        if not emptyNeighbourCoords: return                 # no room to move - just wait...
        # MOVE
        for nx, ny in emptyNeighbourCoords:
            if not self.onBoard.nextFood(nx, ny, self.foodType, 1):
                return                                      # no food around - just wait...

            self.onBoard.npboard[self.ypos, self.xpos] = 0      # remove from current position
            self.onBoard.placeEntityIdOnBoard(nx, ny, self) # move to new position
            self.subtractCost(self.moveCost)                    # consider movement cost...
            return                                              # done - hopefully

        return

class Plant(Entity):
    def __init__(self, board: BoardSim) -> None:
        super().__init__(board)
        self.eType = PLANT
        self.energy = PLSTARTENERGY
        self.livingCost = PLENERGYCOST
        return
    
class PlantEater(Entity):
    def __init__(self, board: BoardSim) -> None:
        super().__init__(board)
        self.eType = PLANTEATER
        self.foodType = PLANT
        self.energy = PESTARTENERGY
        self.maxEnergyDrain = PEENERGYDRAIN
        self.splitEnergy = PESPLITENERGY
        self.livingCost = PEENERGYCOST
        self.moveCost = PEMOVECOST
        return
    
class Predator(Entity):
    def __init__(self, board: BoardSim) -> None:
        super().__init__(board)
        self.eType = PREDATOR
        self.foodType = PLANTEATER
        self.energy = PRSTARTENERGY
        self.maxEnergyDrain = PRENERGYDRAIN
        self.splitEnergy = PRSPLITENERGY
        self.livingCost = PRENERGYCOST
        self.moveCost = PRMOVECOST
        return

#############################################################################
def testBoardSim(width: int, height: int) -> None:
    bSim = BoardSim(width, height)
    bSim.seedBoard()
    
    for i in range(DOCYCLES):
        bSim.doLiveCycle()
        bSim.printBoardToTerminal()
        bSim.printSimData()


    return

if __name__ == "__main__":
    testBoardSim(width=10, height=10)