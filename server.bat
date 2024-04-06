@echo off
CMD /k "call venv/scripts/activate.bat & call python yolov9/detect.py --weights best.pt --source 0 --conf 0.8 --device 0"
start /k "call venv/scripts/activate.bat & call python client.py"