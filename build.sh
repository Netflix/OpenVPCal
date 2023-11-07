if [ -d "myenv" ]; then
  sudo rm -rf myenv
fi

if [ -d "dist" ]; then
  sudo rm -rf dist
fi

if [ -d "build" ]; then
  sudo rm -rf dist
fi

if [ -d "OpenVPCal.spec" ]; then
  sudo rm -rf "OpenVPCal.spec"
fi

python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
pip freeze > requirements.txt
python3 compile.py
deactivate

if [ -d "build" ]; then
  sudo rm -rf build
fi

if [ -d "myenv" ]; then
  sudo rm -rf myenv
fi

if [ -f "OpenVPCal.spec" ]; then
  sudo rm -rf "OpenVPCal.spec"
fi

