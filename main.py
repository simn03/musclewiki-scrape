#!/usr/bin/env python3
import requests
import sqlite3

API_BASE = "https://musclewiki.com/newapi/exercise/exercises/"
LIMIT = 50
INITIAL_OFFSET = 1050

GENDER_MAP = {"male": 1, "female": 2}

def create_tables(conn):
    with open("schema.sql", 'r') as f:
        sql = f.read()
    conn.executescript(sql)

def upsert_lookup(conn, table, row):
    """Generic upsert for tables with an integer PK 'id' and all-other TEXT fields."""
    cols = ", ".join(row.keys())
    placeholders = ", ".join("?" for _ in row)
    sql = f"INSERT OR IGNORE INTO {table} ({cols}) VALUES ({placeholders})"
    conn.execute(sql, tuple(row.values()))

def main():
    conn = sqlite3.connect("musclewiki.db")
    conn.execute("PRAGMA foreign_keys = ON;")

    # create schema
    create_tables(conn)

    # seed genders
    for name, gid in GENDER_MAP.items():
        conn.execute(
            "INSERT OR IGNORE INTO genders (id, name, name_en_us) VALUES (?, ?, ?)",
            (GENDER_MAP[name], name.capitalize(), name.capitalize())
        )

    next_url = f"{API_BASE}?limit={LIMIT}&offset={INITIAL_OFFSET}&status=Published"
    
    while next_url:
        print("Fetching", next_url)
        resp = requests.get(next_url).json()

        for ex in resp["results"]:
            # --- difficulty / force / mechanic ---
            if ex["difficulty"] is not None:
                upsert_lookup(conn, "difficulty",  {
                    "id":   ex["difficulty"]["id"],
                    "name": ex["difficulty"]["name"],
                    "name_en_us": ex["difficulty"]["name_en_us"]
                })
                
            if ex["force"] is not None:
                upsert_lookup(conn, "forces", {
                    "id":   ex["force"]["id"],
                    "name": ex["force"]["name"],
                    "url_name": ex["force"]["url_name"],
                    "name_en_us": ex["force"]["name_en_us"],
                    "description": ex["force"]["description"],
                    "description_en_us": ex["force"]["description_en_us"]
                })
                
            if ex["mechanic"] is not None:
                upsert_lookup(conn, "mechanics", {
                    "id":   ex["mechanic"]["id"],
                    "name": ex["mechanic"]["name"],
                    "url_name": ex["mechanic"]["url_name"],
                    "name_en_us": ex["mechanic"]["name_en_us"],
                    "description": ex["mechanic"]["description"],
                    "description_en_us": ex["mechanic"]["description_en_us"]
                })
            
            # Check if we have a variation_of that isn’t in the table yet
            var_of = ex["variation_of"]
            if var_of is not None:
                exists = conn.execute(
                    "SELECT 1 FROM exercises WHERE id = ?", (var_of,)
                ).fetchone()
                if not exists:
                    # Insert a stub row with just the ID—everything else will be NULL for now
                    conn.execute(
                        "INSERT OR IGNORE INTO exercises (id) VALUES (?)",
                        (var_of,)
                    )

            # --- main exercise row ---
            conn.execute("""
            INSERT OR REPLACE INTO exercises (
                id, name, name_en_us, name_alternative, slug,
                need_warmup, advanced_weight, featured_weight, weight, impact,
                description, description_en_us, use_youtube_links,
                featured, sponsored_link, exercise_to_copy,
                status, sharing_hash, variation_of,
                difficulty_id, force_id, mechanic_id
            ) VALUES (
                :id, :name, :name_en_us, :name_alt, :slug,
                :need_wu, :adv_w, :feat_w, :w, :impact,
                :desc, :desc_en, :use_yt,
                :feat, :spons, :copy,
                :status, :shash, :var_of,
                :did, :fid, :mid
            )""", {
                "id":   ex["id"],
                "name": ex["name"],
                "name_en_us": ex["name_en_us"],
                "name_alt": ex.get("name_alternative"),
                "slug": ex["slug"],
                "need_wu": ex["need_warmup"],
                "adv_w": ex["advanced_weight"],
                "feat_w": ex["featured_weight"],
                "w": ex["weight"],
                "impact": ex["impact"],
                "desc": ex["description"],
                "desc_en": ex["description_en_us"],
                "use_yt": ex["use_youtube_links"],
                "feat": ex["featured"],
                "spons": ex["sponsered_link"],
                "copy": ex["exercise_to_copy"],
                "status": ex["status"],
                "shash": ex["sharing_hash"],
                "var_of": ex["variation_of"],
                "did": ex["difficulty"]["id"] if ex["difficulty"] is not None else None,
                "fid": ex["force"]["id"] if ex["force"] is not None else None,
                "mid": ex["mechanic"]["id"] if ex["mechanic"] is not None else None
            })

            # --- muscles (general / primary / secondary / tertiary) ---
            for group, flag in [
                ("muscles",    ("is_general",   True)),
                ("muscles_primary",   ("is_primary",   True)),
                ("muscles_secondary", ("is_secondary", True)),
                ("muscles_tertiary",  ("is_tertiary",  True))
            ]:
                for m in ex.get(group, []):
                    upsert_lookup(conn, "muscles", {
                        "id": m["id"],
                        "name": m["name"],
                        "name_en_us": m["name_en_us"],
                        "scientific_name": m["scientific_name"],
                        "url_name": m["url_name"],
                        "description": m["description"],
                        "description_en_us": m["description_en_us"],
                        "lft": m["lft"],
                        "rght": m["rght"],
                        "tree_id": m["tree_id"],
                        "level": m["level"],
                        "parent": m["parent"]
                    })
                    conn.execute(f"""
                    INSERT OR REPLACE INTO exercise_muscles
                        (exercise_id, muscle_id, {flag[0]})
                    VALUES (?, ?, ?)
                    """, (ex["id"], m["id"], flag[1]))

            # --- grips ---
            for g in ex.get("grips", []):
                upsert_lookup(conn, "grips", {
                    "id": g["id"],
                    "name": g["name"],
                    "name_en_us": g["name_en_us"],
                    "description": g["description"],
                    "description_en_us": g["description_en_us"],
                    "url_name": g["url_name"]
                })
                conn.execute("""
                    INSERT OR REPLACE INTO exercise_grips
                      (exercise_id, grip_id)
                    VALUES (?, ?)
                """, (ex["id"], g["id"]))

            # --- category + additional_categories ---
            cat = ex["category"]
            upsert_lookup(conn, "categories", {
                "id": cat["id"], "name": cat["name"], "name_en_us": cat["name_en_us"],
                "include_in_api": cat["include_in_api"],
                "include_in_workout_generator": cat["include_in_workout_generator"],
                "display_order": cat["display_order"], "enable": cat["enable"],
                "featured": cat["featured"], "description": cat["description"]
            })
            conn.execute("""
              INSERT OR REPLACE INTO exercise_categories
                (exercise_id, category_id, is_primary, is_additional)
              VALUES (?, ?, 1, 0)
            """, (ex["id"], cat["id"]))
            for ac in ex.get("additional_categories", []):
                upsert_lookup(conn, "categories", {
                    "id": ac["id"], "name": ac["name"], "name_en_us": ac["name_en_us"],
                    "include_in_api": ac["include_in_api"],
                    "include_in_workout_generator": ac["include_in_workout_generator"],
                    "display_order": ac["display_order"], "enable": ac["enable"],
                    "featured": ac["featured"], "description": ac["description"]
                })
                conn.execute("""
                  INSERT OR REPLACE INTO exercise_categories
                    (exercise_id, category_id, is_primary, is_additional)
                  VALUES (?, ?, 0, 1)
                """, (ex["id"], ac["id"]))

            # --- long_form_content (no YouTube URL) ---
            for lfc in ex.get("long_form_content", []):
                gid = lfc["gender"]["id"]
                # assume genders already seeded or will IGNORE
                conn.execute("""
                  INSERT OR IGNORE INTO long_form_content
                    (id, exercise_id, gender_id)
                  VALUES (?, ?, ?)
                """, (lfc["id"], ex["id"], gid))

            # --- correct_steps ---
            for step in ex.get("correct_steps", []):
                conn.execute("""
                  INSERT OR IGNORE INTO correct_steps
                    (id, exercise_id, step_order, text, text_en_us)
                  VALUES (?, ?, ?, ?, ?)
                """, (
                    step["id"], ex["id"],
                    step["order"],
                    step["text"], step["text_en_us"]
                ))

            # --- seo_tags ---
            for tag in ex.get("seo_tags", []):
                conn.execute("""
                  INSERT OR REPLACE INTO seo_tags (exercise_id, tag)
                  VALUES (?, ?)
                """, (ex["id"], tag))

            # --- target_urls & urls (non-media) ---
            for tbl in ("target_urls", "urls"):
                for gender_str, link in ex.get(tbl, {}).items():
                    gid = GENDER_MAP[gender_str.lower()]
                    conn.execute(f"""
                      INSERT OR REPLACE INTO {tbl}
                        (exercise_id, gender_id, url)
                      VALUES (?, ?, ?)
                    """, (ex["id"], gid, link))

            # --- full_measure + lookups ---
            fm = ex["full_measure"]
            
            if fm is not None:
                # measures
                if fm["measure"] is not None:
                    upsert_lookup(conn, "measures",  {
                            "id": fm["measure"]["id"], 
                            "name": fm["measure"]["name"]
                        }
                    )
                    for u in fm["measure"]["units"]:
                        upsert_lookup(conn, "units", {"id": u["id"], "name": u["name"]})
                        conn.execute("""
                        INSERT OR IGNORE INTO measure_units (measure_id, unit_id)
                        VALUES (?, ?)
                        """, (fm["measure"]["id"], u["id"]))
                        
                # denominators
                if fm["denominator"] is not None:
                    upsert_lookup(conn, "denominators", {"id": fm["denominator"]["id"], "name": fm["denominator"]["name"]})
                    for u in fm["denominator"]["units"]:
                        upsert_lookup(conn, "units", {"id": u["id"], "name": u["name"]})
                        conn.execute("""
                        INSERT OR IGNORE INTO denominator_units (denominator_id, unit_id)
                        VALUES (?, ?)
                        """, (fm["denominator"]["id"], u["id"]))
                        
                # calculation modes
                if fm["calculation_mode"] is not None:
                    upsert_lookup(conn, "calculation_modes", {
                        "id": fm["calculation_mode"]["id"],
                        "name": fm["calculation_mode"]["name"],
                        "description": fm["calculation_mode"]["description"]
                    })
                    
                # full_measures
                conn.execute("""
                INSERT OR REPLACE INTO full_measures
                    (id, exercise_id, measure_id, denominator_id, calculation_mode_id)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    fm["id"], ex["id"],
                    fm["measure"]["id"] if fm["measure"] is not None else None,
                    fm["denominator"]["id"] if fm["denominator"] is not None else None,
                    fm["calculation_mode"]["id"]  if fm["calculation_mode"] is not None else None,
                ))

            # --- joints (if any) ---
            for j in ex.get("joints", []):
                upsert_lookup(conn, "joints", {
                    "id": j,
                })
                conn.execute("""
                  INSERT OR IGNORE INTO exercise_joints (exercise_id, joint_id)
                  VALUES (?, ?)
                """, (ex["id"], j))

            # --- body_map_images (ignore the actual image URLs) ---
            for bmi in ex.get("body_map_images", []):
                gid = bmi["gender"]["id"]
                conn.execute("""
                  INSERT OR REPLACE INTO body_map_images
                    (id, exercise_id, gender_id, kind, dark_mode)
                  VALUES (?, ?, ?, ?, ?)
                """, (
                    bmi["id"], ex["id"], gid,
                    bmi["kind"], bmi["dark_mode"]
                ))

        conn.commit()
        next_url = resp.get("next")

    print("Done.")

if __name__ == "__main__":
    main()
