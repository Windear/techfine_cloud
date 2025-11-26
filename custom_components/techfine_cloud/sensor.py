import logging
import hashlib
import hmac
import json
import uuid
import base64
import requests
from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    UnitOfPower, UnitOfElectricPotential, UnitOfElectricCurrent,
    UnitOfEnergy, PERCENTAGE, UnitOfTemperature
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.entity import DeviceInfo

# ======================== 配置项集中管理（头部统一配置）========================
_LOGGER = logging.getLogger(__name__)
DOMAIN = "techfine_cloud"

# 配置项键名（改为 DTUID，移除原 DeviceID）
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_DTU_ID = "dtu_id"  # 新增：用户输入的 DTUID（数字串，如 53676403221983325773）

# API 核心配置
APP_ID = "rBrTRfAPXz"
APP_SECRET = "CJbrtLtqFES62bJ3ZW7c"
AUTH_URL = "https://solar.siseli.com/apis/login/account"  # 登录接口
DTU_INFO_URL_TEMPLATE = "https://solar.siseli.com/apis/device/dtu/info?dtuDtuid={}"  # DTU信息接口（用于获取DeviceID）
DATA_URL_TEMPLATE = "https://solar.siseli.com/apis/deviceState/simple/state/latest/v1?deviceId={}&dataSource=1"  # 数据接口

# 数据刷新间隔（10秒/次）
UPDATE_INTERVAL_SECONDS = 10

# Token失效判定条件（精准匹配返回格式：code=9 + message=Token expired）
TOKEN_EXPIRED_CODE = 9
TOKEN_EXPIRED_MSG = "Token expired"
TOKEN_INVALID_HTTP_CODES = {401, 403}  # 补充HTTP状态码判定
# 兼容旧版本HA：手动定义HERTZ单位（避免导入错误）
HERTZ = "Hz"
# ==============================================================================

class TechfineAPI:
    def __init__(self, username, password, dtu_id):
        self.username = username
        self.raw_password = password
        self.dtu_id = dtu_id  # 用户输入的 DTUID
        self.device_id = None  # 自动获取的 DeviceID（从DTU接口解析）
        self.token = None  # 当前有效Token
        self.last_login_time = None  # 上次登录时间（用于日志追踪）
        self.last_debug_msg = "Initializing..."  # 调试信息

        # 固定请求头（模拟官方APP请求）
        self.headers = {
            "Content-Type": "application/json; charset=utf-8",
            "IOT-Open-AppID": APP_ID,
            "IOT-Time-Zone": "Asia/Shanghai",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

    def _generate_signature(self, params):
        """生成API签名（严格遵循官方HMAC-SHA256+MD5规则）"""
        try:
            # 1. 按key排序参数
            sorted_params = sorted(params.items(), key=lambda x: x[0])
            # 2. 拼接参数字符串
            raw_param_str = "&".join([f"{k}={v}" for k, v in sorted_params])
            # 3. Base64编码
            b64_encoded = base64.b64encode(raw_param_str.encode("utf-8")).decode("utf-8")
            # 4. HMAC-SHA256签名 + MD5小写
            hmac_obj = hmac.new(APP_SECRET.encode("utf-8"), b64_encoded.encode("utf-8"), hashlib.sha256)
            return hashlib.md5(hmac_obj.digest()).hexdigest().lower()
        except Exception as e:
            _LOGGER.error(f"签名生成失败: {str(e)}")
            return None

    def login(self):
        """登录获取Token（失败返回False，成功更新self.token）"""
        _LOGGER.debug(f"触发登录流程，用户名: {self.username}")
        try:
            # 1. 处理手机号格式（自动为11位手机号添加86-前缀）
            account = self.username
            if account.isdigit() and len(account) == 11 and not account.startswith("86-"):
                account = f"86-{account}"
            
            # 2. 密码MD5加密（官方接口要求）
            password_md5 = hashlib.md5(self.raw_password.encode("utf-8")).hexdigest().lower()
            payload = {"account": account, "password": password_md5}
            payload_str = json.dumps(payload, separators=(',', ':'))  # 紧凑JSON格式（避免空格影响签名）
            
            # 3. 生成签名所需参数
            nonce = str(uuid.uuid4()).replace("-", "")  # 随机字符串
            body_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest().lower()  # 请求体哈希
            sign_params = {
                "IOT-Open-AppID": APP_ID,
                "IOT-Open-Nonce": nonce,
                "IOT-Open-Body-Hash": body_hash
            }
            signature = self._generate_signature(sign_params)
            if not signature:
                self.last_debug_msg = "登录失败：签名生成失败"
                return False

            # 4. 构造登录请求头
            login_headers = self.headers.copy()
            login_headers.update({
                "IOT-Open-Nonce": nonce,
                "IOT-Open-Body-Hash": body_hash,
                "IOT-Open-Sign": signature
            })

            # 5. 发送登录请求（忽略SSL验证，适配部分网络环境）
            response = requests.post(
                AUTH_URL,
                data=payload_str,
                headers=login_headers,
                timeout=15,
                verify=False
            )
            response.raise_for_status()  # 抛出HTTP状态码异常（4xx/5xx）
            result = response.json()

            # 6. 解析登录结果（成功：code=0 + 返回accessToken）
            if result.get("code") == 0 and "accessToken" in result.get("data", {}):
                self.token = result["data"]["accessToken"]
                self.last_login_time = datetime.now()
                self.last_debug_msg = f"登录成功（Token前6位: {self.token[:6]}...）"
                _LOGGER.info(f"登录成功，Token有效期预计24小时，上次登录时间: {self.last_login_time.strftime('%Y-%m-%d %H:%M:%S')}")
                # 登录成功后，自动获取DeviceID
                if not self._fetch_device_id_from_dtu():
                    self.last_debug_msg = "登录成功，但获取DeviceID失败"
                    _LOGGER.error("登录成功，但无法通过DTUID获取DeviceID")
                    return False
                return True
            else:
                error_msg = result.get("message", "未知错误")
                self.last_debug_msg = f"登录失败：{error_msg}（code: {result.get('code')}）"
                _LOGGER.error(f"登录失败，接口返回: {json.dumps(result, ensure_ascii=False)}")
                return False

        except requests.exceptions.RequestException as e:
            # 网络异常（超时、连接失败等）
            self.last_debug_msg = f"登录网络错误：{str(e)}"
            _LOGGER.error(f"登录网络异常: {e}")
        except Exception as e:
            # 其他未知异常
            self.last_debug_msg = f"登录未知错误：{str(e)}"
            _LOGGER.error(f"登录异常: {e}", exc_info=True)
        return False

    def _fetch_device_id_from_dtu(self):
        """通过DTUID获取DeviceID（从 devicesAlreadyAdded 中提取第一个设备的id）"""
        _LOGGER.debug(f"开始通过DTUID获取DeviceID，DTUID: {self.dtu_id}")
        if not self.token:
            _LOGGER.error("获取DeviceID失败：无有效Token")
            return False

        # 构造DTU信息请求
        dtu_info_url = DTU_INFO_URL_TEMPLATE.format(self.dtu_id)
        dtu_headers = self.headers.copy()
        dtu_headers["iot-token"] = self.token

        try:
            response = requests.get(
                dtu_info_url,
                headers=dtu_headers,
                timeout=15,
                verify=False
            )
            response.raise_for_status()
            result = response.json()

            # 解析DTU接口返回
            if result.get("code") != 0:
                error_msg = result.get("message", "未知错误")
                _LOGGER.error(f"DTU信息接口返回异常：{error_msg}（code: {result.get('code')}）")
                return False

            # 提取devicesAlreadyAdded中的第一个设备id
            devices = result.get("data", {}).get("devicesAlreadyAdded", [])
            if not devices:
                _LOGGER.error(f"DTUID {self.dtu_id} 未关联任何设备（devicesAlreadyAdded为空）")
                return False

            # 取第一个已添加设备的id作为DeviceID
            self.device_id = devices[0]["id"]
            device_name = devices[0].get("name", "未知设备")
            _LOGGER.info(f"成功获取DeviceID：{self.device_id}（设备名称：{device_name}）")
            self.last_debug_msg = f"成功获取DeviceID：{self.device_id[:8]}..."
            return True

        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"获取DeviceID网络错误：{str(e)}")
        except Exception as e:
            _LOGGER.error(f"获取DeviceID解析异常：{str(e)}", exc_info=True)
        return False

    def fetch_device_data(self):
        """获取设备数据（核心逻辑：Token失效自动重登 + DeviceID校验）"""
        # 1. 无Token时直接触发登录（登录时会自动获取DeviceID）
        if not self.token:
            _LOGGER.warning("无有效Token，首次登录...")
            if not self.login():
                return {"_error": self.last_debug_msg}

        # 2. 校验DeviceID是否存在（防止获取失败）
        if not self.device_id:
            _LOGGER.warning("无有效DeviceID，尝试重新获取...")
            if not self._fetch_device_id_from_dtu():
                return {"_error": "DeviceID获取失败，请检查DTUID是否正确"}

        # 3. 构造数据请求参数
        data_url = DATA_URL_TEMPLATE.format(self.device_id)
        data_headers = self.headers.copy()
        data_headers["iot-token"] = self.token  # 携带Token

        try:
            # 4. 发送数据请求
            response = requests.get(
                data_url,
                headers=data_headers,
                timeout=15,
                verify=False
            )

            # 5. 解析响应（先处理JSON格式）
            try:
                result = response.json()
            except json.JSONDecodeError:
                self.last_debug_msg = f"数据接口返回非JSON格式：{response.text[:100]}"
                _LOGGER.error(f"数据接口返回格式异常: {response.text}")
                return {"_error": self.last_debug_msg}

            # 6. 精准判定Token失效（匹配 code=9 + message=Token expired）
            token_expired = False
            if result.get("code") == TOKEN_EXPIRED_CODE and result.get("message") == TOKEN_EXPIRED_MSG:
                token_expired = True
            elif response.status_code in TOKEN_INVALID_HTTP_CODES:
                # 补充HTTP状态码判定（如401/403）
                token_expired = True

            # 7. Token失效时自动重登并重新请求数据（重登时会自动刷新DeviceID）
            if token_expired:
                _LOGGER.warning(f"Token失效（code: {result.get('code')}, message: {result.get('message')}），触发自动重登...")
                if self.login():  # 重登成功（会自动重新获取DeviceID）
                    data_headers["iot-token"] = self.token  # 更新Token
                    # 重新发送数据请求
                    response = requests.get(
                        data_url,
                        headers=data_headers,
                        timeout=15,
                        verify=False
                    )
                    response.raise_for_status()
                    result = response.json()
                else:
                    # 重登失败返回错误
                    return {"_error": "Token失效，自动重登失败"}

            # 8. 解析有效数据（code=0 为成功）
            if result.get("code") == 0 and "fields" in result.get("data", {}):
                self.last_debug_msg = f"数据更新成功（{datetime.now().strftime('%H:%M:%S')}）"
                # 返回字段数据 + 调试信息
                return {
                    **result["data"]["fields"],
                    "_debug_msg": self.last_debug_msg,
                    "_raw_preview": json.dumps(result, ensure_ascii=False)[:300],  # 原始数据预览（截取前300字符）
                    "_device_id": self.device_id,  # 新增：在调试数据中携带DeviceID
                    "_dtu_id": self.dtu_id  # 新增：在调试数据中携带DTUID
                }
            else:
                # 数据接口返回异常（非Token失效）
                error_msg = result.get("message", "未知错误")
                self.last_debug_msg = f"数据获取失败：{error_msg}（code: {result.get('code')}）"
                _LOGGER.error(f"数据接口返回异常: {json.dumps(result, ensure_ascii=False)}")
                return {"_error": self.last_debug_msg}

        except requests.exceptions.RequestException as e:
            error_msg = f"数据请求异常：{str(e)}"
            _LOGGER.error(error_msg)
            return {"_error": error_msg}
        except Exception as e:
            error_msg = f"数据解析异常：{str(e)}"
            _LOGGER.error(error_msg, exc_info=True)
            return {"_error": error_msg}

async def async_setup_entry(hass, entry, async_add_entities):
    """Home Assistant集成入口（初始化传感器）"""
    # 1. 从配置中读取参数（改为读取DTUID）
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    dtu_id = entry.data[CONF_DTU_ID]

    # 校验DTUID格式（纯数字串，避免明显错误）
    if not dtu_id.isdigit():
        _LOGGER.error(f"DTUID格式错误：{dtu_id}（必须是纯数字串）")
        return

    # 2. 初始化API客户端（传入DTUID，而非DeviceID）
    api_client = TechfineAPI(username, password, dtu_id)

    # 3. 定义异步数据更新协调器（10秒刷新一次）
    async def async_update_data():
        """异步获取数据（适配HA异步架构）"""
        return await hass.async_add_executor_job(api_client.fetch_device_data)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"techfine_inverter_{dtu_id}",  # 协调器名称改为DTUID前缀
        update_method=async_update_data,
        update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS)  # 配置项中定义的10秒刷新
    )

    # 4. 首次刷新数据（启动时立即获取）
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as e:
        _LOGGER.warning(f"首次数据刷新失败: {str(e)}，将在{UPDATE_INTERVAL_SECONDS}秒后自动重试")

    # 5. 设备信息（用于HA设备列表显示，添加DTUID标识）
    device_info = DeviceInfo(
        identifiers={(DOMAIN, api_client.device_id or dtu_id)},  # 用DeviceID或DTUID作为唯一标识
        name=f"Techfine 光伏逆变器（DTU: {dtu_id[-8:]}）",  # 设备名称显示DTUID后8位（简洁）
        manufacturer="Techfine / SiSe Solar",
        model="混合式逆变器",
        configuration_url="https://solar.siseli.com",
        sw_version="1.4.0"  # 集成版本号（支持DTUID自动解析）
    )

    # ======================== 全字段传感器定义（按优先级排序）========================
    sensors = [
        # 一、核心发电量（用户最关注）
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "tqfDailyElectricityGeneration", "日发电量", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "tqfMonthlyElectricityGeneration", "月发电量", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "tqfYearlyElectricityGeneration", "年发电量", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "tqfTotalElectricityGeneration", "总发电量", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL),
        
        # 二、核心功率数据
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "pvPower", "PV功率", UnitOfPower.WATT, SensorDeviceClass.POWER),
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "generationPower", "发电功率", UnitOfPower.KILO_WATT, SensorDeviceClass.POWER),
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "outputActivePower", "输出有功功率", UnitOfPower.KILO_WATT, SensorDeviceClass.POWER),
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "mainsPower", "市电功率", UnitOfPower.KILO_WATT, SensorDeviceClass.POWER),
        
        # 三、电池核心数据
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "batteryCapacity", "电池容量", PERCENTAGE, SensorDeviceClass.BATTERY),
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "batteryVoltage", "电池电压", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE),
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "batteryChargingCurrent", "电池充电电流", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT),
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "batteryDischargeCurrent", "电池放电电流", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT),
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "batteryStatus", "电池状态", None, None),
        
        # 四、电网相关数据
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "acInputVoltage", "市电电压", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE),
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "mainsFrequency", "市电频率", HERTZ, None),
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "mainsCurrentFlowDirection", "市电电流流向", None, None),
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "gridConnectedCurrent", "并网电流", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT),
        
        # 五、输出相关数据
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "outputVoltage", "输出电压", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE),
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "outputFrequency", "输出频率", HERTZ, None),
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "outputApparentPower", "输出视在功率", "VA", None),
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "outputLoadPercent", "输出负载百分比", PERCENTAGE, None),
        
        # 六、设备状态数据
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "inverterTemperature", "逆变温度", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "transformerTemperature", "变压器温度", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "fan1Status", "风扇1状态", None, None),
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "fan2Status", "风扇2状态", None, None),
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "workingMode", "工作模式", None, None),
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "gridConnectionSign", "并网标志", None, None),
        
        # 七、设备信息数据
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "deviceType", "设备类型", None, None),
        TechfineSensor(coordinator, api_client.device_id or dtu_id, device_info, "softwareVersion", "软件版本", None, None),
        
        # 八、调试传感器（最后显示，用于问题排查，新增DTUID/DeviceID显示）
        TechfineDebugSensor(coordinator, api_client.device_id or dtu_id, device_info, "debug_status", "调试状态"),
    ]

    # 批量添加传感器到HA
    async_add_entities(sensors)

class TechfineSensor(SensorEntity):
    """通用传感器类（适配所有数据字段）"""
    def __init__(self, coordinator, device_unique_id, device_info, field_key, name, unit, device_class, state_class=None):
        self.coordinator = coordinator  # 数据协调器
        self._field_key = field_key  # 接口返回的字段名
        self._attr_unique_id = f"{DOMAIN}_{device_unique_id}_{field_key}"  # 唯一ID（避免重复）
        self._attr_has_entity_name = True  # 启用实体名称（HA 2023.12+要求）
        self._attr_name = name  # 传感器显示名称（中文）
        self._attr_native_unit_of_measurement = unit  # 单位
        self._attr_device_class = device_class  # 设备类别（用于HA图标自动匹配）
        self._attr_state_class = state_class  # 状态类别（累计型/即时型）
        self._attr_device_info = device_info  # 关联设备
        self._attr_should_poll = False  # 禁用主动轮询（使用协调器推送）

    @property
    def native_value(self):
        """获取传感器值（优先取value，非数值取valueDisplay）"""
        if not self.coordinator.data or "_error" in self.coordinator.data:
            return None
        
        # 获取字段数据（接口返回的fields字典）
        field_data = self.coordinator.data.get(self._field_key)
        if not isinstance(field_data, dict):
            return None
        
        # 优先获取数值型value，转换失败则取显示值
        value = field_data.get("value")
        try:
            # 尝试转换为浮点型（适配整数/小数）
            return float(value) if value is not None else None
        except (ValueError, TypeError):
            # 非数值类型（如状态字符串），返回显示值
            return field_data.get("valueDisplay", value)

    @property
    def available(self):
        """传感器可用性（无错误时可用）"""
        return self.coordinator.data and "_error" not in self.coordinator.data

    async def async_added_to_hass(self):
        """传感器添加到HA时，注册数据更新监听"""
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

class TechfineDebugSensor(SensorEntity):
    """调试传感器（显示集成运行状态，新增DTUID/DeviceID）"""
    def __init__(self, coordinator, device_unique_id, device_info, field_key, name):
        self.coordinator = coordinator
        self._attr_unique_id = f"{DOMAIN}_{device_unique_id}_{field_key}"
        self._attr_has_entity_name = True
        self._attr_name = name
        self._attr_icon = "mdi:bug"  # 调试图标
        self._attr_device_info = device_info
        self._attr_should_poll = False

    @property
    def native_value(self):
        """调试信息显示"""
        if not self.coordinator.data:
            return "初始化中..."
        data = self.coordinator.data
        if "_error" in data:
            return f"❌ {data['_error']}"
        return f"✅ {data.get('_debug_msg', '未知状态')}"

    @property
    def extra_state_attributes(self):
        """额外属性（显示DTUID、DeviceID、原始数据预览）"""
        if not self.coordinator.data:
            return {"说明": "集成初始化中，暂无数据"}
        data = self.coordinator.data
        return {
            "DTUID": data.get("_dtu_id", "未知"),
            "DeviceID": data.get("_device_id", "未知"),
            "原始数据预览": data.get("_raw_preview", "无"),
            "最后更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "刷新间隔": f"{UPDATE_INTERVAL_SECONDS}秒"
        }

    async def async_added_to_hass(self):
        """注册数据更新监听"""
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))