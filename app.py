import json
import logging
import threading
import time

import requests
from flask import Flask, jsonify, request

from config import Config
from utils.fallback_manager import FallbackManager

app = Flask(__name__)

fallback_manager = FallbackManager()

# Global health state cache
_health_state = {
    "status": "unknown",
    "current_provider": Config.AI_MODEL_PROVIDER,
    "current_model": Config.AI_MODEL_NAME,
    "ready_providers": 0,
    "total_providers": 0,
    "provider_details": {},
    "last_updated": None,
    "error": None,
}

# Set up logging
log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(level=log_level)

# Validate configuration on startup
try:
    Config.validate_provider_config()
    app.logger.info(
        "Using AI provider: %s with model: %s",
        Config.AI_MODEL_PROVIDER,
        Config.AI_MODEL_NAME,
    )
except ValueError as e:
    app.logger.error(f"Configuration error: {e}")
    raise


def refresh_provider_status():
    """Update global health state with current provider status."""
    global _health_state
    try:
        provider_status = fallback_manager.get_provider_status()
        ready_providers = sum(
            1 for status in provider_status.values() if status.get("ready", False)
        )

        _health_state = {
            **_health_state,
            "status": "healthy" if ready_providers > 0 else "degraded",
            "ready_providers": ready_providers,
            "total_providers": len(provider_status),
            "provider_details": provider_status,
            "last_updated": time.time(),
            "error": None,
        }
    except Exception as e:
        _health_state = {
            **_health_state,
            "status": "unhealthy",
            "ready_providers": 0,
            "total_providers": 0,
            "provider_details": {},
            "last_updated": time.time(),
            "error": str(e),
        }


def health_checker_loop():
    """Background thread that periodically refreshes provider status."""
    while True:
        refresh_provider_status()
        time.sleep(Config.HEALTH_CHECK_INTERVAL)


# Start background health checker thread
threading.Thread(target=health_checker_loop, daemon=True).start()


@app.route("/alert", methods=["POST"])
def receive_alert():
    try:
        # Get the JSON payload from the request
        alert_data = request.get_json()

        if alert_data is None:
            return (
                jsonify(
                    {"status": "error", "message": "Request body must be valid JSON"}
                ),
                400,
            )

        # Type narrow for type checker
        assert isinstance(alert_data, dict)

        # Log the received alert data for debugging purposes
        app.logger.info(f"Alert received: {alert_data}")

        # Use fallback manager for robust AI analysis
        # fallback_manager = FallbackManager()
        analysis_result = fallback_manager.analyze_with_fallback(alert_data)

        if not analysis_result["success"]:
            app.logger.error(f"All AI providers failed: {analysis_result['error']}")
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": analysis_result["error"],
                        "providers_tried": analysis_result.get("providers_tried", []),
                    }
                ),
                500,
            )

        analysis_content = analysis_result["analysis"]
        provider_used = analysis_result["provider_used"]
        fallback_used = analysis_result["fallback_used"]

        if fallback_used:
            app.logger.warning(
                f"Primary provider failed, used fallback: {provider_used}"
            )
        else:
            app.logger.info(
                f"Analysis completed with primary provider: {provider_used}"
            )

        print(analysis_content)

        # Format the message for Discord
        fallback_indicator = " (FALLBACK)" if fallback_used else ""
        discord_message = {
            "content": (
                f"**Alert Analysis** ({provider_used}{fallback_indicator}):\n"
                f"{analysis_content}\n"
                "** Please check your application to reduce the logs**"
            )
        }

        # Send the analysis to the Discord webhook
        try:
            discord_response = requests.post(
                Config.DISCORD_WEBHOOK_URL,
                headers={"Content-Type": "application/json"},
                data=json.dumps(discord_message),
                timeout=30,
            )

            # Check if the Discord webhook message was sent successfully
            if discord_response.status_code != 204:
                error_msg = (
                    f"Discord webhook error: {discord_response.status_code} - "
                    f"{discord_response.text}"
                )
                app.logger.error(error_msg)
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "Failed to send message to Discord",
                        }
                    ),
                    500,
                )

            app.logger.info("Discord notification sent successfully")

        except requests.exceptions.RequestException as e:
            app.logger.error(f"Discord webhook request failed: {e}")
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Failed to send Discord notification: {str(e)}",
                    }
                ),
                500,
            )

        # Send a JSON response back to acknowledge receipt of the alert
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Alert received and processed",
                    "provider": provider_used,
                    "fallback_used": fallback_used,
                    "model": analysis_result["model_used"],
                }
            ),
            200,
        )

    except Exception as e:
        app.logger.error(f"Error processing alert: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint with cached provider information."""
    status = _health_state["status"]
    status_code = 503 if status == "unhealthy" else 200

    return jsonify(_health_state), status_code


@app.get("/live")
def live():
    return {"status": "up"}


@app.get("/status")
def status():
    try:
        # fallback_manager = FallbackManager()
        provider_status = fallback_manager.get_provider_status()
        ready_providers = sum(
            1 for status in provider_status.values() if status.get("ready", False)
        )
        return (
            jsonify(
                {
                    "status": "healthy" if ready_providers > 0 else "degraded",
                    "current_provider": Config.AI_MODEL_PROVIDER,
                    "current_model": Config.AI_MODEL_NAME,
                    "ready_providers": ready_providers,
                    "total_providers": len(provider_status),
                    "provider_details": provider_status,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 50


if __name__ == "__main__":
    app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT)
