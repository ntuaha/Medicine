with open('./stat_medicine_filter.csv','w+') as fw:
  with open('./stat_medicine.csv','r') as f:
    lines = f.readlines()
    a = []
    for line in lines:
      [index,name,sex,count] = line.strip().split(",")
      if len(a)==0:
        a.append([index,name,sex,count])
      elif a[len(a)-1][0] != index:
        a.append([index,name,sex,count])
      else:
        a[len(a)-1][3] = count
  for aa in a:
    fw.write(",".join(aa)+"\n") 
