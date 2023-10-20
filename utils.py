def getPaddedImageSizeForInference(img_size, padding, ptch_size, ptch_overlapping):
  """
  Calculate new image size for patched based inference with overlapping patch extraction and stitching
  Formula for patch extraction: (img_size + padding) // wndSize + 1
  :param img_size: input image size, for example [121, 610, 1280]
  :param padding: paddings to the input image, for example, [16, 16, 16]
  :param ptch_size: patch size, for example, [64, 128, 128]
  :param ptch_overlapping: patch overlapping pixels, for example, [16, 16, 16]
  :return: new image size with paddings
  """
  newSize = []
  
  for i, p, ps, po in zip(img_size, padding, ptch_size, ptch_overlapping):
    # wndSize: effective patch size, equals ptch_size mius patch_overlapping * 2
    wndSize = ps - po*2
    newSize.append( ((i+p) // wndSize) * wndSize + ps * 2 )
    
return newSize
