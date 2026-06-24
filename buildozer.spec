[app]
# 应用名称
title = Lights Out
# 包名
package.name = lightsout
package.domain = org.example
# 源代码目录
source.dir = .
# 主程序文件
source.include_exts = py,png,jpg,kv,json
# 应用版本
version = 0.1
version.code = 1
# 应用要求
requirements = python3,kivy
# 图标
icon.filename = %(source.dir)s/icon.png
# 启动图片
presplash.filename = %(source.dir)s/presplash.png
# 屏幕方向
orientation = portrait
# Android API版本
android.api = 33
# 最低Android版本
android.minapi = 21
# 目标Android版本
android.targetapi = 33
# 是否全屏
fullscreen = 0
# 应用权限
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
# 应用特性
android.features = 
# 屏幕适配
android.wake_lock = False
# 沉浸式状态栏
android.statusbar = True

[buildozer]
# 构建目录
builddir = .buildozer
# 日志级别 (0=errors only, 1=warnings, 2=info, 3=debug)
log_level = 2
