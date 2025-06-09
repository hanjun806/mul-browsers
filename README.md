# 多开浏览器管理工具

基于Python和PyQt5开发的Chrome浏览器Profile管理工具，支持多个浏览器实例的独立管理和配置。

## 功能特性

### 核心功能
- 🔍 **自动扫描Profile**: 自动发现系统中所有Chrome用户配置
- 📊 **详细信息展示**: 显示书签数量、扩展程序、存储大小等
- 🚀 **一键启动**: 支持单个或批量启动浏览器实例
- ⚙️ **个性化配置**: 语言、代理、窗口大小等独立设置
- 📈 **实时监控**: 显示运行状态、内存使用、CPU占用等
- 🎛️ **进程管理**: 优雅关闭或强制终止浏览器进程

### 界面特色
- 🎨 **现代化UI**: 扁平设计风格，支持响应式布局
- 📋 **三栏布局**: Profile列表 + 详细配置 + 状态监控
- 🔄 **实时更新**: 每2秒自动刷新运行状态
- 📝 **操作日志**: 详细记录所有操作和系统事件

## 系统要求

- Python 3.7+
- PyQt5 5.15+
- psutil 5.9+
- Google Chrome浏览器

### 支持的操作系统
- ✅ macOS 10.15+
- ✅ Windows 10/11
- ✅ Linux (主流发行版)

## 安装和使用

### 1. 克隆项目
```bash
git clone <repository-url>
cd mul-browsers
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 运行程序
```bash
python run.py
```
或直接运行主程序:
```bash
python main.py
```

## 使用说明

### 主界面布局

1. **左侧Panel**: Profile列表
   - 显示所有发现的Chrome Profile
   - 双击可直接启动浏览器
   - 显示基本信息（书签数、扩展数等）

2. **中间区域**: 详细配置
   - Profile基本信息展示
   - 启动配置选项
   - 操作按钮（启动/关闭/重启）

3. **右侧Panel**: 状态监控
   - 实时显示运行中的浏览器
   - 系统资源使用情况
   - 操作日志记录

### 配置选项

#### 语言设置
- 中文 (zh-CN)
- 英文 (en-US) 
- 日文 (ja)
- 韩文 (ko)

#### 代理配置
- HTTP/HTTPS代理
- SOCKS4/SOCKS5代理
- 自定义服务器和端口

#### 窗口设置
- 自定义窗口大小
- 支持常见分辨率预设

## 快捷键

- `F5`: 刷新Profile列表
- `Ctrl+Q`: 退出程序
- `双击Profile`: 启动浏览器

## 项目结构

```
mul-browsers/
├── main.py              # 主程序入口
├── run.py               # 启动脚本
├── requirements.txt     # 依赖包列表
├── READER.md           # 需求文档
├── README.md           # 项目说明
├── core/               # 核心模块
│   ├── profile_manager.py    # Profile管理器
│   └── browser_manager.py    # 浏览器进程管理器
└── gui/                # 用户界面
    └── main_window.py        # 主窗口
```

## 开发特性

### 核心类说明

- `ProfileManager`: 负责Chrome Profile的发现、扫描和信息提取
- `BrowserManager`: 负责浏览器进程的启动、关闭和监控
- `MainWindow`: 主GUI窗口，整合所有功能模块

### 设计模式
- 采用MVC架构分离业务逻辑和界面
- 使用数据类(dataclass)管理结构化数据
- 异步更新机制保证界面响应性

## 已知限制

1. **代理认证**: Chrome不直接支持代理用户名密码认证，需要使用扩展程序
2. **Profile锁定**: 如果Profile正在被其他Chrome实例使用，可能无法启动
3. **权限要求**: 某些系统可能需要管理员权限来访问Chrome配置文件

## 故障排除

### 常见问题

**Q: 程序提示"未找到Chrome可执行文件"**
A: 请确保已安装Google Chrome浏览器，或检查安装路径是否标准

**Q: Profile列表为空**
A: 检查Chrome是否已创建用户配置，可以先启动Chrome创建Profile

**Q: 启动浏览器失败**
A: 确保Profile没有被其他Chrome实例占用，尝试关闭所有Chrome窗口后重试

### 调试模式
修改`main.py`中的日志级别可以获得更详细的调试信息。

## 版本历史

- **v1.0.0**: 初始版本
  - 基础Profile管理功能
  - 浏览器启动/关闭功能
  - GUI界面和状态监控

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 许可证

本项目采用MIT许可证 - 详见LICENSE文件 