#!/usr/bin/env python3
"""Seed DuckDB with mock observations + insights for UI preview."""

import random
from datetime import UTC, datetime, timedelta

import duckdb

from app.storage.migrations import MIGRATIONS

random.seed(42)

DB = "data/observatory.duckdb"
NOW = datetime.now(UTC)
OBS_COLS = "id, timestamp, source, category, entity, features, metadata, version"
INS_COLS = "id, title, description, source, confidence, timestamp, metadata"


def _id(prefix: str, n: int) -> str:
    return f"{prefix}_{n:04d}"


def _ts(days_ago: float) -> str:
    return (NOW - timedelta(days=days_ago)).isoformat()


def _random_features(keys: list[str], ranges: list[tuple[float, float]]) -> dict:
    return {k: round(random.uniform(lo, hi), 1) for k, (lo, hi) in zip(keys, ranges)}


def _run_migrations(con: duckdb.DuckDBPyConnection) -> None:
    for _, _, sql in MIGRATIONS:
        con.execute(sql)


def seed_observations(con: duckdb.DuckDBPyConnection) -> int:
    rows: list[list] = []
    n = 0

    for day in range(14):
        rows.append(
            [
                _id("fitbit", n), _ts(day), "fitbit", "health", "sleep",
                _random_features(["duration_h", "deep_pct", "rem_pct"], [(5, 9), (10, 30), (15, 30)]),
                {"device": "Charge 6"}, 1,
            ]
        )
        n += 1
        rows.append(
            [
                _id("fitbit", n), _ts(day), "fitbit", "health", "steps",
                _random_features(["count"], [(3000, 12000)]),
                {"goal": 10000}, 1,
            ]
        )
        n += 1
        rows.append(
            [
                _id("fitbit", n), _ts(day), "fitbit", "health", "heart_rate",
                _random_features(["resting_bpm", "max_bpm"], [(52, 68), (120, 170)]),
                {}, 1,
            ]
        )
        n += 1
        rows.append(
            [
                _id("fitbit", n), _ts(day), "fitbit", "health", "hrv",
                _random_features(["rmssd"], [(20, 65)]),
                {}, 1,
            ]
        )
        n += 1
        rows.append(
            [
                _id("fitbit", n), _ts(day + 0.5), "fitbit", "activity", "workout",
                _random_features(["duration_min", "calories"], [(20, 90), (100, 500)]),
                {"type": random.choice(["run", "walk", "weights", "yoga"])}, 1,
            ]
        )
        n += 1

    for day in range(14):
        for _ in range(random.randint(0, 4)):
            rows.append(
                [
                    _id("cal", n), _ts(day + random.random()), "calendar", "events", "meeting",
                    _random_features(["duration_min", "attendees"], [(15, 120), (1, 12)]),
                    {"title": random.choice(["Standup", "Sprint Review", "1:1", "Design Review", "Workshop"])}, 1,
                ]
            )
            n += 1

    genres = ["indie", "electronic", "jazz", "classical", "rock", "hip-hop"]
    for day in range(14):
        track_count = random.randint(3, 15)
        total_min = round(sum(random.uniform(2, 7) for _ in range(track_count)), 1)
        rows.append(
            [
                _id("spot", n), _ts(day), "spotify", "music", "listening",
                {"track_count": track_count, "total_minutes": total_min, "unique_artists": random.randint(1, 8)},
                {"top_genre": random.choice(genres), "top_artist": random.choice(["Artist A", "Artist B", "Artist C", "Artist D"])}, 1,
            ]
        )
        n += 1

    conditions = ["clear", "cloudy", "rain", "drizzle", "overcast"]
    for day in range(14):
        rows.append(
            [
                _id("wthr", n), _ts(day), "weather", "climate", "daily",
                _random_features(["temp_high_c", "temp_low_c", "humidity_pct", "wind_kmh"], [(5, 35), (-2, 20), (30, 95), (0, 40)]),
                {"condition": random.choice(conditions), "uv_index": round(random.uniform(0, 8), 1)}, 1,
            ]
        )
        n += 1

    statuses = ["reading", "finished"]
    for day in range(14):
        if random.random() < 0.5:
            rows.append(
                [
                    _id("book", n), _ts(day), "hardcover", "reading", "book",
                    _random_features(["pages_read", "progress_pct"], [(5, 80), (1, 15)]),
                    {"title": random.choice(["Dune", "Pattern Recognition", "Neuromancer", "The Peripheral", "Snow Crash"]),
                     "status": random.choice(statuses)}, 1,
                ]
            )
            n += 1

    for day in range(14):
        for hour in [8, 12, 18, 22]:
            rows.append(
                [
                    _id("ha", n), _ts(day + hour / 24), "homeassistant", "home", "indoor_temp",
                    _random_features(["temperature_c", "humidity_pct"], [(18, 26), (35, 65)]),
                    {"room": random.choice(["living_room", "bedroom", "office"])}, 1,
                ]
            )
            n += 1
        rows.append(
            [
                _id("ha", n), _ts(day), "homeassistant", "home", "energy",
                _random_features(["kwh"], [(5, 30)]),
                {}, 1,
            ]
        )
        n += 1

    con.executemany(
        f"INSERT INTO observations ({OBS_COLS}) VALUES ({','.join(['?'] * 8)})",
        rows,
    )
    return n


def seed_insights(con: duckdb.DuckDBPyConnection) -> int:
    insights = [
        ["ins_0000", "Sleep quality improving", "Your deep sleep percentage has increased 12% over the last week, correlating with lower evening heart rate.",
         "llm", 0.87, _ts(0.5), '{"llm_raw": "mock"}'],
        ["ins_0001", "Step count dipping on meeting days", "Days with 4+ calendar meetings average 2,100 fewer steps. Consider walking meetings.",
         "llm", 0.82, _ts(0.5), '{"llm_raw": "mock"}'],
        ["ins_0002", "Music preference shift detected", "Indie genre share dropped from 45% to 28% this week. Electronic up 15 percentage points.",
         "llm", 0.74, _ts(1.0), '{"llm_raw": "mock"}'],
        ["ins_0003", "Reading pace consistent", "You've averaged 42 pages/day across 3 active books. Current pace: 2 books/month.",
         "llm", 0.79, _ts(1.5), '{"llm_raw": "mock"}'],
        ["ins_0004", "Home energy correlates with weather", "Energy usage spikes 40% on days below 5°C. Consistent with heating patterns.",
         "llm", 0.91, _ts(2.0), '{"llm_raw": "mock"}'],
        ["ins_0005", "Morning HRV trending up", "Your 7-day RMSSD average increased from 34ms to 41ms, suggesting improved recovery.",
         "llm", 0.85, _ts(2.5), '{"llm_raw": "mock"}'],
        ["ins_0006", "Workout consistency slipping", "5 workouts this week vs 8 last week. Wednesday is your most skipped day.",
         "llm", 0.71, _ts(3.0), '{"llm_raw": "mock"}'],
    ]
    con.executemany(
        f"INSERT INTO insights ({INS_COLS}) VALUES ({','.join(['?'] * 7)})",
        insights,
    )
    return len(insights)


def main() -> None:
    con = duckdb.connect(DB)
    con.execute("DROP TABLE IF EXISTS observations")
    con.execute("DROP TABLE IF EXISTS insights")
    con.execute("DROP TABLE IF EXISTS features")
    con.execute("DROP TABLE IF EXISTS _migrations")
    _run_migrations(con)
    obs = seed_observations(con)
    ins = seed_insights(con)
    con.commit()
    con.close()
    print(f"Seeded {obs} observations and {ins} insights into {DB}")


if __name__ == "__main__":
    main()
