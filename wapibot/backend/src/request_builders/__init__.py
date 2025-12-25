"""Request builders for call_api atomic node.

Request builders implement the RequestBuilder Protocol and generate
HTTP request configurations from BookingState.

IMPORTANT: For Frappe/WAPI APIs, use dedicated nodes instead:
- Frappe APIs: Use call_frappe.node with YawlitClient (NO request builders)
- WAPI: Use send_message.node with WAPIClient (NO request builders)

Request builders should ONLY be used for third-party APIs without dedicated clients:
- Weather APIs
- Maps/geocoding APIs
- Payment gateway webhooks
- SMS providers

Example (third-party API):
    def weather_request_builder(state):
        return {
            "method": "GET",
            "url": "https://api.weather.com/forecast",
            "params": {"city": state.get("location")}
        }

    await call_api.node(state, weather_request_builder, "weather_data")
"""

__all__ = []
