print("\033c\033[40;37m\n")
import copy

def creates(x:int,y:int):
    lx=[]
    ly=[]
    lx=" "*x+"\n"
    for yy in range(y):
        ly.append(copy.copy(lx))
    return ly

def change(ly:list,y:int,s:str):
    lyy=[]
    counter=0
    for ll in ly:
        lll=s
        if counter==y:
            lis=len(ll)-1
            if len(ll)>=len(s):
              lll=s[:lis]+"\n"
            else: 
              lis=len(s)
              lll=s+ll[lis:]
            lyy.append(copy.copy(lll))
        else:
            lyy.append(copy.copy(ll))
        counter=counter+1
    return lyy

def report(ly:list):
    for ll in ly:
        print(ll)
ll=creates(10,10)
ll=change(ll,3,"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
report(ll)
        
    
