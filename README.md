# Techfine Cloud (SiSe Solar) for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![version](https://img.shields.io/badge/version-1.0.0-blue.svg)]()

[English](#english) | [中文说明](#中文说明)

---

<a name="english"></a>
## English Description

A custom component for Home Assistant to integrate **Techfine / SiSe Solar** inverters via the cloud API (`solar.siseli.com`).

This is the perfect solution for users whose inverters have **locked local ports (8899/Telnet)** or hidden configuration pages, making local integration (Modbus/Solarman) impossible.

### Features
*   ☁️ **Cloud Polling**: No extra hardware (ESP32/RS232) required.
*   🔐 **Auto Login & Signing**: Automatically handles MD5 hashing, HMAC signatures, and Token refresh.
*   ⚡ **Real-time Data**: Fetches Power, Voltage, Current, Daily Energy, Battery SoC, etc.
*   🛠 **Easy Config**: Setup via Home Assistant UI with your cloud username/password.

### Installation

#### Method 1: HACS (Recommended)
1.  Open HACS -> Integrations.
2.  Click the 3 dots in the top right corner -> **Custom repositories**.
3.  Paste this repository URL.
4.  Category: **Integration**.
5.  Click **Add**, then search for "Techfine Cloud" and install.
6.  Restart Home Assistant.

#### Method 2: Manual
1.  Download the `custom_components/techfine_cloud` folder.
2.  Copy it to your Home Assistant's `config/custom_components/` directory.
3.  Restart Home Assistant.

### Configuration
1.  Go to **Settings** -> **Devices & Services**.
2.  Click **Add Integration** and search for **Techfine Cloud**.
3.  Enter your:
    *   **Username**: Your login phone number/account.
    *   **Password**: Your login password (Plain text).
    *   **Device ID**: The ID of your inverter/collector.

---

<a name="中文说明"></a>
## 中文说明

这是一个 Home Assistant 自定义集成，用于通过云端 API (`solar.siseli.com`) 接入 **泰琪丰 (Techfine) / 四色光伏 (SiSe Solar)** 的逆变器数据。

**适用场景：** 如果你的 WiFi 棒（采集器）**封锁了本地 8899 端口**，或者无法进入后台修改 MQTT 配置，导致无法使用 Solarman 集成，那么这个插件是你的最佳选择。

### ✨ 功能特点
*   ☁️ **无需硬件**：不需要购买 ESP32 或进行复杂的 RS232 接线。
*   🔐 **自动登录与签名**：内置了 App 所有的加密算法（MD5 + HMAC-SHA256），只需输入明文密码，插件会自动获取和更新 Token。
*   🔄 **自动维护**：Token 过期自动重连，无需人工干预。
*   📊 **核心数据**：支持读取 功率、电网电压、电流、今日发电量、累计发电量、电池电量 (SoC)、电池电压等。
*   🛠 **UI 配置**：直接在 HA 界面添加，操作简单。

### 🚀 安装方法

#### 方法一：HACS 安装 (推荐)
1.  打开 Home Assistant 的 **HACS** -> **集成**。
2.  点击右上角三个点 -> **自定义仓库**。
3.  输入本项目的 GitHub 地址。
4.  类别选择：**集成**。
5.  点击添加，然后搜索 **Techfine Cloud** 并下载。
6.  重启 Home Assistant。

#### 方法二：手动安装
1.  下载本项目。
2.  将 `custom_components/techfine_cloud` 文件夹复制到你的 HA 配置目录下的 `custom_components/` 文件夹中。
3.  重启 Home Assistant。

### ⚙️ 配置说明

1.  重启 HA 后，进入 **配置** -> **设备与服务**。
2.  点击右下角 **添加集成**。
3.  搜索 **Techfine** 或 **SiSe**。
4.  在弹出的窗口中输入：
    *   **Username**: 你的登录账号（通常是手机号）。
    *   **Password**: 你的登录密码（直接填明文，插件会自动加密）。
    *   **Device ID**: 你的设备 ID。

![配置界面截图](images/config_flow.png)
*(请在此处放置配置界面的截图)*

### ❓ 如何获取 Device ID

1.  电脑浏览器登录 [四色光伏云平台](https://solar.siseli.com)。
2.  点击进入设备详情页。
3.  在浏览器地址栏 URL 中找到 `deviceId=` 后面的数字，或者在设备信息栏中查看。

![获取DeviceID截图](images/device_id.png)
*(请在此处放置网页上获取ID的截图)*

### 📊 支持的传感器

| 实体名称 | 说明 | 单位 |
| :--- | :--- | :--- |
| `sensor.techfine_power` | 当前功率 | W |
| `sensor.techfine_grid_voltage` | 电网电压 | V |
| `sensor.techfine_grid_current` | 电网电流 | A |
| `sensor.techfine_today_energy` | 今日发电量 | kWh |
| `sensor.techfine_total_energy` | 累计发电量 | kWh |
| `sensor.techfine_battery_soc` | 电池剩余电量 | % |
| `sensor.techfine_battery_voltage` | 电池电压 | V |

### ⚠️ 免责声明

*   本插件为非官方开发，仅供学习交流使用。
*   数据来源于四色光伏云平台，请合理设置刷新频率，避免对服务器造成压力。

---
**Enjoy your solar data! 🌞**