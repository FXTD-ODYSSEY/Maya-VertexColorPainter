
# Maya-VertexColorPainter

单通道顶点色绘制工具

[博客总结](https://blog.l0v0.com/posts/1cdbfd5e.html)

[en_US](./README.md) | [zh_CN](./README_zh.md)


## 安装 

我使用了 Maya 的模块安装方法，借助 rj 大神的力量，可以去他的 [github仓库](https://github.com/robertjoosten/maya-module-installer) 查阅。    
只需要按照下面的步骤进行操作即可：

1. 在 Github 上下载发布的插件压缩包 （或者克隆到本地）
2. 将压缩包解压到任意路径上（建议路径保持全英文）(如果是克隆分支的不需要解压操作)
3. 将 `VertexColorPainter.mel` 拖拽到 Maya 的视窗上 

当你安装成功之后，你每次打开 Maya 插件就会自动加载 `vertex_color_painter.py` 插件。   

## 使用视频

https://cdn.jsdelivr.net/gh/FXTD-odyssey/FXTD-odyssey.github.io@master/post_img/1cdbfd5e/demo.mp4

## 使用说明

![alt](https://cdn.jsdelivr.net/gh/FXTD-odyssey/FXTD-odyssey.github.io@master/post_img/1cdbfd5e/dfb9ca62bbf7b8121c65dfb559630a1c.jpeg)

在原生 UI 基础上添加了两个 UI

**Single Channel**
1. RGB
2. R
3. G
4. B
5. A

分别对应 全通道 和 四个单通道绘制模式

全通道模式和默认绘制一致  
单通道模式则获取 Color Value 对应通道的颜色值绘制

---

**Color Display**
1. Auto
2. RGB
3. R
4. G
5. B
6. A

切换顶点色显示模式

