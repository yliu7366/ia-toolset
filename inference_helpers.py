def getPaddedImageSizeForInference(img_size, padding, ptch_size, ptch_overlap):
  """
  Calculate new image size for patched based inference with overlapping patch extraction and stitching
  Formula for patch extraction: (img_size + padding) // wndSize + 1
  :param img_size: input image size, for example [121, 610, 1280]
  :param padding: paddings to the input image, for example, [16, 16, 16]
  :param ptch_size: patch size, for example, [64, 128, 128]
  :param ptch_overlap: patch overlapping pixels, for example, [16, 16, 16]
  :return: new image size with paddings and effective patch sizes
  """
  newSize = []
  wndSize = []

  for i, p, ps, po in zip(img_size, padding, ptch_size, ptch_overlap):
    # wndSize: effective patch size, equals ptch_size minus ptch_overlap * 2
    size = ps - po * 2
    wndSize.append(size)
    newSize.append(((i + p * 2) // size + 1) * size + ps)

  return newSize, wndSize

def getOverlappingCoordsForInference2D(img_size, wnd_size, ptch_size, offset = [0, 0]):
  """
  Generate patch coordinates for overlapping sliding window based inference
  :param img_size: [image size y, image size x]
  :param wnd_size: [wnd_size y, wnd_size x], effective patch size, equals ptch_size - ptch_overlap * 2
  :param ptch_size: [patch size y, patch size x]
  :param offset: optional offset for dithered patch generatioin
  :return: [[y0, x0], ...] list of the top left point coordinates of each patch
  """
  coords = []
  for y in range(img_size[0] // wnd_size[0]):
    for x in range(img_size[1] // wnd_size[1]):
      yy = y * wnd_size[0] + offset[0]
      xx = x * wnd_size[1] + offset[1]
      if (yy + ptch_size[0]) < img_size[0] and (xx + ptch_size[1]) < img_size[1]:
        coords.append([yy, xx])

  return coords
