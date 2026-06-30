MIGRATIONS: list[tuple[int, str, str]] = [
    (
        1,
        "Create observations and insights tables",
        """
        CREATE TABLE IF NOT EXISTS observations (
            id VARCHAR PRIMARY KEY,
            timestamp TIMESTAMP WITH TIME ZONE,
            source VARCHAR,
            category VARCHAR,
            entity VARCHAR,
            features JSON,
            metadata JSON,
            version INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS insights (
            id VARCHAR PRIMARY KEY,
            title VARCHAR,
            description VARCHAR,
            source VARCHAR,
            confidence DOUBLE,
            timestamp TIMESTAMP WITH TIME ZONE,
            metadata JSON
        );

        CREATE INDEX IF NOT EXISTS idx_observations_source
            ON observations (source);

        CREATE INDEX IF NOT EXISTS idx_observations_timestamp
            ON observations (timestamp);

        CREATE INDEX IF NOT EXISTS idx_observations_entity
            ON observations (entity);
        """,
    ),
    (
        2,
        "Add features table for normalized feature storage",
        """
        CREATE TABLE IF NOT EXISTS features (
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            value VARCHAR NOT NULL,
            observation_id VARCHAR NOT NULL,
            source VARCHAR NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_features_observation_id
            ON features (observation_id);

        CREATE INDEX IF NOT EXISTS idx_features_name
            ON features (name);
        """,
    ),
]
