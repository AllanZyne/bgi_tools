
[Bgi_asdis](https://github.com/mchubby-3rdparty/Bgi_asdis)
- 可以编译和反编译 bgi 的脚本

Bgi_text
- 在 Bgi_asdis 基础上做的文本导入和导出


[arc-reader](https://github.com/minirop/arc-reader)
- arc 包的拆包和解密工具（c）
- 对它做了稍许修改，添加 build.bat 和 arc.def 用来把它编译成 dll，给 python 的 cffi 用（见 arc.py）

arc-writer
- 参考 arc-reader 实现的加密和解密算法（python3）

arc.py
- arc-reader 的 dll 提供解密算法，arc-writer 提供加密算法

pack.py  
unpack.py
- python3 实现的 arc 包的拆包、打包工具

```
# python3
pip install -r requirements.txt

py unpack.py --help
py pack.py --help

# 解包
py unpack.py data*.arc
# 打包
py pack.py data*
```
