#!/bin/bash
#source venv/taco-tracker/bin/activate

python3 app.py --driver='Scott' --route='CHI' --rate=3 --density 7 --multiplier 1.45 & 
python3 app.py --driver='Chad' --route='STL' --rate=4 --density 3 --multiplier 0.9 &
python3 app.py --driver='Paul' --route='KC' --rate=3 --density 3 &
