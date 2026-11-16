import numpy as Math

tempPt = [0,0]

class IsoHelper:
	def __init__(self):
		pass

	def isoTo2D(self, pt):
		tempPt = [(2*pt[1]+pt[0])/2, (2*pt[1]-pt[0])/2]
		return tempPt

	def twoDToIso(self, pt):
		tempPt = [(pt[1]-pt[0]), (pt[0]+pt[1])/2]
		return tempPt

	def getTileCoordinates(self, pt, tileHeight):
		tempPt = [Math.floor(pt[0]/tileHeight), Math.floor(pt[1]/tileHeight)]
		return tempPt

	def get2dFromTileCoordinates(self, pt, tileHeight):
		tempPt = [pt[0]*tileHeight, pt[1]*tileHeight]
 		return tempPt;

