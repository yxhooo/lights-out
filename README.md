# Lights Out - 关灯游戏

一个基于Kivy开发的Android"关灯"益智游戏。

## 游戏说明

点击格子会切换该格子及其上下左右相邻格子的状态（亮/灭）。目标是将所有灯都熄灭。

## 功能特性

- 🎮 5×5 网格 puzzle
- ⏱️ 实时计时器
- 📊 最佳记录保存（按网格大小）
- 📱 适配Android平台

## 本地运行

```bash
pip install kivy
python main.py
```

## 打包Android APK

### 方式一：GitHub Actions自动构建（推荐）

1. 将代码推送到GitHub仓库
2. 进入仓库的 **Actions** 标签页
3. 选择 **Build Android APK** workflow
4. 点击 **Run workflow**
5. 构建完成后在 **Artifacts** 中下载APK

### 方式二：本地构建

```bash
# 安装依赖
pip install buildozer cython==0.29.33

# 构建APK
buildozer -v android debug

# APK输出路径：bin/lightsout-0.1-debug.apk
```

## 项目结构

```
├── main.py              # 游戏主程序
├── icon.png             # 应用图标
├── presplash.png        # 启动画面
├── buildozer.spec       # Buildozer配置文件
└── .github/
    └── workflows/
        └── build-android.yml  # GitHub Actions配置
```

## 技术栈

- Python 3.10+
- Kivy 2.x
- Buildozer (Android打包)
