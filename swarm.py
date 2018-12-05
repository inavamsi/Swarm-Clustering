import random
import copy
import csv
import math
import time


class Bird():
  def __init__(self, name,dump, boardsize):
    self.dir=(random.random(),random.random())
    self.speed = random.random()
    self.x = random.randint(0,boardsize)
    self.y = random.randint(0,boardsize)
    self.name = name
    self.list_val=dump #list of attributes, in case of stock a list(close,volume,volatility) in same order as time
    self.history=[]

def dist(x1,y1,x2,y2,boardsize):

  xs1=(x1-x2)*(x1-x2)
  ys1=(y1-y2)*(y1-y2)

  xs2=(boardsize-abs(x1-x2))*(boardsize-abs(x1-x2))
  ys2=(boardsize-abs(y1-y2))*(boardsize-abs(y1-y2))

  xs=min(xs1,xs2)
  ys=min(ys1,ys2)

  dist=math.sqrt(xs+ys)
  return dist

def bdist(b1,b2, boardsize):
  x1=b1.x
  y1=b1.y
  x2=b2.x
  y2=b2.y
  return dist(x1,y1,x2,y2, boardsize)

def randomly(arr):
  if(arr==[]):
    return None                                    
  n=len(arr)
  r=random.random()
  for i in range(0,n):
    if(r<(i+1)/n):
      return arr[i]
  return arr[n-1]

#move in direction
def move_vector(x,y,direction,speed):
  (u,v)=direction
  r = random.random()
  directions=[(1,0),(0,1),(-1,0),(0,-1)]
  d=randomly(directions)
  if r<u/(u+v):
    d=(u/(abs(u)),0)
  else:
    d=(0,v/(abs(v)))

  s=random.random()
  if(s<speed):
    return d
  else:
    return (0,0)

# if we cant move to vector sum of attrection and alignment then we just move closer to the flock as much as permitted
def adjacent_move_vec(x,y,a,b, boardsize):
  directions=[(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)]
  adjl=[]
  adje=[]
  stdd=dist(x,y,a,b, boardsize)
  for d in directions:
    (u,v)=d
    if dist(x+u,y+v,a,b, boardsize)<stdd:
      adjl.append(d)
  if dist(x+u,y+v,a,b, boardsize)==stdd:
      adje.append(d)

  if(adjl!=[]):
    return randomly(adjl)
  if(adje!=[]):
    return randomly(adje)

  return (0,0)

def initialise_birdpos(l,board):
  n=len(board)
  for b in l:
    b.x=random.randint(0,n-1)
    b.y=random.randint(0,n-1)
    while(board[b.x][b.y]!=None):
      b.x=random.randint(0,n-1)
      b.y=random.randint(0,n-1)
    board[b.x][b.y]=b
    b.history.append((b.x,b.y))

  return (l,board)

def centroid(lob):
  cx=0
  cy=0
  for b in lob:
    cx+=b.x
    cy+=b.y

  cx/=len(lob)
  cy/=len(lob)

  return(cx,cy)

#speed of attraction will be proportioanl to dist to centroid and inverse to size of cluster.
def set_speed(b,lofbirds,thresh,mindist,maxdist, boardsize,time):
  similar_birds=findneighbours(b, lofbirds, thresh, mindist, maxdist,boardsize,time)
  if(similar_birds==[]):
    b.speed=random.random()
    return b

  (cx,cy)=centroid(similar_birds)
  d2cntrd=dist(b.x,b.y,cx,cy, boardsize)

  if d2cntrd < 3.5:
    b.speed=0.5
  else:
    b.speed=0.5 + d2cntrd/boardsize

  return b

def mean_dir(lob):
  dx=0
  dy=0
  for b in lob:
    dx,dy=b.dir

  dx/=len(lob)
  dy/=len(lob)
  return (dx,dy)

def signed_vec(sc,tc, boardsize):  #sign of vector from sourcecord to target cord
  disp=abs(sc-tc)
  minv=min(disp,boardsize-disp)
  if(minv==0):
    sign=1 
  else:
    sign=minv/abs(minv)
  return sign*minv

def attvec(bx,by,cx,cy, boardsize):
  svx=signed_vec(bx,cx, boardsize)
  svy=signed_vec(by,cy, boardsize)
  return(svx,svy)

# weighted vector sum of alignment vector and attraction vector
def set_dir(b,lofbirds,thresh,mindist,maxdist,attw,aligw, boardsize,time):
  similar_birds=findneighbours(b, lofbirds, thresh, mindist, maxdist,boardsize,time)
  directions=[(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)]
  if(similar_birds==[]):
    b.speed=random.random()
    return b

  (alx,aly)=mean_dir(similar_birds)
  (cx,cy)=centroid(similar_birds)
  (atx,aty)=attvec(b.x,b.y,cx,cy, boardsize)

  dx=attw*atx+aligw*alx
  dy=attw*aty+aligw*aly
  b.dir=(dx,dy)

  return b


def similar_val(b1,b2,time): #2 objects and time starting at 1
  #normalise similarity between 0 and 1, 1 being equal
  time=time+1
  if(b1.list_val['close'][time-1]==0 or b2.list_val['close'][time-1]==0):
    return 0
  b1cv=(float)(b1.list_val['close'][time])-(float)(b1.list_val['close'][time-1])
  b2cv=(float)(b2.list_val['close'][time])-(float)(b2.list_val['close'][time-1])
  b1cv/=(float)(b1.list_val['close'][time-1])
  b2cv/=(float)(b2.list_val['close'][time-1])

  if(b1cv==0 or b2cv==0):
    return 0
  return min(b1cv/b2cv,b2cv/b1cv)

def findneighbours(b, l, t, mindist, maxdist, boardsize,time): # objec b and sample space l is a list of objects, t is threshold of being same species mindist os personal space marker, maxdist is distance of consideration

  '''
  min_no=2
  most_similar=None
  if(l[0].x!=b.x or l[0].y!=b.y):
    most_similar=copy.deepcopy(l[0])
  else:
    most_similar=copy.deepcopy(l[1])
  scores=[]
  '''

  similar=[]
  for i in l:
    if(bdist(i,b, boardsize)<=maxdist and bdist(i,b, boardsize)>= mindist and similar_val(i,b, time)>=t):
      btemp=copy.deepcopy(i)
      similar.append(btemp)

  return similar

def find_in_personal_space(b,l,mindist, maxdist,time, boardsize):
  inper=[]
  for i in l:
    if(dist(i,b, boardsize)<mindist and similar_val(i,b, time)>=t):
      btemp=copy.deepcopy(l[i])
      inper.append(btemp)

  return inper



def one_move(attributes):
  board=attributes['board']
  newb=copy.deepcopy(board)
  lobirds=attributes['lob']
  attw=attributes['attw']
  aligw=attributes['aligw']
  thresh=attributes['threshold']
  mindist=attributes['mindist']
  maxdist=attributes['maxdist']
  time=attributes['time']
  boardsize=attributes['boardsize']
  lofbirds=attributes['lob']
  
  def move(b,boardsize):
    (p,q)=move_vector(b.x,b.y,b.dir,b.speed)
    if p==0 and q==0:
      (p,q)=move_vector(b.x,b.y,b.dir,b.speed)
    else:
      u=b.x+b.dir[0] 
      u= u%boardsize
      v=b.y+b.dir[1]
      v=v%boardsize
      (p,q)=adjacent_move_vec(b.x,b.y,u,v,boardsize)
    return (p,q)
  
  newlob=[]
  for b in lofbirds:
    b=set_dir(b,lofbirds,thresh,mindist,maxdist,attw,aligw, boardsize,time)
    b=set_speed(b,lofbirds,thresh,mindist,maxdist, boardsize,time)
    
    (p,q)=move(b,boardsize)
    px=(int)(b.x+p)% boardsize                #special (int)
    py=(int)(b.y+q)% boardsize

    if(board[px][py]!=None or newb[px][py]!=None ):
      (p,q)=move(b,boardsize)

    px=(int)(b.x+p)% boardsize
    py=(int)(b.y+q)% boardsize
    
    if(board[px][py]==None and newb[px][py]==None):
      board[b.x][b.y]=None
      newb[px][py]=b
      b.x=px
      b.y=py
    newlob.append(b)
      
  for b in newlob:
    attributes['board'][b.x][b.y]=b
  attributes['time']+=1
  attributes['lob']=newlob
  return attributes

def readBirds():
  bdict={}
  with open('merged_data_backup.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    prev="AAPL"
    open1=[]
    close=[]
    low=[]
    high=[]
    volume=[]
    dataMap=[]
    temp=[]
    for data in csv_reader:
        if data[3].endswith("2014") or data[3].endswith("2015") or data[3].endswith("2016") or data[3].endswith("2017"):
            if prev==data[1]:
                open1.append(data[6])
                volume.append(data[7])
                high.append(data[4])
                low.append(data[5])
                close.append(data[2])
            
            else:
                temp={}
                temp['name']=prev
                temp['open']=open1
                temp['volume']=volume
                temp['high']=high
                temp['low']=low
                temp['close']=close
                #print(temp)
                dataMap.append(temp)
                bdict[prev]=temp
                #print(dataMap)
                open1=[]
                volume=[]
                high=[]
                low=[]
                close=[]
                temp=[]
                prev=data[1]
                open1.append(data[6])
                volume.append(data[7])
                high.append(data[4])
                low.append(data[5])
                close.append(data[2])
      
  #print("******************")
  return bdict

def init_game(n, bs):
  attributes={
      'attw':0.5,    #attraction vector weight
      'aligw':0.5,  #alignment vector weight
      'mindist':1,   # separation :min distance between birds
      'maxdist':bs/3,  #maximum distance in sight of bird
      'threshold':0.1,    # threshold for similarity, between 0 and 1
      'time':0,
      'time limit':n,
      'lob':[],   # list of birds'
      
      'board':[],
      'boardsize':bs,
      'directions':[(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)]
  }
 
  directions=attributes['directions']
  
  boardsize=attributes['boardsize']
 
  for j in range(0,boardsize):
    temp=[]
    for i in range(0,boardsize):
      temp.append(None)
    attributes['board'].append(temp)

  #intialise birds and values   
  #read dict bdict name: [close values between 2013-2017]
  bdict=readBirds()
  
  for bname in bdict:
    attributes['lob'].append(Bird(bname,bdict[bname],boardsize))


  (attributes['lob'],attributes['board'])=initialise_birdpos(attributes['lob'],attributes['board'])
  
  return attributes

def simulate(n):
  boardsize=20
  attributes=init_game(n, boardsize)
  for b in attributes['lob']:
    print(b.name,"       ",b.x," , ",b.y)

  print("****")
  print(" ")
  for i in range(0,n):
    attributes=one_move(attributes)
    printboard(boardsize,attributes)

def printboard(boardsize,attributes):
  for i in range(0,boardsize):
    for j in range(0,boardsize):
      bo=attributes['board']
      if(bo[i][j]==None):
        print(" ",end=" ")
      else:
        name=(bo[i][j].name)
        if len(name)<1:
          print("I",end=" ")
        else:
          print(name[0],end=" ")
    print("")
  print("******************")
  time.sleep(0.3)


simulate(100)
