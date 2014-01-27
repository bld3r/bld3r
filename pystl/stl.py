#!/usr/bin/env python

import struct
import math

class STL(object):
    def __init__(self,file):
        self.loadFromFile(file)

    ##### Public Methods #####
    def loadFromFile(self,file):
        if isinstance(file,str):
            with open(file,'rb') as f:
                self._unpack(f)
        else:
            self._unpack(file)

    def writeToFile(self,file):
        if isinstance(file,str):
            with open(file,'wb') as f:
                self._pack(f)
        else:
            self._pack(file)

    def writeToTextFile(self,file):
        if isinstance(file,str):
            with open(file,'w') as f:
                self._packText(f)
        else:
            self._packText(file)

    def getTriangles(self):
        return self._triangles

    def rotate(self,point,rotation):
        pass

    def getCenter(self):
        pass

    def scale(self,factor):
        for i,triangle in enumerate(self._triangles):
            for j in range(3):
                self._triangles[i]['vertices'][j] = \
                        triangle['vertices'][j]*factor

    #translate the shape acording to the translation vector
    def translate(self,translation):
        for i,triangle in enumerate(self._triangles):
            for j in range(3):
                self._triangles[i]['vertices'][j] = \
                        triangle['vertices'][j] + translation

    #make copies of the current shape and add them to the shape
    #these copies can, and should, have an offset
    #if offset is a list of offsets, a copy is made for each offset
    def copy(self,offset):
        pass

    #combine two shapes into one
    #pretty much just append the other shape's vertices
    #probably should be similar to __add__() and __iadd__()
    def merge(self,other):
        pass

    ##### Private Methods #####
    def _updateNormals(self):
        for i,triangle in enumerate(self._triangles):
            pass

    ##### Magic Methods #####
    def __len__(self):
        return len(self._triangles)

    #used for joining multiple shapes together
    def __add__(self,other):
        pass
    def __radd__(self,other):
        pass
    def __iadd__(self,other):
        pass

    ##### file related methods #####
    #set the header that will be used when the file is saved
    #if longer than 80 characters, only the first 80 are used
    def setHeader(self,header):
        self._header = header[0:80]
        self._header += ' '*80-len(self._header)

    #todo: look into struct.unpack_from()
    #load from a file
    def _unpack(self,f):
        #read the 80 byte header
        self._header = f.read(80)
        #print 'Header:\n{0}'.format(self._header)
        
        #read the number of triangles
        tCount = struct.unpack('<I',f.read(4))[0]
        #print 'Triangle Count: {0}'.format(tCount)

        #parse each triangle
        self._triangles = [{}]*tCount
        for i in xrange(tCount):
            self._triangles[i]['normal'] = \
                    Vector(struct.unpack('<fff',f.read(12)))
            self._triangles[i]['vertices'] = [(),(),()]
            for j in range(3):
                self._triangles[i]['vertices'][j] = \
                        Vector(struct.unpack('<fff',f.read(12)))
            self._triangles[i]['attribute'] = struct.unpack('<H',f.read(2))[0]

        #I don't think this is necessary
        #if f.read() != '':
            #raise TypeError('Invalid STL File')

    #todo look into struct.pack_into()
    def _pack(self,f):
        #write the 80 byte header
        f.write(self._header)
        
        #write the number of triangles
        tCount = len(self._triangles)
        f.write(struct.pack('<I',tCount))
        
        #write each triangle
        for triangle in self._triangles:
            f.write(struct.pack('<fff',*triangle['normal']))
            for j in range(3):
                f.write(struct.pack('<fff',*triangle['vertices'][j]))
            f.write(struct.pack('<H',triangle['attribute']))

    def _packText(self,f):
        #todo: make this work even with newlines in self._header
        #write the header
        f.write('solid {0}'.format(self._header))

        #todo: finish this method
        for triangle in self._triangles:
            f.write('facet normal {0:e} {1:e} {2:e}'.format(\
                    triangle['normal'][0],triangle['normal'][1],\
                    triangle['normal'][2]))
            f.write('outer loop')
            for j in range(3):
                f.write('vertex {0:e} {1:e} {2:e}'.format(\
                        triangle['vertices'][j][0],triangle['vertices'][j][1],\
                        triangle['vertices'][j][2]))
            f.write('endloop')
            f.write('endfacet')
        f.write('endsolid {0}'.format(self._header))

class Vector(tuple):
    def __init__(self,inVec):
        length = len(inVec)
        if length > 3 or length < 2:
            raise ValueError('Only supports vectors in 3D')
        if length == 2:
            inVec = (inVec[0],inVec[1],0)
        tuple.__init__(inVec)

    def cross((sx,sy,sz),(ox,oy,oz)):
        return Vector((sy*oz-sz*oy,sz*ox-sx*oz,sx*oy-sy*ox))

    def dot((sx,sy,sz),(ox,oy,oz)):
        return sx*ox+sy*oy+sz*oz
    #n dimensional version:
    #def dot(self,other):
        #return sum(map(lambda x,y:x*y,self,other))

    def unit(self):
        return Vector(self / abs(self))

    @property
    def x(self):
        return self[0]
    @property
    def y(self):
        return self[1]
    @property
    def z(self):
        return self[2]

    def __add__((sx,sy,sz),(ox,oy,oz)):
        return Vector((sx+ox,sy+oy,sz+oz))
    def __radd__((sx,sy,sz),(ox,oy,oz)):
        return Vector((sx+ox,sy+oy,sz+oz))

    def __sub__((sx,sy,sz),(ox,oy,oz)):
        return Vector((sx-ox,sy-oy,sz-oz))
    def __rsub__((sx,sy,sz),(ox,oy,oz)):
        return Vector((ox-sx,oy-sy,oz-sz))

    def __mul__(self,other):
        if isinstance(other,(int,float,long)):
            return self._intMul(other)
        return self.dot(other)
    def __rmul__(self,other):
        if isinstance(other,(int,float,long)):
            return self._intMul(other)
        return self.dot(other)
    def _intMul((x,y,z),c):
        return Vector((x*c,y*c,z*c))

    def __div__((x,y,z),c):
        return Vector((x/c,y/c,z/c))
    def __truediv__((x,y,z),c):
        c = float(c)
        return Vector((x/c,y/c,z/c))
    def __floordiv__((x,y,z),c):
        return Vector(map(int,map(math.floor,(x/c,y/c,z/c))))

    def __pos__(self):
        return self

    def __neg__((x,y,z)):
        return Vector((-x,-y,-z))

    def __abs__((x,y,z)):
        return math.sqrt(x**2+y**2+z**2)

    def __str__((x,y,z)):
        return '({0},{1},{2})'.format(x,y,z)

    def __repr__((x,y,z)):
        return 'Vector(({0},{1},{2}))'.format(x,y,z)
