import voluptuous as vol
from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv

DOMAIN = "techfine_cloud"

class TechfineConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Techfine Cloud."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # 使用 Device ID 作为唯一的标识符，防止重复添加
            await self.async_set_unique_id(user_input["device_id"])
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(
                title=f"Inverter {user_input['device_id']}",
                data=user_input
            )

        # 定义表单结构
        data_schema = vol.Schema({
            vol.Required("username"): str,
            vol.Required("password"): str,
            vol.Required("device_id"): str,
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )