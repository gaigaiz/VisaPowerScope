# oscill

Python 示波器控制与测量工具包，面向 Tektronix MSO4034（及兼容 SCPI 的示波器），通过 NI-VISA / USB 连接，提供图形界面与命令行两种操作方式。

## 项目解决什么问题

在硬件测试与功耗测量场景中，需要反复从示波器读取波形、执行通道测量、统计功耗并导出测试报告。本项目将仪器连接、数据采集、测量计算、功耗累计与结果导出封装为统一的 Python 工具包，并提供可实时显示波形的图形上位机，替代手动操作示波器面板与人工记录数据。

## 主要功能

- **仪器连接**：NI-VISA 资源扫描与连接，支持 Tektronix MSO4034
- **多通道测量**：平均电压、纹波峰峰值、有效值、最小/最大电压、平均/峰值电流、电流纹波、频率
- **实时波形显示**：基于 PyQtGraph 的多通道波形渲染，支持单次读取与 500 ms 实时刷新
- **功耗统计**：同步采集电压/电流窗口，累计平均功率、峰值功率与能耗（Wh）
- **限值判定**：每通道 Min/Max 限值与功耗上限，自动判定 PASS / FAIL
- **结果导出**：波形 CSV 导出、JSON 测试报告（含测量值、功耗、限值、判定结果）
- **中英文双语**：界面语言运行时切换，无需重启；CLI 支持 `OSCILL_LANGUAGE` 环境变量
- **模拟模式**：内置模拟示波器，无需硬件即可验证环境与流程
- **命令行工具**：`oscill` 支持 identify / list-resources / measure

## 安装方法

> 目标平台：Ubuntu 22.04 LTS + Python 3.10.12

```bash
# 1. 系统依赖（PyQt5 与 NumPy 用 apt，避免与 pip 混用）
sudo apt install -y python3-pyqt5 python3-numpy python3-pip python3-venv

# 2. 创建虚拟环境（必须带 --system-site-packages 以访问系统 pyvisa）
python3 -m venv --system-site-packages .venv
source .venv/bin/activate

# 3. 安装 pyqtgraph（纯 Python，pip 安装不冲突）
pip install "pyqtgraph>=0.13,<0.14"

# 4. 安装本项目（--no-deps 避免 pip 改动系统 pyvisa）
pip install --no-deps -e .
```

pyvisa 与 NI-VISA 运行时沿用系统已有环境，不在本项目依赖中强制管理。

## 使用方法

### 图形界面

```bash
source .venv/bin/activate
oscill-gui
```

界面顶部右侧可切换中文 / English；在设备连接区输入或扫描 VISA 资源后点击连接；勾选通道、选择测量类型后开始测量与波形显示。

### 命令行

```bash
# 列出 VISA 资源
oscill list-resources

# 识别示波器
oscill --resource "USB0::0x0699::0x0408::<序列号>::INSTR" identify

# 测量 CH1 平均电压
oscill --resource "USB0::0x0699::0x0408::<序列号>::INSTR" \
  --model tektronix-mso4034 measure --parameter MEAN --source CH1

# 模拟模式（无需硬件）
oscill --simulate identify
oscill --simulate --model tektronix-mso4034 measure --parameter VPP --source CH1
```

详细环境配置与操作说明见 [环境配置与使用说明.md](Environment%20configuration%20and%20usage%20instructions/环境配置与使用说明.md)，快速上手指南见 [快速使用步骤.md](Environment%20configuration%20and%20usage%20instructions/快速使用步骤.md)，NI-VISA 运行时安装见 [NI-VISA安装与使用说明.md](Environment%20configuration%20and%20usage%20instructions/NI-VISA安装与使用说明.md)。

## 输入输出示例

**输入**（模拟模式识别）：

```bash
oscill --simulate identify
```

**输出**：

```
OSCILL,SIMULATOR,0001,1.0
```

**输入**（模拟 Tektronix 测量 CH1 峰峰值）：

```bash
oscill --simulate --model tektronix-mso4034 measure --parameter VPP --source CH1
```

**输出**：

```
CH1 VPP: 1.234
```

连接真实示波器时，`identify` 返回仪器的 `*IDN?` 字符串（如 `TEKTRONIX,MSO4034,<序列号>,...`），`measure` 返回对应通道的测量值与单位。

## 项目结构

```
oscill-0.1.0-linux/
├── oscill/                          # Python 包
│   ├── __init__.py
│   ├── controller.py                # 仪器控制层（Oscilloscope / TektronixMSO4034 / Waveform）
│   ├── services.py                  # 采集、测量、功耗统计服务
│   ├── transport.py                 # VISA 传输层与模拟传输
│   ├── worker.py                    # 后台串行执行器
│   ├── i18n.py                     # 轻量国际化（中英文字典 + 运行时切换）
│   ├── gui.py                      # PyQt5 + PyQtGraph 图形界面
│   ├── cli.py                      # 命令行入口
│   └── py.typed                    # PEP 561 类型标记
├── Environment configuration and usage instructions/
│   ├── NI-VISA安装与使用说明.md      # NI-VISA 运行时安装与配置
│   ├── 环境配置与使用说明.md          # Ubuntu 22.04 完整环境配置与 GUI/CLI 使用指南
│   ├── 快速使用步骤.md               # 快速上手指南
│   └── 项目执行计划.md               # 改造执行计划 v1.2
├── NI_VISA_deb/
│   └── ni-ubuntu2204-drivers-2026Q3.deb   # NI-VISA Ubuntu 22.04 驱动包
├── _static_check.py                # i18n 键完整性与属性自检（零依赖）
├── _format_check.py                # 格式化占位符一致性自检（零依赖）
├── pyproject.toml                  # 包配置与依赖声明
├── LICENSE                         # MIT
└── README.md
```

> `oscill-0.1.0.dist-info/`、`.venv/`、`__pycache__/` 等构建与环境产物已在 `.gitignore` 中排除。

## 项目管理

本项目的开发执行计划（[项目执行计划.md](Environment%20configuration%20and%20usage%20instructions/项目执行计划.md)）使用 [project-execution-planner](https://github.com/gaigaiz/The-production-and-sharing-of-SKILL) Skill 制作，该 Skill 来自 [The-production-and-sharing-of-SKILL](https://github.com/gaigaiz/The-production-and-sharing-of-SKILL) 项目，可将口语化项目需求转化为结构完整、可执行的项目执行计划文档。

## 许可证

MIT
