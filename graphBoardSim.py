import pygame
import math

import boardSim

def main():

    pygame.init()
    pygame.display.set_caption("Board Simulation")

    #board size
    BWIDTH, BHEIGHT = 80, 80

    #screen size
    SWIDTH, SHEIGHT = 800, 800
    FPS = 30
    #tile size
    twidth = SWIDTH / BWIDTH
    theight = SHEIGHT / BHEIGHT

    circrad = math.sqrt((twidth/2)**2 + (theight/2)*2)

    screen = pygame.display.set_mode((SWIDTH, SHEIGHT))




    board = boardSim.BoardSim(BWIDTH, BHEIGHT)
    board.seedBoard()         # setup all entitys

    clock = pygame.time.Clock()

    run = True
    while run:
        clock.tick(FPS)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break
        
        screen.fill("white")         # fill background

        bIter = board.bIter()
        for posx, posy, id in bIter:
            if id:
                energy = board.eDict[id].energy

                if board.eDict[id].eType == boardSim.PLANT:         # greenish for plants
                    rcolor = pygame.Color(min(128, 32+energy), min(255, 64+(energy*energy)), min(128, 32+energy))
                if board.eDict[id].eType == boardSim.PLANTEATER:    # blueish for planteaters
                    rcolor = pygame.Color('blue')
                    # rcolor = pygame.Color(min(128, 32+energy), min(128, 32+energy), min(255, 64+(energy*energy)))
                if board.eDict[id].eType == boardSim.PREDATOR:      # redish for predators
                    rcolor = pygame.Color('red')
                    # rcolor = pygame.Color(min(255, 64+(energy*energy)), min(128, 32+energy), min(128, 32+energy))

                # pygame.draw.rect(screen, rcolor, pygame.Rect(posx*twidth+1, posy*theight+1, twidth-2, theight-2))
                pygame.draw.circle(screen, rcolor, (posx*twidth+twidth/2, posy*theight+theight/2), circrad)

        pygame.display.flip()
            
        board.doLiveCycle()     # next generation...
        if board.cycle%10 == 0 : board.printSimData()
    pygame.quit()
    quit()

if __name__ == "__main__":
    main()