from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class IntegrationField:
    key: str
    label: str
    type: Literal["string", "password", "number", "select", "url"] = "string"
    placeholder: str = ""
    options: list[str] | None = None
    required: bool = False


@dataclass
class IntegrationDef:
    source: str
    label: str
    auth_type: Literal["api_key", "oauth", "url_token"]
    fields: list[IntegrationField] = field(default_factory=list)
    doc_url: str = ""
    oauth_scopes: str = ""


INTEGRATION_DEFINITIONS: list[IntegrationDef] = [
    IntegrationDef(
        source="weather",
        label="OpenWeatherMap",
        auth_type="api_key",
        doc_url="https://home.openweathermap.org/api_keys",
        fields=[
            IntegrationField(key="api_key", label="API Key", type="password", required=True),
            IntegrationField(key="lat", label="Latitude", type="number", placeholder="51.5"),
            IntegrationField(key="lon", label="Longitude", type="number", placeholder="-0.12"),
            IntegrationField(
                key="units",
                label="Units",
                type="select",
                options=["metric", "imperial", "standard"],
            ),
        ],
    ),
    IntegrationDef(
        source="hardcover",
        label="Hardcover",
        auth_type="api_key",
        doc_url="https://hardcover.app/account/api",
        fields=[
            IntegrationField(key="api_key", label="API Key", type="password", required=True),
        ],
    ),
    IntegrationDef(
        source="homeassistant",
        label="Home Assistant",
        auth_type="url_token",
        doc_url="https://developers.home-assistant.io/docs/api/rest/",
        fields=[
            IntegrationField(
                key="url", label="Instance URL", type="url",
                placeholder="http://homeassistant.local:8123", required=True,
            ),
            IntegrationField(key="token", label="Long-Lived Token", type="password", required=True),
        ],
    ),
    IntegrationDef(
        source="google_health",
        label="Google Health (Fitness)",
        auth_type="oauth",
        doc_url="https://console.cloud.google.com/apis/credentials",
        oauth_scopes=(
            "https://www.googleapis.com/auth/fitness.activity.read"
            " https://www.googleapis.com/auth/fitness.body.read"
            " https://www.googleapis.com/auth/fitness.heart_rate.read"
            " https://www.googleapis.com/auth/fitness.sleep.read"
        ),
        fields=[
            IntegrationField(key="client_id", label="Client ID", required=True),
            IntegrationField(
                key="client_secret", label="Client Secret",
                type="password", required=True,
            ),
        ],
    ),
    IntegrationDef(
        source="calendar",
        label="Google Calendar",
        auth_type="oauth",
        doc_url="https://console.cloud.google.com/apis/credentials",
        oauth_scopes="https://www.googleapis.com/auth/calendar.events.readonly",
        fields=[
            IntegrationField(
                key="client_id",
                label="Client ID (shared with Google Health)",
                required=False,
            ),
            IntegrationField(
                key="client_secret", label="Client Secret",
                type="password", required=False,
            ),
        ],
    ),
    IntegrationDef(
        source="spotify",
        label="Spotify",
        auth_type="oauth",
        doc_url="https://developer.spotify.com/dashboard",
        oauth_scopes="user-read-recently-played user-read-currently-playing",
        fields=[
            IntegrationField(key="client_id", label="Client ID", required=True),
            IntegrationField(
                key="client_secret", label="Client Secret",
                type="password", required=True,
            ),
        ],
    ),
]
