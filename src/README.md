## DADC.py
Main module with DADC algorithm. It uses algoMeter framework interface and bundle module for bundle management.
DADC function receive in input algormeter kernel class instance p with properties and methods for each problem optimization. 
DADC iterates by calling
```
for k in p.loop()
  ...
```

## bundle.py
General bundle management module with quadratic programming solver method  (by qpsolvers package).

## ../scripts/runme.py
call algorMeter main with problems list and algorithms list (DADC in our case). It returns pandas dataframes with results and writes a .csv file in csv folder

## algorMeter
See https://github.com/xedla/algormeter/blob/master/README.md   
See algormeter minimize method (example6.py in algormeter repository) if you want use algormeter compatible algorithm like DADC to search problem/function minimum.