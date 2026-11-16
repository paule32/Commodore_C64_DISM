import numpy as np
import isohelper as hlp
import cv2

levelData = np.matrix([
  [1,1,1,1,1,1],
  [1,0,0,2,0,1],
  [1,0,0,0,0,1],
  [1,0,0,0,0,1],
  [1,1,1,1,1,1]
])

black_image = np.zeros((288, 382))

tileWidth = 50
borderOffsetX = 70
borderOffsetY = 275

id = 0
tileType = 0

hiso = hlp.IsoHelper()

def do_tileStuff(i,j):
	id = 0
	hiso.tempPt = [j * tileWidth, i * tileWidth]
	hiso.tempPt = hiso.twoDToIso(hiso.tempPt)

def placeTile(id,i,j):
	if (id == 1):
		do_tileStuff(i,j)

def createLevel():
	pos = hlp.tempPt
	for i in range(4):
		for j in range(5):
			tileType = levelData[i,j]
			placeTile(tileType,i,j)

	#cv2.rectangle(black_image,(14,20),(110,128),(110,255,0),3)

	cv2.rectangle(black_image,hiso.twoDToIso[14,20],hiso.twoDToIso[110,128],(110,255,0),3)

	cv2.imshow("Image",black_image)
	cv2.waitKey(0)
