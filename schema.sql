-- Enable foreign-key support
PRAGMA foreign_keys = ON;

-- 1) Main exercises table
CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY,
    name TEXT,
    name_en_us TEXT,
    name_alternative TEXT,
    slug TEXT,
    need_warmup BOOLEAN,
    advanced_weight INTEGER,
    featured_weight INTEGER,
    weight INTEGER,
    impact INTEGER,
    description TEXT,
    description_en_us TEXT,
    use_youtube_links BOOLEAN,
    featured BOOLEAN,
    sponsored_link BOOLEAN,
    exercise_to_copy INTEGER,
    status TEXT,
    sharing_hash TEXT,
    variation_of INTEGER,
    difficulty_id INTEGER,
    force_id INTEGER,
    mechanic_id INTEGER,
    FOREIGN KEY (variation_of)    REFERENCES exercises(id),
    FOREIGN KEY (difficulty_id)   REFERENCES difficulty(id),
    FOREIGN KEY (force_id)        REFERENCES forces(id),
    FOREIGN KEY (mechanic_id)     REFERENCES mechanics(id)
);

-- 2) Muscles and their association to exercises (general / primary / secondary / tertiary)
CREATE TABLE IF NOT EXISTS muscles (
    id INTEGER PRIMARY KEY,
    name TEXT,
    name_en_us TEXT,
    scientific_name TEXT,
    url_name TEXT,
    description TEXT,
    description_en_us TEXT,
    lft INTEGER,
    rght INTEGER,
    tree_id INTEGER,
    level INTEGER,
    parent INTEGER,
    FOREIGN KEY(parent) REFERENCES muscles(id)
);
CREATE TABLE IF NOT EXISTS exercise_muscles (
    exercise_id INTEGER,
    muscle_id INTEGER,
    is_general   BOOLEAN DEFAULT 0,
    is_primary   BOOLEAN DEFAULT 0,
    is_secondary BOOLEAN DEFAULT 0,
    is_tertiary  BOOLEAN DEFAULT 0,
    PRIMARY KEY (exercise_id, muscle_id),
    FOREIGN KEY (exercise_id) REFERENCES exercises(id),
    FOREIGN KEY (muscle_id)   REFERENCES muscles(id)
);

-- 3) Grips
CREATE TABLE IF NOT EXISTS grips (
    id INTEGER PRIMARY KEY,
    name TEXT,
    name_en_us TEXT,
    description TEXT,
    description_en_us TEXT,
    url_name TEXT
);
CREATE TABLE IF NOT EXISTS exercise_grips (
    exercise_id INTEGER,
    grip_id     INTEGER,
    PRIMARY KEY (exercise_id, grip_id),
    FOREIGN KEY (exercise_id) REFERENCES exercises(id),
    FOREIGN KEY (grip_id)     REFERENCES grips(id)
);

-- 4) Categories (primary + additional)
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY,
    name TEXT,
    name_en_us TEXT,
    include_in_api BOOLEAN,
    include_in_workout_generator BOOLEAN,
    display_order INTEGER,
    enable BOOLEAN,
    featured BOOLEAN,
    description TEXT
);
CREATE TABLE IF NOT EXISTS exercise_categories (
    exercise_id   INTEGER,
    category_id   INTEGER,
    is_primary    BOOLEAN DEFAULT 0,
    is_additional BOOLEAN DEFAULT 0,
    PRIMARY KEY (exercise_id, category_id),
    FOREIGN KEY (exercise_id) REFERENCES exercises(id),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- 5) Difficulty / Force / Mechanic lookup tables
CREATE TABLE IF NOT EXISTS difficulty (
    id INTEGER PRIMARY KEY,
    name TEXT,
    name_en_us TEXT
);
CREATE TABLE IF NOT EXISTS forces (
    id INTEGER PRIMARY KEY,
    name TEXT,
    url_name TEXT,
    name_en_us TEXT,
    description TEXT,
    description_en_us TEXT
);
CREATE TABLE IF NOT EXISTS mechanics (
    id INTEGER PRIMARY KEY,
    name TEXT,
    url_name TEXT,
    name_en_us TEXT,
    description TEXT,
    description_en_us TEXT
);

-- 6) Genders (for content, URLs, body-map entries)
CREATE TABLE IF NOT EXISTS genders (
    id INTEGER PRIMARY KEY,
    name TEXT,
    name_en_us TEXT
);

-- 7) Long-form content (we ignore the YouTube URL per “no media URLs”)
CREATE TABLE IF NOT EXISTS long_form_content (
    id INTEGER PRIMARY KEY,
    exercise_id INTEGER,
    gender_id   INTEGER,
    FOREIGN KEY (exercise_id) REFERENCES exercises(id),
    FOREIGN KEY (gender_id)   REFERENCES genders(id)
);

-- 8) “Correct steps” instructions
CREATE TABLE IF NOT EXISTS correct_steps (
    id INTEGER PRIMARY KEY,
    exercise_id INTEGER,
    step_order  INTEGER,
    text        TEXT,
    text_en_us  TEXT,
    FOREIGN KEY (exercise_id) REFERENCES exercises(id)
);

-- 9) SEO tags (one row per tag)
CREATE TABLE IF NOT EXISTS seo_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_id INTEGER,
    tag TEXT,
    FOREIGN KEY (exercise_id) REFERENCES exercises(id)
);

-- 10) Target URLs and site URLs (not media)
CREATE TABLE IF NOT EXISTS target_urls (
    exercise_id INTEGER,
    gender_id   INTEGER,
    url         TEXT,
    PRIMARY KEY (exercise_id, gender_id),
    FOREIGN KEY (exercise_id) REFERENCES exercises(id),
    FOREIGN KEY (gender_id)   REFERENCES genders(id)
);
CREATE TABLE IF NOT EXISTS urls (
    exercise_id INTEGER,
    gender_id   INTEGER,
    url         TEXT,
    PRIMARY KEY (exercise_id, gender_id),
    FOREIGN KEY (exercise_id) REFERENCES exercises(id),
    FOREIGN KEY (gender_id)   REFERENCES genders(id)
);

-- 11) Full-measure breakdown
CREATE TABLE IF NOT EXISTS measures (
    id INTEGER PRIMARY KEY,
    name TEXT
);
CREATE TABLE IF NOT EXISTS units (
    id INTEGER PRIMARY KEY,
    name TEXT
);
CREATE TABLE IF NOT EXISTS measure_units (
    measure_id INTEGER,
    unit_id    INTEGER,
    PRIMARY KEY (measure_id, unit_id),
    FOREIGN KEY (measure_id) REFERENCES measures(id),
    FOREIGN KEY (unit_id)    REFERENCES units(id)
);
CREATE TABLE IF NOT EXISTS denominators (
    id INTEGER PRIMARY KEY,
    name TEXT
);
CREATE TABLE IF NOT EXISTS denominator_units (
    denominator_id INTEGER,
    unit_id        INTEGER,
    PRIMARY KEY (denominator_id, unit_id),
    FOREIGN KEY (denominator_id) REFERENCES denominators(id),
    FOREIGN KEY (unit_id)        REFERENCES units(id)
);
CREATE TABLE IF NOT EXISTS calculation_modes (
    id INTEGER PRIMARY KEY,
    name TEXT,
    description TEXT
);
CREATE TABLE IF NOT EXISTS full_measures (
    id                 INTEGER PRIMARY KEY,
    exercise_id        INTEGER default null,
    measure_id         INTEGER default null,
    denominator_id     INTEGER default null,
    calculation_mode_id INTEGER default null,
    FOREIGN KEY (exercise_id)        REFERENCES exercises(id),
    FOREIGN KEY (measure_id)         REFERENCES measures(id),
    FOREIGN KEY (denominator_id)     REFERENCES denominators(id),
    FOREIGN KEY (calculation_mode_id)REFERENCES calculation_modes(id)
);

-- 12) Joints (if any) and association
CREATE TABLE IF NOT EXISTS joints (
    id INTEGER PRIMARY KEY,
    name TEXT,
    name_en_us TEXT,
    url_name TEXT,
    description TEXT,
    description_en_us TEXT
);
CREATE TABLE IF NOT EXISTS exercise_joints (
    exercise_id INTEGER,
    joint_id    INTEGER,
    PRIMARY KEY (exercise_id, joint_id),
    FOREIGN KEY (exercise_id) REFERENCES exercises(id),
    FOREIGN KEY (joint_id)    REFERENCES joints(id)
);

-- 13) Body-map entries (we ignore the front/back image URLs)
CREATE TABLE IF NOT EXISTS body_map_images (
    id INTEGER PRIMARY KEY,
    exercise_id INTEGER,
    gender_id   INTEGER,
    kind        TEXT,
    dark_mode   BOOLEAN,
    FOREIGN KEY (exercise_id) REFERENCES exercises(id),
    FOREIGN KEY (gender_id)   REFERENCES genders(id)
);
