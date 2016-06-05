
arc-reader 
https://github.com/minirop/arc-reader
对它做稍许修改，加一个build.bat脚本用来把它编译成dll，给py的cffi用（见arc.py）

bp_tools
script_tools

python3
pip install -r requirements.txt

[imaimo]

py unpack.py data*.arc
解包
py pack.py data*
打包
