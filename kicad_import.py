import sys


"""

1 centimeter = 393.700787 mils
1 mils = 0.00254 centimeters

"""

#####################################################################

try:
    import maya.cmds as cmds
except:
    print '##---->## hey bro, no Maya!'
    sys.exit()


#####################################################################


def buildcurvefrompoints(FBT, periodic, degree, name):
    out    = ''
    points = ''
    knots  = ''
    buffervar = ''
    a = 0
    size = len(FBT)
    while a < size:
      if a == 0:
        points =  '('+str(FBT[a])+','+str(FBT[a+1])+','+str(FBT[a+2])+')';
      if a > 0 :
        points =  points + ',('+str(FBT[a])+','+str(FBT[a+1])+','+str(FBT[a+2])+')';
      a=a+3
     #points =  ('('+str(FBT[a])+','+str(FBT[a+1])+','+str(FBT[a+2]+')') );
     #buffervar = buffervar + str(points)+','
    numFBT_verts = len(FBT)/3
    #debug
    if numFBT_verts%3!=0:
       print ("buildCurveFromPoints DATA IS NOT DIVISIBLE BY THREE\n")
    #debug

    #command = 'cmds.curve( d='+str(degree)+','
    command = 'd='+str(degree)+','
    if periodic ==1:
      command = command + ' per=True,'
    #[
    command = command +' p=['+ points +']'
   
    numknots = ((numFBT_verts+degree)-1)
    command = command + ',k=['
   
    numberofknots = int(numknots)
    #print 'numb gnuts = '
    #print numberofknots
   
    for a in range(numknots):
        knots =  ("0," )
        if a < (numberofknots-1):
          knots =  ("0," )
        if a == (numberofknots-1):
          knots =  ("0" )
        command = command + knots
    #command = command + '])'
    #curvename = 'KURVE'
   
    command = (command + '],name='+'\''+name+'\'' + ')' )
    #exec( command )
    runcom = ('cmds.curve('+command)
    exec(runcom) #DEBUG THIS WONT RETURN THE NAME
    #THIS IS A HACK !
    OUT=[]
    
    curveXform = cmds.ls(sl=True)
    curveShape = cmds.listRelatives(c=True,type='nurbsCurve')
    OUT.append(curveXform[0])
    OUT.append(curveShape[0])
    #THIS IS A HACK !
    #raw_input()
    #cmds.eval(runcom)
    #cmds.eval(runcom)
   
    return OUT

#buildcurvefrompoints([0,0,0,1,1,1,4,4,4 ], False,1 , 'foo')




#####################################################################

class import_kicad_footprint(object):

    def __init__(self):
        self.file_contents = []
        self.kicad_units = 'mils'
        self.maya_units  = 'cm'
        self.dryrun = False   #disable building a model in maya
        self.ZAXIS = 0        #default Z plane to import into
        self.GLOBAL_SCALE = 0.3904 #unit conversion (cm to mills?)

    ##############
    def load(self, filename):
        print('reading file %s'%filename)
        f = open(filename, 'r')
        for line in f:
            self.file_contents.append(line)

    ##############
    #@property
    def scrub(self, inp):
        """ clean up parsed characters from kicad file """

        out = inp
        out = out.strip()
        out = out.replace(')','')
        return out
    
    ##############    
    def do_shift(self, group):
        """ transform data operation after loading but before buidling 
            just for now flip Y negative, maybe more later  
        """
        #flip axis and normalize transforms
        cmds.scale( 1, -1, 1, group, pivot=(0, 0, 0), absolute=True )
        cmds.makeIdentity( group, apply=True, t=1, r=1, s=1, n=2 )

        #now perform a final scaling to ( mils from cm ?)
        cmds.scale( self.GLOBAL_SCALE, self.GLOBAL_SCALE, self.GLOBAL_SCALE, group, pivot=(0, 0, 0), absolute=True )
        cmds.makeIdentity( group, apply=True, t=1, r=1, s=1, n=2 )



    ##############
    def process(self):
        """ take loaded text data and parse it looking for info to build pads and lines objects with """

        #(module KL_ALPS_10KPOT
        part_grp = cmds.group( em=True, name='null1' )

        for l in  self.file_contents:
            linedata =  l.strip().split('(fp_line ')

            sx = 0
            sy = 0
            ex = 0
            ey = 0

            padx = 0
            pady = 0
            dia_padx = 0 #use same value x and y 

            ######################             
            #build layers and assign names to them
            #color like kicad 

            ###################### 
            #build pads and display as NURBS circles
            if len(linedata)<=1:
                parse_pads = linedata[0].split(' ')
                if parse_pads[0]=='(pad':
                    padx = self.scrub(parse_pads[5])
                    pady = self.scrub(parse_pads[6])
                    print 'pad found at %s %s'%(padx,pady)
                    
                    if parse_pads[7]=='(size':
                        dia_padx = parse_pads[8]  
                        #dia_pady = parse_pads[9]  

                    ##############
                    # disable maya object creation
                    if not self.dryrun:
                        # place a locator at origin 
                        sl = cmds.spaceLocator()
                        cmds.move( padx, pady, self.ZAXIS, sl[0], absolute=True )
 
                        # draw a circle to show pin diameter
                        cir = cmds.circle( r=(float(dia_padx)/2), nr=(0, 0, 1), c=(padx, pady, self.ZAXIS) )
                        cmds.parent(cir[0], sl[0])
                        #parent everything to top level 
                        cmds.parent(sl[0], part_grp)

            ###################### 
            #import line segments as first degree NURBS curve segments
            if len(linedata)>1:
                vtxdata = linedata[1].split()
                
                #print linedata

                if vtxdata[0]=='(start':
                    sx = self.scrub(vtxdata[1])
                    sy = self.scrub(vtxdata[2])  
                if vtxdata[3]=='(end':
                    ex = self.scrub(vtxdata[4])
                    ey = self.scrub(vtxdata[5]) 
                #print( 'the line is %s %s %s %s '%(sx,sy,ex,ey))  
                
                ###########
                #disable maya object creation
                if not self.dryrun:

                    #Float By Three format !! Serialized vertices! 
                    segcurve = buildcurvefrompoints([sx,sy,self.ZAXIS, ex,ey,self.ZAXIS ], False,1 , 'kicad')
                    
                    print segcurve
                    #parent everything to top level 
                    cmds.parent(segcurve[0], part_grp)

        #do final transform and scale 
        self.do_shift( part_grp )


###########

IK = import_kicad_footprint()
IK.load('C:/kicad_maya/10k_pot.mod')
IK.process()

###########################################################
