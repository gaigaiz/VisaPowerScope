# NI-VISA 安装与使用说明（Ubuntu 22.04 + oscill）

> 适用平台：Ubuntu 22.04 LTS x86_64
> 配套项目：oscill（https://github.com/gaigaiz/VisaPowerScope）
> 示波器：Tektronix MSO4034（USB / NI-VISA）
> 文档日期：2026-09-18

---

## 1. 概述

NI-VISA 是 National Instruments 提供的虚拟仪器软件架构（Virtual Instrument Software Architecture），为 USB / GPIB / 串口等仪器提供统一的 I/O 接口。oscill 项目在 Linux 上**默认使用 NI-VISA 后端**（`@ni`），通过 Python `pyvisa` 库调用 `libvisa.so` 与示波器通信。

本文档说明如何在 Ubuntu 22.04 上安装 NI-VISA 运行时，并与 oscill 项目配合使用。

---

## 2. 安装包说明

项目 `NI_VISA_deb/` 目录下提供了 NI 驱动仓库配置包：

```
NI_VISA_deb/
└── ni-ubuntu2204-drivers-2026Q3.deb
```

该包是 NI 2026 Q3 驱动套件的 **apt 仓库配置包**（约 33 KB），作用是：
- 添加 NI 官方 apt 软件源
- 导入 NI 软件包签名 GPG 密钥
- 注册 NI 驱动套件的优先级配置

安装此包后，即可通过 `apt` 安装完整的 NI-VISA 运行时及相关驱动。

> 如需最新版本，可从 NI 官网下载对应 Ubuntu 22.04 的驱动仓库包：https://www.ni.com/zh-cn/support/downloads/drivers.html

---

## 3. 安装步骤

### 3.1 安装 NI 驱动仓库配置包

```bash
cd /path/to/oscill-0.1.0-linux   # 替换为你的实际项目路径
sudo dpkg -i NI_VISA_deb/ni-ubuntu2204-drivers-2026Q3.deb
```

如果提示缺少依赖，执行：

```bash
sudo apt install -f
```

### 3.2 更新软件源

```bash
sudo apt update
```

### 3.3 安装 NI-VISA 运行时

```bash
sudo apt install -y ni-visa
```

> `ni-visa` 会自动拉入依赖（包括 NI USB 驱动内核模块、`libvisa.so` 运行时库等）。如果 `ni-visa` 包名不可用，可执行 `apt search ni-visa` 查看实际包名（部分版本中运行时包名为 `ni-visa-runtime`）。

安装过程中可能出现 NI 最终用户许可协议（EULA）提示，按提示确认即可。

### 3.4 重启系统

NI 内核模块需要在重启后加载：

```bash
sudo reboot
```

---

## 4. 验证安装

### 4.1 检查 NI-VISA 运行时库

```bash
ls /usr/lib/x86_64-linux-gnu/libvisa*
```

预期输出类似：
```
/usr/lib/x86_64-linux-gnu/libvisa.so.0
/usr/lib/x86_64-linux-gnu/libvisa.so.0.0.0
```

### 4.2 检查 NI 内核模块

```bash
lsmod | grep ni
```

预期能看到 `ni_usb` 等相关模块已加载。

### 4.3 用 Python pyvisa 验证

oscill 项目使用系统 `pyvisa`（通过 `--system-site-packages` 的 venv 访问）。确保已激活 oscill 的虚拟环境：

```bash
source /path/to/oscill-0.1.0-linux/.venv/bin/activate
python -c "import pyvisa; rm = pyvisa.ResourceManager('@ni'); print('NI-VISA backend OK'); print(rm.list_resources())"
```

- 输出 `NI-VISA backend OK` 表示 pyvisa 成功加载 NI-VISA 后端
- `list_resources()` 会列出当前连接的 VISA 资源（未接设备时可能为空元组 `()`）

如果报 `VI_ERROR_RSRC_NFOUND` 或后端加载失败，见第 7 节常见问题。

---

## 5. 与 oscill 项目配合使用

### 5.1 虚拟环境要求

oscill 的虚拟环境**必须**带 `--system-site-packages`，以便访问系统安装的 `pyvisa` 和 NI-VISA 运行时：

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
```

> 不要在 venv 内单独 `pip install pyvisa`，这可能与系统 NI-VISA 运行时产生版本冲突。系统 `pyvisa` 已通过 `--system-site-packages` 可见。

### 5.2 oscill 默认后端

oscill 在 Linux 上默认使用 NI-VISA 后端（`@ni`），无需额外配置。代码中的后端选择逻辑：

```python
# oscill/transport.py
def _get_visa_backend() -> str:
    return os.environ.get("OSCILL_VISA_BACKEND", "@ni")
```

支持的后端：
| 后端值 | 说明 |
|--------|------|
| `@ni` | NI-VISA（默认，需安装本文档所述 NI-VISA） |
| `@py` | pyvisa-py 纯 Python 后端（需额外安装 pyusb + libusb，不推荐用于本项目） |
| `/path/to/libvisa.so` | 显式指定 libvisa.so 路径 |

如需临时切换后端：

```bash
OSCILL_VISA_BACKEND=@ni oscill list-resources
```

### 5.3 列出示波器资源

将示波器通过 USB 连接到电脑，开机后执行：

```bash
source .venv/bin/activate
oscill list-resources
```

预期输出类似：
```
USB0::0x0699::0x0408::C012345::INSTR
```

其中 `0x0699` 是 Tektronix 的 USB VID，`0x0408` 是 MSO4034 的 PID，`C012345` 是你的示波器序列号（每台不同）。

> 如果 `list-resources` 输出为空，先确认 USB 线已连接、示波器已开机，再参考第 6 节 USB 权限检查。

### 5.4 命令行识别示波器

```bash
oscill --resource "USB0::0x0699::0x0408::<你的序列号>::INSTR" identify
```

预期输出示波器的 `*IDN?` 字符串，类似：
```
TEKTRONIX,MSO4034,C012345,CF:91.1CT FV:1.38
```

### 5.5 命令行测量

```bash
oscill --resource "USB0::0x0699::0x0408::<你的序列号>::INSTR" \
  --model tektronix-mso4034 measure --parameter MEAN --source CH1
```

### 5.6 图形界面

```bash
oscill-gui
```

1. 在"设备连接"区点击 **扫描**，下拉框中选择示波器资源
2. 点击 **连接**，身份信息栏显示 `*IDN?` 字符串
3. 勾选通道、选择测量类型，点击 **开始测量**
4. 点击 **读取波形** 或 **实时刷新** 查看波形

---

## 6. USB 设备权限

NI-VISA 安装时通常会自动配置 udev 规则，允许普通用户访问 USB 仪器。如果遇到权限问题（`list-resources` 看不到设备或报 `VI_ERROR_PERM`），按以下步骤排查：

### 6.1 确认设备已被系统识别

```bash
lsusb | grep -i tek
```

预期输出类似：
```
Bus 003 Device 005: ID 0699:0408 Tektronix, Inc.
```

### 6.2 检查 NI udev 规则

```bash
ls /etc/udev/rules.d/ | grep -i ni
```

NI 驱动通常会安装类似 `ni-usbtmc.rules` 或 `99-nilxibus.rules` 的规则文件。

### 6.3 重新加载 udev 规则

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

然后重新插拔示波器 USB 线。

### 6.4 将用户加入 plugdev 组（备选）

如果 udev 规则未生效，可尝试将当前用户加入 `plugdev` 组：

```bash
sudo usermod -aG plugdev $USER
```

注销并重新登录后生效。

---

## 7. 常见问题

**Q1：`oscill list-resources` 报错 `VI_ERROR_INV_SETUP` 或找不到 NI-VISA 后端**
A：NI-VISA 未正确安装或 `libvisa.so` 不在库路径中。重新执行第 3 节安装步骤，确认 `ls /usr/lib/x86_64-linux-gnu/libvisa*` 有输出，并重启系统。

**Q2：`import pyvisa` 成功但 `ResourceManager('@ni')` 报错**
A：系统 `pyvisa` 版本与 NI-VISA 运行时不匹配。确认使用的是系统 `pyvisa`（`python -c "import pyvisa; print(pyvisa.__file__)"` 应指向 `/usr/lib/python3/dist-packages/`），而非 venv 内单独安装的版本。

**Q3：`oscill list-resources` 输出为空，但 `lsusb` 能看到示波器**
A：USB 权限问题。按第 6 节检查 udev 规则，重新加载规则并重新插拔 USB 线。

**Q4：连接时报 `VI_ERROR_RSRC_NFOUND`（资源未找到）**
A：资源名拼写错误。用 `oscill list-resources` 查看实际资源名，完整复制。注意 VISA 资源名区分大小写，必须以 `::INSTR` 结尾。

**Q5：连接时报 `VI_ERROR_TMO`（超时）**
A：示波器未开机、USB 线接触不良，或示波器正被其他程序占用。确认示波器开机、无其他软件连接，适当增大超时时间。

**Q6：可以用 pyvisa-py（@py）替代 NI-VISA 吗？**
A：技术上可以，但需要额外安装 `pyvisa-py`、`pyusb` 和 `libusb`，且部分 Tektronix 二进制波形传输（`CURVE?`）在 pyvisa-py 下可能不稳定。oscill 项目默认并推荐使用 NI-VISA（`@ni`）。

---

## 8. 卸载 NI-VISA（如需）

```bash
sudo apt remove -y ni-visa
sudo apt autoremove -y
# 移除 NI 仓库配置包
sudo dpkg -r ni-ubuntu2204-drivers
```

---

## 9. 参考链接

- NI Linux 设备驱动下载：https://www.ni.com/zh-cn/support/downloads/drivers.html
- PyVISA 文档：https://pyvisa.readthedocs.io/
- oscill 项目：https://github.com/gaigaiz/VisaPowerScope

---

*安装完成后，建议运行 `oscill --simulate identify` 确认 oscill 本身正常，再连接真实示波器执行 `oscill list-resources` 和 `identify` 验证 NI-VISA 链路。*
