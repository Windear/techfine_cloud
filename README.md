# Techfine Cloud (SiSe) 光伏逆变器 Home Assistant 集成

这是一个用于 Home Assistant 的第三方集成，可实现 Techfine/SiSe 光伏逆变器的**数据实时同步、状态监控、历史数据追踪**等功能，全程自动化运行，无需人工干预。

## 功能特点

1. **全量数据同步**：覆盖发电量（日/月/年/总）、功率、电池状态、电网参数、设备状态等核心数据

2. **自动 Token 管理**：登录 Token 失效时自动重新登录，无需人工操作

3. **高频数据刷新**：默认 10 秒刷新一次，实时反馈设备状态

4. **调试友好**：内置调试传感器，便于问题排查

5. **兼容广泛**：适配新旧版本 Home Assistant，支持 11 位手机号自动添加 86-前缀

## 前置条件

1. 拥有 Techfine/SiSe 光伏逆变器及对应的账号密码（需能正常登录官方 APP/网页）

2. Home Assistant 版本 ≥ 2022.11（旧版本可尝试，不保证兼容）

3. 网络可访问逆变器官方服务器（`https://solar.siseli.com`）

## 安装方法

### 方法 1：通过 HACS 安装（推荐）

1. 打开 Home Assistant → HACS → 集成 → 右上角「三个点」→ 自定义仓库

2. 仓库 URL：`https://github.com/Windear/techfine_cloud`（替换为你的仓库地址）

3. 类别：`Integration` → 点击「添加」

4. 等待仓库加载完成后，搜索「Techfine Cloud (SiSe)」→ 点击「下载」

5. 下载完成后，重启 Home Assistant

### 方法 2：手动安装

1. 下载本项目最新版本的 [ZIP 压缩包](https://github.com/Windear/techfine_cloud/archive/refs/heads/main.zip)

2. 解压后，将 `techfine_cloud` 文件夹复制到 Home Assistant 的 `config/custom_components/` 目录下

3. 重启 Home Assistant

## 配置步骤

1. 重启完成后，进入 Home Assistant → 设置 → 设备与服务 → 集成 → 右上角「添加集成」

2. 搜索「Techfine Cloud (SiSe)」并选择

3. 按照引导输入以下信息：

    - 用户名：登录官方 APP/网页的账号（通常是手机号）

    - 密码：登录密码

    - 设备 ID：逆变器的设备 ID（可在官方 APP/网页的设备详情中查看）

4. 点击「提交」，集成将自动完成登录和数据同步

5. 配置成功后，可在「设备与服务」中查看新增的设备及传感器

## 传感器列表（按优先级排序）

|传感器名称|实体 ID 前缀|单位|说明|
|---|---|---|---|
|日发电量|`sensor.techfine_光伏逆变器_日发电量`|kWh|当日累计发电量|
|月发电量|`sensor.techfine_光伏逆变器_月发电量`|kWh|当月累计发电量|
|年发电量|`sensor.techfine_光伏逆变器_年发电量`|kWh|当年累计发电量|
|总发电量|`sensor.techfine_光伏逆变器_总发电量`|kWh|设备累计总发电量|
|PV 功率|`sensor.techfine_光伏逆变器_pv功率`|W|光伏板实时功率|
|发电功率|`sensor.techfine_光伏逆变器_发电功率`|kW|设备总发电功率|
|输出有功功率|`sensor.techfine_光伏逆变器_输出有功功率`|kW|向电网输出的有功功率|
|市电功率|`sensor.techfine_光伏逆变器_市电功率`|kW|电网输入/输出功率（负值为输入）|
|电池容量|`sensor.techfine_光伏逆变器_电池容量`|%|储能电池剩余电量|
|电池电压|`sensor.techfine_光伏逆变器_电池电压`|V|电池实时电压|
|电池充电电流|`sensor.techfine_光伏逆变器_电池充电电流`|A|电池充电电流|
|电池放电电流|`sensor.techfine_光伏逆变器_电池放电电流`|A|电池放电电流|
|市电电压|`sensor.techfine_光伏逆变器_市电电压`|V|电网输入电压|
|市电频率|`sensor.techfine_光伏逆变器_市电频率`|Hz|电网频率|
|逆变温度|`sensor.techfine_光伏逆变器_逆变温度`|°C|逆变器核心温度|
|变压器温度|`sensor.techfine_光伏逆变器_变压器温度`|°C|变压器温度|
|工作模式|`sensor.techfine_光伏逆变器_工作模式`|-|设备当前工作模式（如：并网发电、储能充电）|
|并网标志|`sensor.techfine_光伏逆变器_并网标志`|-|并网状态（如：已并网、未并网）|
|调试状态|`sensor.techfine_光伏逆变器_调试状态`|-|集成运行状态（用于问题排查）|
## 常见问题排查

### 1. 集成添加失败，提示「登录失败」

- 检查用户名/密码是否正确（注意手机号是否需要带国家码）

- 确认设备 ID 是否正确（可在官方 APP 中复制）

- 检查网络是否能访问 `https://solar.siseli.com`（可尝试 ping 测试）

### 2. 传感器显示「不可用」

- 查看「调试状态」传感器，获取具体错误信息

- 检查逆变器是否在线（官方 APP 中确认）

- 确认网络通畅，无防火墙拦截请求

### 3. 数据不更新

- 查看 HA 日志（设置 → 系统 → 日志），搜索「techfine_cloud」查看报错

- 确认 Token 未失效（集成会自动重登，无需手动操作）

- 尝试重启集成（设备与服务 → Techfine Cloud → 右上角「三个点」→ 重新加载）

### 4. 报错「SSL 验证失败」

- 集成已默认关闭 SSL 验证，若仍报错，可检查网络环境（如：代理、VPN）

## 自定义配置（可选）

若需修改默认配置（如刷新间隔），可在 `config/custom_components/techfine_cloud/sensor.py` 头部修改以下参数：

```Python
# 数据刷新间隔（默认10秒，最小可设5秒）
UPDATE_INTERVAL_SECONDS = 10

# Token失效判定条件（无需修改）
TOKEN_EXPIRED_CODE = 9
TOKEN_EXPIRED_MSG = "Token expired"

```

修改后需重启 Home Assistant 生效。

## 日志查看

若需排查问题，可在 `config/configuration.yaml` 中添加日志配置，获取详细运行日志：

```YAML
logger:
  default: warning
  logs:
    custom_components.techfine_cloud: debug

```

重启 HA 后，可在「设置 → 系统 → 日志」中查看详细输出。

## 免责声明

1. 本集成是第三方非官方工具，仅用于数据同步，不涉及设备控制

2. 使用本集成前，请确保已了解官方服务条款，避免违规操作

3. 作者不对因使用本集成导致的设备故障、数据丢失、服务封禁等问题负责

4. 集成仅获取公开的设备数据，不会存储用户账号密码（密码仅用于登录官方服务器）

## 贡献代码

欢迎提交 PR 或 Issue 改进本集成：

- 提交 Issue：描述问题现象、HA 版本、报错日志

- 提交 PR：请遵循 Home Assistant 集成开发规范，确保代码风格一致

## 联系作者

若有问题或建议，可通过以下方式联系：

- GitHub Issue：[点击提交](https://github.com/Windear/techfine_cloud/issues)

- 邮箱：[your-email@example.com](bob23456@163.com)

---

**更新日志**

- v1.2.0：全字段覆盖，优化传感器排序，添加调试传感器

- v1.1.0：实现 Token 自动重登，优化登录逻辑

- v1.0.0：初始版本，支持核心数据同步
