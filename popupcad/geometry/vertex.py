# -*- coding: utf-8 -*-
"""
Written by Daniel M. Aukes.
Email: danaukes<at>seas.harvard.edu.
Please see LICENSE.txt for full license.
"""
   
import numpy
import sympy
    
from popupcad.constraints.constraints import Variable, Constant
    
class BaseVertex(object):
    editable = ['pos','static','construction']
    deletable = []
    
    roundvalue = 5
    def __init__(self,position = None):

        self.id = id(self)
        self._pos = None
        self.setstatic(False)
        self.set_construction(True)
        self.setmoveable(True)

        if position !=None:
            self.setpos(position)
    def set_construction(self,test):
        self.construction = test
    def is_construction(self):
        try:
            return self.construction
        except AttributeError:
            self.construction = True
            return self.construction

    def setstatic(self,test):
        self.static = test

    def is_static(self):
        return self.static

    def setmoveable(self,test):
        self.moveable = test

    def is_moveable(self):
        try:
            return self.moveable
        except AttributeError:
            self.moveable = True
            return self.moveable

    def isValid(self):
        return True

    def is_equal(self,other,tolerance):
        import popupcad.algorithms.points as points
        if type(self)==type(other):
            return points.twopointsthesame(self.getpos(),other.getpos(),tolerance)
        return False

    def __str__(self):
        return 'vertex'+str(self.id)
        
    def vertices(self):
        return [self]

    def lines(self):
        return []

    def __hash__(self):
        return self.id

    def __eq__(self,other):
        if type(self)==type(other):
            return self.id == other.id
        return False
        
    def p(self):
        if self.is_static():
            p_x = Constant(str(self)+'_x')
            p_y = Constant(str(self)+'_y')
        else:
            p_x = Variable(str(self)+'_x')
            p_y = Variable(str(self)+'_y')
        return sympy.Matrix([p_x,p_y,0])

    def setpos(self,pos):
        pos = numpy.array(pos)
        pos.round(self.roundvalue)
        self._pos = tuple(pos.tolist())

    def getpos(self):
        try:
            if self._pos==None:
                self._pos = self.__pos
                del self.__pos
                return self._pos
            else:
                return self._pos
        except AttributeError:
            try:
                self._pos = self.__pos
                del self.__pos
            except AttributeError:
                self._pos = self._Vertex__pos
                del self._Vertex__pos
            return self._pos

    def setsymbol(self,variable,value):
        p = self.p()
        if p[0] == variable:
            self.setpos((value,self.getpos()[1]))            
        if p[1] == variable:
            self.setpos((self.getpos()[0],value))
            
    def properties(self):
        from popupcad.widgets.propertyeditor import PropertyEditor
        return PropertyEditor(self)
        
    def copy(self,identical = True):
        new = type(self)()
        return self.copy_values(new,identical)
        
    def copy_values(self,new,identical=False):
        new.setpos(self.getpos())
        new.static = self.static
        new.setmoveable(self.is_moveable())
        new.set_construction(self.is_construction())
        
        if identical:
            new.id = self.id
        return new            
#        
#    def gen_interactive(self):
#        from popupcad.graphics2d.interactivevertex import InteractiveVertex
#        iv = InteractiveVertex(self)
#        iv.updatefromgeneric()
#        return iv

#    def get_interactive(self):
#        try:
#            return self.interactivevertex
#        except AttributeError:
#            self.interactivevertex = self.gen_interactive()
#            return self.interactivevertex

    def shape_is_equal(self,other):
        from popupcad.filetypes.genericshapebase import GenericShapeBase
        tolerance = GenericShapeBase.tolerance
        import popupcad.algorithms.points as points
        if type(self)==type(other):
            return points.twopointsthesame(self.getpos(),other.getpos(),tolerance)
        return False
        
    def shift(self,dxdy):
        pos = numpy.array(self.getpos())
        dxdy = numpy.array(dxdy)
        newpos = pos+dxdy
        self.setpos(newpos)

    def constrained_shift(self,dxdy,constraintsystem):
        constraintsystem.constrained_shift([(self,dxdy)])

class ShapeVertex(BaseVertex):
    def gen_interactive(self):
        from popupcad.graphics2d.interactivevertex import InteractiveShapeVertex
        iv = InteractiveShapeVertex(self)
        iv.updatefromgeneric()
        return iv

class DrawnPoint(ShapeVertex):
    def exteriorpoints(self):
        return [self.getpos()]
    def interiorpoints(self):
        return []
    def gen_interactive(self):
        from popupcad.graphics2d.interactivevertex import DrawingPoint
        iv = DrawingPoint(self)
        iv.updatefromgeneric()
        return iv
    def points(self):
        return [self.getpos()]
    def segments(self):
        return []
    def segmentpoints(self):
        return []
    def outputinteractive(self):
        from popupcad.graphics2d.interactivevertex import DrawingPoint
        iv = DrawingPoint(self)
        iv.updatefromgeneric()
        return iv

    def outputstatic(self,*args,**kwargs):
        from popupcad.graphics2d.interactivevertex import StaticDrawingPoint
        iv = StaticDrawingPoint(self)
        iv.updatefromgeneric()
        return iv

    def outputshapely(self):
        from shapely.geometry import Point
        p = Point(*self.getpos())
        return p


class ReferenceVertex(BaseVertex):
    def __init__(self,*args,**kwargs):
        super(ReferenceVertex,self).__init__(*args,**kwargs)
        self.setstatic(True)
    def gen_interactive(self):
        from popupcad.graphics2d.interactivevertex import ReferenceInteractiveVertex
        iv = ReferenceInteractiveVertex(self)
        iv.updatefromgeneric()
        return iv
