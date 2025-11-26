import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

# 配置项键名（与 sensor.py 保持一致）
DOMAIN = "techfine_cloud"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_DTU_ID = "dtu_id"

_LOGGER = logging.getLogger(__name__)

# 配置表单Schema（优化提示文字和默认值）
STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_USERNAME, description={"suggested_value": "", "description": "登录官方APP的账号（通常是手机号）"}): str,
    vol.Required(CONF_PASSWORD, description={"suggested_value": "", "description": "登录官方APP的密码"}): str,
    vol.Required(CONF_DTU_ID, description={"suggested_value": "", "description": "APP中设备详情的DTUID（纯数字串）"}): str,
})

async def validate_input(hass: HomeAssistant, data: dict) -> dict:
    """验证用户输入的有效性（避免明显错误）"""
    dtu_id = data[CONF_DTU_ID]
    username = data[CONF_USERNAME]
    password = data[CONF_PASSWORD]

    # 1. DTUID必须是纯数字串
    if not dtu_id.isdigit():
        raise InvalidDTUId("DTUID必须是纯数字串（无空格、特殊字符）")
    
    # 2. DTUID长度校验（15-25位，覆盖常见场景）
    if len(dtu_id) < 15 or len(dtu_id) > 25:
        _LOGGER.warning(f"DTUID长度异常（{len(dtu_id)}位），请用户确认是否正确")

    # 3. 用户名/密码不能为空
    if not username or not password:
        raise EmptyCredentials("用户名或密码不能为空")

    # 返回配置标题（显示DTUID后8位，简洁易识别）
    return {"title": f"Techfine逆变器（DTU:{dtu_id[-8:]}）"}

class TechfineConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Techfine Cloud."""
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL  # 标记为云轮询模式

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # 验证输入数据
                info = await validate_input(self.hass, user_input)
                
                # 按DTUID去重（避免重复添加同一设备）
                await self.async_set_unique_id(user_input[CONF_DTU_ID])
                self._abort_if_unique_id_configured()

                # 创建配置条目
                return self.async_create_entry(
                    title=info["title"],
                    data=user_input
                )
            except InvalidDTUId:
                errors["base"] = "invalid_dtu_id"
                _LOGGER.error(f"DTUID格式错误：{user_input[CONF_DTU_ID]}（非纯数字）")
            except EmptyCredentials:
                errors["base"] = "empty_credentials"
                _LOGGER.error("用户名或密码为空")
            except Exception as e:
                errors["base"] = "unknown"
                _LOGGER.error(f"配置失败：{str(e)}", exc_info=True)

        # 显示配置表单（带错误提示和指引）
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "guide": "DTUID在官方APP「设备详情」中查找（纯数字串，长度15-25位）",
                "example": "示例：53676403221983325773"
            }
        )

    @callback
    def async_get_options_flow(self, config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """支持后续修改配置（用户名、密码、DTUID）"""
        return OptionsFlow(config_entry)

class OptionsFlow(config_entries.OptionsFlow):
    """配置修改流程"""
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """修改配置的初始化步骤"""
        errors: dict[str, str] = {}
        current_data = self.config_entry.data  # 当前已保存的配置

        if user_input is not None:
            try:
                # 重新验证修改后的输入
                await validate_input(self.hass, user_input)
                # 更新配置条目
                self.hass.config_entries.async_update_entry(self.config_entry, data=user_input)
                return self.async_create_entry(title="", data={})
            except InvalidDTUId:
                errors["base"] = "invalid_dtu_id"
            except EmptyCredentials:
                errors["base"] = "empty_credentials"
            except Exception as e:
                errors["base"] = "unknown"
                _LOGGER.error(f"修改配置失败：{str(e)}")

        # 显示修改表单（默认填充当前配置）
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME, default=current_data.get(CONF_USERNAME)): str,
                vol.Required(CONF_PASSWORD, default=current_data.get(CONF_PASSWORD)): str,
                vol.Required(CONF_DTU_ID, default=current_data.get(CONF_DTU_ID)): str,
            }),
            errors=errors,
            description_placeholders={
                "guide": "DTUID在官方APP「设备详情」中查找（纯数字串，长度15-25位）",
                "example": "示例：53676403221983325773"
            }
        )

# 自定义异常类（明确错误类型）
class InvalidDTUId(HomeAssistantError):
    """DTUID格式无效"""
    pass

class EmptyCredentials(HomeAssistantError):
    """用户名或密码为空"""
    pass