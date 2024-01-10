# utility helpers
def byteLiteralList2String(bl):
  """
  convert a list of byte literals to string
  for example: bl: b'0' b'.' b'0' b'0' b'5' b'2'
               bl_str: "0.0052"
  Imaris/HDF save strings as lists of byte literals
  :param bl: a list of byte literals
  :return: a string version of the input binary literal list
  """
  bl_list = [v.decode() for v in bl]
  str = ""
  bl_str = str.join(bl_list)

  return bl_str
