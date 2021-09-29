from random import shuffle, randint
from tkinter import Tk,Label,Frame,Canvas
from tkinter.font import Font

import threading,time

pieceActivated=[None,None]
threads=[]

class GradientFrame(Canvas):
    '''A gradient frame which uses a canvas to draw the background'''
    def __init__(self, parent, color1="red", color2="black", **kwargs):
        Canvas.__init__(self, parent, **kwargs)
        self._color1 = color1
        self._color2 = color2
        self.bind("<Configure>", self._draw_gradient)

    def _draw_gradient(self, event=None):
        '''Draw the gradient'''
        self.delete("gradient")
        width = self.winfo_width()
        height = self.winfo_height()
        limit = width
        (r1,g1,b1) = self.winfo_rgb(self._color1)
        (r2,g2,b2) = self.winfo_rgb(self._color2)
        r_ratio = float(r2-r1) / limit
        g_ratio = float(g2-g1) / limit
        b_ratio = float(b2-b1) / limit

        for i in range(limit):
            nr = int(r1 + (r_ratio * i))
            ng = int(g1 + (g_ratio * i))
            nb = int(b1 + (b_ratio * i))
            color = "#%4.4x%4.4x%4.4x" % (nr,ng,nb)
            self.create_line(i,0,i,height, tags=("gradient",), fill=color)
        self.lower("gradient")

class Piece():
    def __init__(self,color,num,id,wildcard=False):
        self.color=color
        self.num=num
        self.id=id
        self.selected=False

        self.tkPiece=None

        if wildcard:
            self.wildCard=True
        else:
            self.wildCard=False
        
    def __repr__(self):
        return f"<Piece {self.id} {self.getCardCode()}>\n"
    
    def getCardCode(self):
        if self.wildCard:
            return f"X:00"

        num="0" if self.num > 9 else ""
        num=f"{num}{self.num}"

        return f"{self.color}:{self.num}"

    def getCardUniqueID(self):
        return self.id

    def defineTkPiece(self,x):
        self.tkPiece=x

    def possibleAdjacentPieces(self):
        l=[]
        x=self.getCardCode()
        
        i=int(x[2:4])+1
        if i != 14:
            l.append(f"{x[0]}:{i if i > 9 else f'0{i}'}")

        i=int(x[2:4])-1
        if i != 0:
            l.append(f"{x[0]}:{i if i > 9 else f'0{i}'}")

        colors=["B","R","P","O"]
        colors.remove(self.color)

        for color in colors:
            i=int(x[2:4])
            l.append(f"{color}:{i if i > 9 else f'0{i}'}")

        return l
        
class Player():
    def __init__(self,name=""):
        self.hand=[]
        self.name=name

    def draw(self,cards):
        for card in cards:
            self.hand.append(card)

class Game():
    def __init__(self,players=[]):
        self.drawPile=self.getStartingDeck()
        shuffle(self.drawPile)

        self.players=players

        for player in players:
            player.draw(self.drawHand())

        # format:
        # [
        #     [ int representing set one or set 2, (row, column), piece object ]
        #     [ int representing set one or set 2, (row, column), piece object ]
        #     etc
        # ]
        
        self.cardsOnBoard=[]
        self.hilightedSquares=[]

        self.initializeTk()

        self.gameScreen()

        self.root.mainloop()

    def initializeTk(self):
        self.root=Tk()

        self.fontPrimary="Lexend"
        self.fontSecondary="Roboto"

        self.titleFont=Font(
            family=self.fontPrimary,
            size="36",
            weight="bold"
        )

        self.headerFont=Font(
            family=self.fontSecondary,
            size="24",
        )

        self.captionFont=Font(
            family=self.fontPrimary,
            size="20",
            weight="bold"
        )

        self.bodyFont=Font(
            family=self.fontPrimary,
            size="12"
        )

        self.colors = {
            "dark":"#111111",
            "light":"#fdfdfd",

            "danger":"#EA5D5C",
            "warning":"#ffc107",
            "success":"#4dbd74",

            "primary": {
                "light": "#384461",
                "accent": "#2F3951",
                "normal": "#252D40",
                "dark": "#131720"
            },

            "secondary": {
                "light": "#FEC87C",
                "accent": "#FDBD63",
                "normal": "#FDB34B",
                "dark": "#FC9D17"
            },

            "accent1": {
                "light": "#83D7BB",
                "accent": "#70D1B1",
                "normal": "#5DCBA6",
                "dark": "#3BB98F"
            },

            "accent2": {
                "light": "#EF8476",
                "accent": "#EC7060",
                "normal": "#E95A47",
                "dark": "#E4331B"
            },

            "gray": {
                "100":"#cfcfd7",
                "200":"#c2cfd6",
                "300":"#c1c1cf",
                "400":"#9f9fab",
            }
        }

        self.bgcolor=self.colors["light"]

        self.root.title("Rummikub")
        self.w=self.root.winfo_screenwidth()
        self.h=self.root.winfo_screenheight()
        self.root.geometry(f"{self.w}x{self.h}")
        self.root.minsize(self.w,self.h)
        self.root.state("zoomed")

        #self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.root.configure(bg=self.bgcolor)
        #self.root.attributes("-alpha",0.9)

    def gameScreen(self):
        title=self.createTitle()
        
        board=Frame(self.root,bg=self.bgcolor)
        board.grid(row=1,column=0)
        board.grid_propagate(1)

        deck=Frame(board,bg=self.bgcolor)
        deck.grid(row=0,column=0,pady=10,columnspan=2)
        deck.columnconfigure(15, weight=1)

        self.set1=Frame(board,bg=self.bgcolor)
        self.set1.grid(row=1, column=0, pady=10,padx=10,sticky="W")

        self.set2=Frame(board,bg=self.bgcolor)
        self.set2.grid(row=1, column=1, pady=10,padx=10,sticky="E")

        # create board spaces

        for i in range(13):
            l=self.createPiecePlaceholder(deck)
            l.grid(row=1,column=i,padx=2)

        for y in range(8):
            for x in range(13):
                l=self.createPiecePlaceholder(self.set1)
                l.grid(row=y,column=x,padx=2)

        for y in range(8):
            for x in range(13):
                l=self.createPiecePlaceholder(self.set2)
                l.grid(row=y,column=x,padx=2)
        
        i=0
        for piece in self.players[0].hand:
            l=self.createPiece(deck,piece)
            piece.defineTkPiece(l)
            l.grid(row=1,column=i,padx=2)
            i+=1

            if i==1:
                l=self.createPiece(self.set1,piece)
                l.grid(row=7,column=12)

    def createTitle(self):
        title=Label(self.root,text="Rummikub", font=self.titleFont,fg=self.colors["primary"]["normal"],bg=self.bgcolor)
        title.grid(row=0,column=0)
        return title

    def createPieceMoveArea(self,root,left=True):
        c1=self.colors["gray"]["100"]
        c2=self.colors["gray"]["100"]
        
        if left:
            c1,c2 = c2,c1
            
        label=GradientFrame(
            root,
            c1,
            c2,
            width=62,
            height=94,
            bd=0,
            bg=self.bgcolor,
        )
    
        return label
       

    def createPiecePlaceholder(self,root):
        label=Label(
            root,
            font=self.captionFont,
            text="",
            bg=self.bgcolor,
            width=3,
            height=2,
            bd=5,
            #relief="groove",
        )

        return label

    def createPiece(self,root,piece):

        def labelHilight(e,piece):

            def movePiece(e,piece,self,pos):
                global pieceActivated

                for square in self.hilightedSquares:
                    square.destroy()
                
                piece[0].destroy()
                parent=self.set1
                if pos[0]==1:
                    parent=self.set2
                l=self.createPiece(parent,piece[1])
                
                l.grid(row=pos[1][0],column=pos[1][1])

                self.cardsOnBoard.append([pos[0],pos[1],piece[1]])

                pieceActivated=[None,None]


                # [ int representing set one or set 2, (row, column), piece object ]
            
            global pieceActivated
            
            if pieceActivated[0] is not None:
                for square in self.hilightedSquares:
                    square.destroy()
                pieceActivated[0].config(bg=self.colors["gray"]["100"])
                pieceActivated[1].selected=False
                
            e.widget.config(bg=self.colors["gray"]["300"])
            piece.selected=True

            pieceActivated=[e.widget,piece]

            pieceCode=piece.getCardCode()
            pieceNum=int(pieceCode[2:4])
            pieceCol=pieceCode[0]

            possibleSquares=[]

            itera=0

            # [ int representing set one or set 2, (row, column), piece object ]    
            
            filledSquares=[]
            for item in self.cardsOnBoard:
                filledSquares.append([item[0], item[1]])

            set1=[]
            set2=[]

            for item in self.cardsOnBoard:
                if item[0] == 0:
                    set1.append(item[1])
                elif item[0] == 1:
                    set2.append(item[1])

            s1Exhausted=False
            
            while possibleSquares==[]:
                if not s1Exhausted:
                    if itera > 7:
                        s1Exhausted=True
                        itera=0
                        
                    if (itera,pieceNum-1) not in set1:
                        possibleSquares.append([0,(itera,pieceNum-1)])
                        break
                    
                else:
                    if itera >  7:
                        break
                    
                    if (itera,pieceNum-1) not in set2:
                        possibleSquares.append([1,(itera,pieceNum-1)])
                        break

                itera+=1
                        

            for item in possibleSquares:
                parent=self.set1
                if item[0]==1:
                    parent=self.set2
                    
                l=self.createPieceMoveArea(parent)
                l.grid(row=item[1][0],column=item[1][1])

                l.bind("<Button-1>",lambda event, piece=pieceActivated,self=self,pos=item: movePiece(event,piece,self,pos))

                self.hilightedSquares.append(l)
            
            

        def onHover(e):
            if pieceActivated[0]==e.widget:
                return
            e.widget.config(bg=self.colors["gray"]["200"])

        def onHoverExit(e):
            if pieceActivated[0]==e.widget:
                return
            e.widget.config(bg=self.colors["gray"]["100"])

        def jokerRotate(j):
            colors=[self.colors["primary"]["light"],self.colors["accent2"]["dark"],self.colors["accent1"]["dark"],self.colors["secondary"]["dark"]]
            i=0
            while True:
                i=randint(0,3)
                j.config(fg=colors[i])
                time.sleep(0.1)

        joker=False
       
        if piece.color=="B":
            pieceColor=self.colors["primary"]["light"]
        elif piece.color=="R":
             pieceColor=self.colors["accent2"]["dark"]
        elif piece.color=="P":
             pieceColor=self.colors["accent1"]["dark"]
        elif piece.color=="O":
            pieceColor=self.colors["secondary"]["dark"]
        else:
            pieceColor=self.colors["gray"]["400"]
            joker=True
            
        label=Label(
            root,
            font=self.captionFont,
            text=piece.num if piece.num != None else "☺",
            bg=self.colors["gray"]["100"],
            cursor="plus",
            width=3,
            height=2,
            relief="groove",
            bd=5,
            fg=pieceColor,
        )

        label.bind("<Button-1>",lambda event, piece=piece: labelHilight(event,piece))

        label.bind("<Enter>", onHover)
        label.bind("<Leave>", onHoverExit)

        if joker:
            t = threading.Thread(target=jokerRotate, args=[label])
            threads.append(t)
            t.start()

        return label
        

    def drawHand(self):
        hand=[]
        for i in range(14):
            x=randint(0,len(self.drawPile)-1)
            hand.append(self.drawPile[x])
            self.drawPile.pop(x)
        return hand

    def getStartingDeck(self):
        colors=["B","R","P","O"]
        deck=[]
        colorInt=0
        step=1
        id_=0

        for i in range(2):
            color=colors[colorInt]

            for i in range(52):
                deck.append(Piece(color,step,id_))
                step+=1
                id_+=1

                if i==51:
                    continue

                if step>13:
                    colorInt+=1
                    step=1
                    color=colors[colorInt]
                    
            colorInt=0
            step=1

        deck.append(Piece(None,None,id_,wildcard=True))
        deck.append(Piece(None,None,id_+1,wildcard=True))
        
        return deck  



player1=Player()
player2=Player()

game=Game(players=[player1,player2])
