import logging
import hashlib
import hmac
import json
import uuid
import time
import requests
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfPower, UnitOfElectricPotential, UnitOfElectricCurrent, UnitOfEnergy, PERCENTAGE
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

DOMAIN = "techfine_cloud"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_DEVICE_ID = "device_id"

# 固定的 API 参数
APP_ID = "rBrTRfAPXz"
APP_SECRET = "CJbrtLtqFES62bJ3ZW7c"
BASE_URL = "https://solar.siseli.com/api"

class TechfineAPI:
    def __init__(self, username, password, device_id):
        self.username = username
        self.raw_password = password
        self.device_id = device_id
        self.token = None
        self.headers = {
            "Content-Type": "application/json; charset=utf-8",
            "IOT-Open-AppID": APP_ID,
            "IOT-Time-Zone": "Asia/Shanghai",
            "User-Agent": "HomeAssistant/TechfineIntegration"
        }

    def _get_sign(self, params):
        """计算 HMAC-SHA256 签名"""
        sorted_keys = sorted(params.keys())
        to_sign = "&".join([f"{k}={params[k]}" for k in sorted_keys])
        signature = hmac.new(APP_SECRET.encode('utf-8'), to_sign.encode('utf-8'), hashlib.sha256).hexdigest().lower()
        return signature

    def login(self):
        """登录获取 Token"""
        _LOGGER.debug("Attempting to login to Techfine Cloud...")
        url = f"{BASE_URL}/auth/login"
        
        # 1. 自动对密码进行 MD5 加密 (解决你的痛点)
        password_md5 = hashlib.md5(self.raw_password.encode('utf-8')).hexdigest().lower()
        
        payload = {
            "account": self.username,
            "password": password_md5,
            "client_id": "web"
        }
        # 生成紧凑 JSON 用于 Hash
        body_str = json.dumps(payload, separators=(',', ':'))
        
        nonce = str(uuid.uuid4()).replace('-', '')
        body_hash = hashlib.sha256(body_str.encode('utf-8')).hexdigest().lower()
        
        sign_params = {
            "IOT-Open-AppID": APP_ID,
            "IOT-Open-Nonce": nonce,
            "IOT-Open-Body-Hash": body_hash
        }
        sign = self._get_sign(sign_params)
        
        headers = self.headers.copy()
        headers.update({
            "IOT-Open-Nonce": nonce,
            "IOT-Open-Body-Hash": body_hash,
            "IOT-Open-Sign": sign
        })
        
        try:
            resp = requests.post(url, data=body_str, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 200:
                    self.token = data["result"]["token"]
                    _LOGGER.info("Techfine login successful.")
                    return True
            _LOGGER.error(f"Login failed: {resp.text}")
        except Exception as e:
            _LOGGER.error(f"Login exception: {e}")
        return False

    def get_data(self):
        """获取设备数据，如果 Token 失效自动重试"""
        if not self.token:
            if not self.login():
                raise UpdateFailed("Initial login failed")

        url = f"{BASE_URL}/device/detail?deviceId={self.device_id}"
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {self.token}"

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            
            # 如果 Token 过期 (通常 401 或 code!=200)，尝试重新登录一次
            if resp.status_code == 401 or (resp.status_code == 200 and resp.json().get("code") != 200):
                _LOGGER.warning("Token expired or invalid, re-logging in...")
                if self.login():
                    headers["Authorization"] = f"Bearer {self.token}"
                    resp = requests.get(url, headers=headers, timeout=10)
                else:
                    raise UpdateFailed("Re-login failed")

            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 200:
                    return data["result"]
            
            raise UpdateFailed(f"Error fetching data: {resp.text}")

        except Exception as e:
            raise UpdateFailed(f"Connection error: {e}")

async def async_setup_entry(hass, entry, async_add_entities):
    """Setup sensor platform."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    device_id = entry.data[CONF_DEVICE_ID]

    api = TechfineAPI(username, password, device_id)

    # 这里的 60 是刷新频率，单位秒。如果你想更快，可以改小，比如 30
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="techfine_sensor",
        update_method=lambda: hass.async_add_executor_job(api.get_data),
        update_interval=timedelta(seconds=60), 
    )

    await coordinator.async_config_entry_first_refresh()

    sensors = [
        TechfineSensor(coordinator, "power", "Power", UnitOfPower.WATT, SensorDeviceClass.POWER),
        TechfineSensor(coordinator, "voltage", "Grid Voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE),
        TechfineSensor(coordinator, "current", "Grid Current", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT),
        TechfineSensor(coordinator, "today_energy", "Today Energy", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
        TechfineSensor(coordinator, "total_energy", "Total Energy", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL),
        TechfineSensor(coordinator, "battery_soc", "Battery SoC", PERCENTAGE, SensorDeviceClass.BATTERY),
        TechfineSensor(coordinator, "battery_voltage", "Battery Voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE),
    ]

    async_add_entities(sensors)

class TechfineSensor(SensorEntity):
    """Representation of a Techfine Sensor."""
    
    def __init__(self, coordinator, key, name_suffix, unit, device_class, state_class=None):
        self.coordinator = coordinator
        self._key = key
        self._attr_name = f"Techfine {name_suffix}"
        self._attr_unique_id = f"{coordinator.data.get('id', 'unknown')}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        if state_class:
            self._attr_state_class = state_class

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(self._key)

    @property
    def should_poll(self):
        return False

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update the entity."""
        await self.coordinator.async_request_refresh()