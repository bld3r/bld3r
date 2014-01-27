#import visvis as vv
import numpy as np
import struct
import time

class StlAsciiReader(StlReader):
		
	def readline(self):
		""" Simple readLine method that strips whitespace and skips
		empty lines.
		"""
		line = ''
		while not line:
			line = self._f.readline().decode('ascii', 'ignore').strip()
		return line
	
	
	def readFace(self, vertices, check=False):
		""" readFace(vertices, check=False)
		
		Read a face (three vertices) from the file. The normal is ignored;
		we will calculate it ourselves.
		
		Info: http://en.wikipedia.org/wiki/STL_%28file_format%29
		
		What a face in a file looks like
		--------------------------------
		facet normal ni nj nk
		outer loop
		vertex v1x v1y v1z
		vertex v2x v2y v2z
		vertex v3x v3y v3z
		endloop
		endfacet
		
		"""
		
		# Read normal and identifier
		line_normal = self.readline()
		if line_normal.startswith('endsolid'):
			raise EOFError() # Finished
		line_begin_loop = self.readline()
		
		# Read 3 vertices
		for i in range(3):
			line_vertex = self.readline()
			numbers = [num for num in line_vertex.split(' ')]
			numbers = [float(num) for num in numbers[1:] if num] 
			vertices.append(*numbers)
		
		# Read two more identifiers
		line_end_loop = self.readline()
		line_end_facet = self.readline()
		
		# Test?
		if check:
			if not line_normal.startswith('facet normal'):
				print('Warning: expected facet normal.')
			if line_begin_loop != "outer loop":
				print('Warning: expected outer loop.')
			if line_end_loop != "endloop":
				print('Warning: expected endloop.')
			if line_end_facet != "endfacet":
				print('Warning: expected endfacet.')
