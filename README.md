# Techfine Cloud 集成

# Techfine Cloud (SiSe Solar) for Home Assistant

![Image](https://p3-flow-imagex-sign.byteimg.com/tos-cn-i-a9rns2rl98/rc/online_import/94f766d040c7496eb7d5c75026864296~tplv-noop.jpeg?rk3s=49177a0b&x-expires=1764141167&x-signature=Ma8YBsE16csPJVhVtFe%2Fcr61idU%3D&resource_key=40e46846-3f96-4db5-8b56-d75078c1115b&resource_key=40e46846-3f96-4db5-8b56-d75078c1115b)

![Image](https://p3-flow-imagex-sign.byteimg.com/tos-cn-i-a9rns2rl98/rc/online_import/b7ede164d1e3490bb0f9724bdb494818~tplv-noop.jpeg?rk3s=49177a0b&x-expires=1764141167&x-signature=7cmdsgsys8gM7XavFPr%2FF%2BcjrS8%3D&resource_key=890e0fd9-3439-487f-b4ef-5ffee2e130bf&resource_key=890e0fd9-3439-487f-b4ef-5ffee2e130bf)

![Image](https://p3-flow-imagex-sign.byteimg.com/tos-cn-i-a9rns2rl98/rc/online_import/de3f6d68f6e64d4eafb33514ce739025~tplv-noop.jpeg?rk3s=49177a0b&x-expires=1764141167&x-signature=eYrYGKsUX5OUCzZa59FGqT986fQ%3D&resource_key=c65f1f4c-5d13-4c13-813b-8f4afca8be92&resource_key=c65f1f4c-5d13-4c13-813b-8f4afca8be92)

[English](#english) | [中文说明](#中文说明)

---

<a name="english"></a>

## English Description

A custom component for Home Assistant to integrate **Techfine / SiSe Solar** inverters via the cloud API (`solar.siseli.com`).

**Why this integration?**

Many new Techfine WiFi loggers (firmware SolarV57+) have **locked local ports (8899/Telnet)** and hidden configuration pages, making local integration (Modbus/Solarman) impossible. This integration solves that by fetching data directly from the cloud using the official mobile app's API.

### Features

- ☁️ **Cloud Polling**: Works even if local ports 8899/1883 are blocked.

- 🔐 **Secure Auth**: Automatically handles MD5 password hashing and HMAC-SHA256 API signing.

- ⚡ **Real-time Data**: Updates every **10 seconds** (configurable).

- 📊 **Comprehensive Metrics**: Monitors PV Power, Grid Voltage, Battery SoC, Charging/Discharging Currents, and Daily/Total Energy.

- 🛠 **UI Config**: Easy setup via Home Assistant UI.

- 🌐 **Chinese Language Support**: Sensors and device names are displayed in Chinese for better user experience.

### Installation

#### Method 1: HACS (Recommended)

1. Open HACS -> Integrations.

2. Click the 3 dots in the top right corner -> **Custom repositories**.

3. Paste this repository URL.

4. Category: **Integration**.

5. Click **Add**, then search for "Techfine Cloud" and install.

6. Restart Home Assistant.

#### Method 2: Manual

1. Download the `custom_components/techfine_cloud` folder from this repo.

2. Copy it to your Home Assistant's `config/custom_components/` directory.

3. Restart Home Assistant.

### Configuration

1. Go to **Settings** -> **Devices & Services**.

2. Click **Add Integration** and search for **Techfine Cloud**.

3. Enter your:

    - **Username**: Your login phone number/account.

    - **Password**: Your login password (Plain text).

    - **Device ID**: The ID of your inverter (Found in the URL of the web dashboard).

---

<a name="中文说明"></a>

## 中文说明

这是一个 Home Assistant 自定义集成，用于通过云端 API (`solar.siseli.com`) 接入 **泰琪丰 (Techfine) / 四色光伏 (SiSe Solar)** 的逆变器数据。

**背景：**

许多新款的 Techfine WiFi 采集器（特别是固件版本 SolarV57及以上）**封锁了本地 TCP 8899 和 MQTT 端口**，且隐藏了配置页面，导致无法使用 Solarman 集成进行本地接入。本插件通过模拟 App 的云端通信协议，完美解决了无法获取数据的问题。

### ✨ 功能特点

- ☁️ **无视端口封锁**：不需要硬件破解，不需要 ESP32，只要设备在线即可获取数据。

- 🔐 **自动签名认证**：内置了 App 的核心加密算法（MD5 + HMAC-SHA256），自动处理 Token 获取与续期。

- 🔄 **秒级刷新**：默认 **10秒** 刷新一次数据，接近本地体验。

- 📈 **数据全**：支持光伏板(PV)、电池(Battery)、电网(Grid)、负载(Load)等全方位数据监控。

- 🛠 **配置简单**：直接在 HA 界面输入账号密码即可，无需编写 YAML。

- 🌐 **中文界面**：设备和传感器名称均为中文，更符合中文用户习惯。

### 🚀 安装方法

#### 方法一：HACS 安装 (推荐)

1. 打开 Home Assistant 的 **HACS** -> **集成**。

2. 点击右上角三个点 -> **自定义仓库**。

3. 输入本项目的 GitHub 地址。

4. 类别选择：**集成**。

5. 点击添加，然后搜索 **Techfine Cloud** 并下载。

6. 重启 Home Assistant。

#### 方法二：手动安装

1. 下载本项目。

2. 将 `custom_components/techfine_cloud` 文件夹完整复制到你的 HA 配置目录下的 `custom_components/` 文件夹中。

3. 重启 Home Assistant。

### ⚙️ 配置说明

1. 重启 HA 后，进入 **配置** -> **设备与服务**。

2. 点击右下角 **添加集成**。

3. 搜索 **Techfine** 或 **SiSe**。

4. 在弹出的窗口中输入：

    - **Username**: 你的登录账号（通常是手机号）。

    - **Password**: 你的登录密码（直接填明文，插件会自动加密）。

    - **Device ID**: 你的设备 ID。

![Image](&resource_key=)

### ❓ 如何获取 Device ID

1. 电脑浏览器登录 [四色光伏云平台](https://solar.siseli.com)。

2. 点击进入设备详情页。

3. 在浏览器地址栏 URL 中找到 `deviceId=` 后面的数字（通常是 18 位数字）。

![Image](&resource_key=)

### 📊 支持的传感器列表

插件会自动创建以下实体（Entity），并按优先级排序：

|实体ID (Entity ID)|显示名称|说明|单位|
|---|---|---|---|
|`sensor.techfine_cloud_发电功率`|发电功率|光伏输入总功率|W|
|`sensor.techfine_cloud_输出有功功率`|输出有功功率|逆变器总输出功率|kW|
|`sensor.techfine_cloud_市电电压`|市电电压|电网输入电压|V|
|`sensor.techfine_cloud_电池电压`|电池电压|电池两端电压|V|
|`sensor.techfine_cloud_电池充电电流`|电池充电电流|电池正在充电的电流|A|
|`sensor.techfine_cloud_电池放电电流`|电池放电电流|电池正在放电的电流|A|
|`sensor.techfine_cloud_电池容量`|电池容量|电池剩余电量百分比 (SoC)|%|
|`sensor.techfine_cloud_pv电压`|PV电压|光伏阵列输入电压|V|
|`sensor.techfine_cloud_pv电流`|PV电流|光伏阵列输入电流|A|
|`sensor.techfine_cloud_输出电压`|输出电压|逆变器交流输出电压|V|
|`sensor.techfine_cloud_负载百分比`|负载百分比|逆变器当前负载率|%|
|`sensor.techfine_cloud_今日发电量`|今日发电量|当天累计发电量|kWh|
|`sensor.techfine_cloud_总发电量`|总发电量|设备累计总发电量|kWh|
|`sensor.techfine_cloud_逆变器温度`|逆变器温度|逆变器内部散热片温度|°C|
|`sensor.techfine_cloud_调试状态`|调试状态|插件运行状态和错误信息|-|
---

### ⚠️ 免责声明 (Disclaimer)

- 本插件为非官方开发 (Unofficial)，仅供学习交流使用。

- 数据来源于四色光伏云平台，虽然 API 允许高频访问，但请合理使用。

- This integration is not affiliated with Techfine or SiSe Solar.

---

**Created by [windy]**
