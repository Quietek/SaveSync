wget https://bootstrap.pypa.io/get-pip.py  
python3 get-pip.py --user
echo "if [ -d "$HOME/.local/bin" ]; then
  PATH='$HOME/.local/bin:$PATH'
fi" >> ~/.bashrc
rm get-pip.py
