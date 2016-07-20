cat stat_medicine* |sort -t "," -k 1 -n > ../stat_medicine_sorted.csv
#cat medicine* |sort| uniq > ../medicine.csv
#cat medicine* |sort| uniq |grep -v '姓名' > ../medicine.csv
cat medicine* |sort| uniq |sort -t ',' -k 9 -n > ../medicine.csv
