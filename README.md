

[Bgi_asdis](https://github.com/mchubby-3rdparty/Bgi_asdis)  
- 可以编译和反编译bgi的脚本

Bgi_text  
- 在Bgi_asdis 基础上做的文本导入和导出

pack.py  
unpack.py  
- 打包和拆包arc文档,

```
python3  
pip install -r requirements.txt

py unpack.py data*.arc
解包
py pack.py data*
打包
```

arc.py
-  arc.py 对文档里的文件解密（图片、音乐）

[arc-reader](https://github.com/minirop/arc-reader)  
arc-writer  
- 对它做稍许修改，加一个build.bat脚本用来把它编译成dll，给py的cffi用（见arc.py）
