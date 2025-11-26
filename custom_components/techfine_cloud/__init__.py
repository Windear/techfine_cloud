import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady

# 定义域名
DOMAIN = "techfine_cloud"
# 定义我们要加载的平台（这里是 sensor）
PLATFORMS = ["sensor"]

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Techfine Cloud from a config entry."""
    # 创建数据存储空间
    hass.data.setdefault(DOMAIN, {})
    
    # 告诉 HA 去加载 sensor.py
    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception as e:
        _LOGGER.error(f"Failed to forward entry setups: {e}")
        raise ConfigEntryNotReady from e
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # 卸载时清理资源
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)