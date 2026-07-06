from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.collectors.base import CollectorCapability, CollectorInput
from app.collectors.http import HttpClient
from app.config import settings
from app.schemas import ObservationCreate


class WeatherCollector(CollectorCapability):
    collector_source = "weather"
    collector_category = "environment"

    def __init__(self, repository: Any, **config: Any) -> None:
        super().__init__(repository, **config)
        api_key = settings.weather_api_key
        self._client = HttpClient(
            base_url="https://api.openweathermap.org/data/2.5",
            timeout=15.0,
        )
        self._api_key = api_key
        self._lat = settings.weather_lat
        self._lon = settings.weather_lon
        self._units = settings.weather_units

    def collect(self, _payload: CollectorInput) -> list[ObservationCreate]:
        now = datetime.now(UTC)

        current = self._client.get(
            "/weather",
            params={
                "lat": self._lat,
                "lon": self._lon,
                "units": self._units,
                "appid": self._api_key,
            },
        )
        forecast = self._client.get(
            "/forecast",
            params={
                "lat": self._lat,
                "lon": self._lon,
                "units": self._units,
                "appid": self._api_key,
                "cnt": 8,
            },
        )

        observations: list[ObservationCreate] = []

        observations.append(
            ObservationCreate(
                timestamp=now,
                source="weather",
                category="environment",
                entity="current_conditions",
                features={
                    "temperature": current.get("main", {}).get("temp"),
                    "feels_like": current.get("main", {}).get("feels_like"),
                    "humidity": current.get("main", {}).get("humidity"),
                    "pressure": current.get("main", {}).get("pressure"),
                    "wind_speed": current.get("wind", {}).get("speed"),
                    "cloud_cover": current.get("clouds", {}).get("all"),
                    "visibility": current.get("visibility"),
                    "weather_code": current.get("weather", [{}])[0].get("id"),
                },
                metadata={
                    "city": current.get("name"),
                    "country": current.get("sys", {}).get("country"),
                    "sunrise": current.get("sys", {}).get("sunrise"),
                    "sunset": current.get("sys", {}).get("sunset"),
                },
            )
        )

        forecast_list = forecast.get("list", [])
        if forecast_list:
            daily: dict[str, list[float]] = {}
            for entry in forecast_list:
                dt = datetime.fromtimestamp(entry["dt"], tz=UTC)
                day_key = dt.strftime("%Y-%m-%d")
                if day_key not in daily:
                    daily[day_key] = []
                daily[day_key].append(entry["main"]["temp"])

            for day_key, temps in daily.items():
                observations.append(
                    ObservationCreate(
                        timestamp=datetime.fromisoformat(day_key),
                        source="weather",
                        category="environment",
                        entity="forecast",
                        features={
                            "high": max(temps),
                            "low": min(temps),
                            "avg": sum(temps) / len(temps),
                            "samples": len(temps),
                        },
                        metadata={"date": day_key},
                    )
                )

        return observations
