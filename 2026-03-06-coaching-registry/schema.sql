-- Conferences: canonical list of athletic conferences.
CREATE TABLE IF NOT EXISTS conferences (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Schools: institutions that employ coaches; optionally linked to a conference.
CREATE TABLE IF NOT EXISTS schools (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    conference_id INTEGER,
    FOREIGN KEY (conference_id) REFERENCES conferences(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

-- Coaches: people in the registry with current hire date information.
CREATE TABLE IF NOT EXISTS coaches (
    id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    full_name TEXT NOT NULL,
    hire_date TEXT
);

-- Positions: coaching role taxonomy (e.g., Head Coach, Offensive Coordinator).
CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL UNIQUE
);

-- CoachSeasons: bridge/season fact table linking coach, school, year, and optional position.
CREATE TABLE IF NOT EXISTS coach_seasons (
    id INTEGER PRIMARY KEY,
    coach_id INTEGER NOT NULL,
    school_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    position_id INTEGER,
    games INTEGER,
    wins INTEGER,
    losses INTEGER,
    ties INTEGER,
    preseason_rank INTEGER,
    postseason_rank INTEGER,
    FOREIGN KEY (coach_id) REFERENCES coaches(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (school_id) REFERENCES schools(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (position_id) REFERENCES positions(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    CONSTRAINT uq_coach_school_year_position UNIQUE (coach_id, school_id, year, position_id)
);

-- Indexes for efficient joins, filtering, and time-series lookups.
CREATE INDEX IF NOT EXISTS idx_schools_conference_id
    ON schools (conference_id);

CREATE INDEX IF NOT EXISTS idx_coaches_full_name
    ON coaches (full_name);

CREATE INDEX IF NOT EXISTS idx_coach_seasons_coach_id
    ON coach_seasons (coach_id);

CREATE INDEX IF NOT EXISTS idx_coach_seasons_school_id
    ON coach_seasons (school_id);

CREATE INDEX IF NOT EXISTS idx_coach_seasons_position_id
    ON coach_seasons (position_id);

CREATE INDEX IF NOT EXISTS idx_coach_seasons_year
    ON coach_seasons (year);

CREATE INDEX IF NOT EXISTS idx_coach_seasons_school_year
    ON coach_seasons (school_id, year);

CREATE INDEX IF NOT EXISTS idx_coach_seasons_coach_year
    ON coach_seasons (coach_id, year);
