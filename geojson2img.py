import shapely
import numpy as np
from PIL import Image, ImageDraw
from skimage.morphology import skeletonize

from itertools import groupby
from operator import itemgetter

def _expandBy(b0, b1):
  """
  Expand bounding box b0 by b1
  :param b0:
  :param b1:
  :return: expanded new bounding box
  """
  xMin = b0[0] if b0[0] < b1[0] else b1[0]
  yMin = b0[1] if b0[1] < b1[1] else b1[1]
  xMax = b0[2] if b0[2] > b1[2] else b1[2]
  yMax = b0[3] if b0[3] > b1[3] else b1[3]

  return [xMin, yMin, xMax, yMax]

def _numpy2pil(v, d=1):
  """
  Convert a numpy array of vertices to a list of tuples as required by PIL
  :param v: numpy array of vertices
  :param d: optional downsampling factor
  :return: converted tuple list
  """
  vv = []
  for pt in v:
    vv.append((int(pt[0] / d), int(pt[1] / d)))
  return vv

def _getRelativeCoordinates(v, b):
  """
  Convert bounding box vertices in image coordinate space to relative coordinates in the bbox coordinate space
  :param v: a list of bounding box vertices
  :param b: defining bounding box
  :return: converted coordinate list
  """
  vv = []
  for pt in v:
    vv.append((pt[0] - b[0], pt[1] - b[1]))
  return vv

def _checkIntersection(s, lu, ld):
  """
  Check if the line section s is an intersection of lines
  :param s: a line section
  :param lu: the scan line above the line section
  :param ld: the scan line below the line section
  :return: list of intersecting end points
           empty list if not intersecting
  """
  # out of bound check unnecessary with padded outline image
  xMin_start = s[0] - 1
  xMax_start = s[0] + 1
  xMin_end   = s[-1] - 1
  xMax_end   = s[-1] + 1

  up_start   = np.amax(lu[xMin_start:xMax_start+1])
  down_start = np.amax(ld[xMin_start:xMax_start+1])
  up_end     = np.amax(lu[xMin_end  :xMax_end  +1])
  down_end   = np.amax(ld[xMin_end  :xMax_end  +1])

  pts = []

  if up_start > 0 and down_start > 0:
    pts.append(s[0])

  if up_end > 0 and down_end > 0:
    pts.append(s[-1])

  if len(pts) == 0: # both ends are not intersecting points
    up   = up_start > 0 or up_end > 0
    down = down_start > 0 or down_end > 0

    if up and down: # intersecting horizontal section
      pts.append(s[-1])

  return pts

def _isIntersectionPoint(s, lu, ld):
  """
    Check if the line section s is an intersection of lines
    :param s: point location as index on the current line
    :param lu: the scan line above the current line
    :param ld: the scan line below the current line
    :return: boolean values. True: intersection, False: not an intersection
  """
  up   = np.sum(lu[s-1:s+2])
  down = np.sum(ld[s-1:s+2])

  if up > 0 and down > 0:
    return True
  else:
    return False

def _getIntersectionPoints(line, lineUp, lineDown):
  """
  Find the intersection points on the current scan line
  :param line: the current scan line to be processed
  :param lineUp: the scan line above the current scan line
  :param lineDown: the scan line below the current scan line
  :return: a list of lists of vertices, each list of vertices
           corresponds to one line section on the current scan line
  """
  # find non-background pixel locations
  pts = np.where(line != 0)[0]
  sections = [list(map(itemgetter(1), g)) for k, g in groupby(enumerate(pts), lambda i_x: i_x[0] - i_x[1])]

  secPtList = []

  for sec in sections:
    if len(sec) == 1:
      if _isIntersectionPoint(sec[0], lineUp, lineDown):
        secPtList.append(sec[0])
    else:
      pts = _checkIntersection(sec, lineUp, lineDown)
      secPtList.extend(pts)

  return secPtList

def _scanlineConversion(outline, label):
  """
  Convert an image (numpy array) with object boundary lines to a solid pixel mask
  :param outline: image contains boundary polygons
  :param label: foreground pixel value for the final pixel mask
  :return:
  """
  outlineCpy = np.copy(outline)
  outlineCpy = np.pad(outlineCpy, (1,1), 'constant', constant_values=0)

  mask = np.zeros(outlineCpy.shape, dtype=np.uint8)

  for y in range(1, outlineCpy.shape[0]-1):
    line = outlineCpy[y, :]
    lineUp = outlineCpy[y-1, :]
    lineDown = outlineCpy[y+1, :]

    # no polygon to fill on this line
    if np.amax(line) == 0:
      continue

    secPtList = _getIntersectionPoints(line, lineUp, lineDown)

    i = 0
    while i < len(secPtList)-1:
      start = secPtList[i]
      end = secPtList[i+1]

      for ii in range(start, end+1):
        mask[y][ii] = label

      i += 2

  # make sure we are not missing boundary pixels
  mask[outlineCpy > 0] = label

  return mask[1:-1, 1:-1]

def _geojson2outline(g, label=255):
  """
  Create outline image from an geojson annotation
  :param g: geojson annotation
  :return: 1. outline image as numpy ndarray
           2. bounding box of the geojson object
  """
  bboxList    = []
  polygonList = []

  type = g['geometry']['type']
  pls  = g['geometry']['coordinates']

  if type == 'MultiPolygon':
    for pl in pls:
      for vertices in pl:
        ply = shapely.Polygon(vertices)
        polygonList.append(vertices)
        bboxList.append(ply.bounds)
  elif type == 'Polygon':
    for vertices in pls:
      ply = shapely.Polygon(vertices)
      polygonList.append(vertices)
      bboxList.append(ply.bounds)

  bbox = bboxList[0]
  for b in bboxList:
    bbox = _expandBy(bbox, b)

  bbox = np.array(bbox).astype(int)

  img = np.zeros((bbox[3]-bbox[1]+1, bbox[2]-bbox[0]+1, ), dtype=np.uint8)
  imgPIL = Image.fromarray(img)

  # draw polygons as outlines
  for p in polygonList:
    vertices = _numpy2pil(p, 1)
    vertices = _getRelativeCoordinates(vertices, bbox)
    ImageDraw.Draw(imgPIL).polygon(vertices, outline=label)

  return np.array(imgPIL), bbox

def getMaskFromGeojson(g, label=255):
  """
  Get a solid pixel mask from a geojson object
  :param g: geojson object
  :param label: foreground pixel value in the created pixel mask
  :return: 1. pixel mask as numpy ndarray
           2. boundingbox of the geojson object
  """
  outlineImg, bbox = _geojson2outline(g, label)

  outlineImg = skeletonize(outlineImg)
  outlineImg[outlineImg > 0] = 255

  mskImg = _scanlineConversion(outlineImg, label)

  return mskImg, outlineImg, bbox