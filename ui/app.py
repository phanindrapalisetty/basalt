import json
import streamlit as st
import ui.api_client as client

st.set_page_config(page_title="Basalt", page_icon="🪨", layout="wide")
st.title("🪨 Basalt — Synthetic Data Generator")

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")
    api_url = st.text_input("API URL", value="http://localhost:8000")
    import os; os.environ["BASALT_API_URL"] = api_url

    seed = st.number_input("Seed", value=42, step=1)
    rows = st.slider("Rows", min_value=1, max_value=5000, value=10)
    fmt = st.selectbox("Output format", ["json", "csv", "ndjson", "parquet", "avro"])

    alive = client.health()
    st.markdown(f"API status: {'🟢 online' if alive else '🔴 offline'}")

# ── Session state ──────────────────────────────────────────────────────────
if "columns" not in st.session_state:
    st.session_state.columns = []

COLUMN_TYPES = ["int", "float", "string", "boolean", "date", "uuid", "timestamp", "email", "phone", "regex"]

# ── Tabs ────────────────────────────────────────────────────────────────────
tab_builder, tab_paste = st.tabs(["Builder", "Paste Spec"])

with tab_builder:
    if st.button("＋ Add Column"):
        st.session_state.columns.append({
            "name": f"col_{len(st.session_state.columns) + 1}",
            "type": "int",
        })

    to_remove = []
    for i, col in enumerate(st.session_state.columns):
        with st.expander(f"Column: {col.get('name', f'col_{i+1}')}", expanded=True):
            col["name"] = st.text_input("Name", value=col.get("name", ""), key=f"name_{i}")
            col["type"] = st.selectbox("Type", COLUMN_TYPES, index=COLUMN_TYPES.index(col.get("type", "int")), key=f"type_{i}")

            t = col["type"]
            if t == "int":
                col["min"] = st.number_input("Min", value=col.get("min", 1), step=1, key=f"min_{i}")
                col["max"] = st.number_input("Max", value=col.get("max", 100), step=1, key=f"max_{i}")
                col["unique"] = st.checkbox("Unique", value=col.get("unique", False), key=f"uniq_{i}")
                col["sequential"] = st.checkbox("Sequential", value=col.get("sequential", False), key=f"seq_{i}")
                if col["sequential"]:
                    col["start"] = st.number_input("Start", value=col.get("start", 1), step=1, key=f"start_{i}")
                    col["step"] = st.number_input("Step", value=col.get("step", 1), step=1, key=f"step_{i}")

            elif t == "float":
                col["min"] = st.number_input("Min", value=float(col.get("min", 0.0)), key=f"min_{i}")
                col["max"] = st.number_input("Max", value=float(col.get("max", 1.0)), key=f"max_{i}")
                col["rounding"] = st.number_input("Rounding (decimal places)", value=col.get("rounding", 2), step=1, min_value=0, key=f"round_{i}")

            elif t == "string":
                values_raw = st.text_input("Values (comma-separated)", value=",".join(col.get("values", [])), key=f"vals_{i}")
                col["values"] = [v.strip() for v in values_raw.split(",") if v.strip()]
                dist_raw = st.text_input("Distribution (comma-separated floats)", value=",".join(str(d) for d in col.get("distribution", [])), key=f"dist_{i}")
                try:
                    col["distribution"] = [float(d.strip()) for d in dist_raw.split(",") if d.strip()]
                except ValueError:
                    col["distribution"] = []

            elif t == "boolean":
                col["true_ratio"] = st.slider("True ratio", 0.0, 1.0, value=float(col.get("true_ratio", 0.5)), key=f"tr_{i}")

            elif t == "date":
                col["start_date"] = st.text_input("Start date (YYYY-MM-DD)", value=col.get("start_date", "2020-01-01"), key=f"sd_{i}")
                col["end_date"] = st.text_input("End date (YYYY-MM-DD)", value=col.get("end_date", "2024-12-31"), key=f"ed_{i}")

            elif t == "timestamp":
                col["start"] = st.text_input("Start (ISO datetime)", value=col.get("start", "2020-01-01T00:00:00"), key=f"ts_s_{i}")
                col["end"] = st.text_input("End (ISO datetime)", value=col.get("end", "2024-12-31T23:59:59"), key=f"ts_e_{i}")

            elif t == "email":
                domains_raw = st.text_input("Domains (comma-separated)", value=",".join(col.get("domains", ["example.com"])), key=f"dom_{i}")
                col["domains"] = [d.strip() for d in domains_raw.split(",") if d.strip()]

            elif t == "phone":
                col["format"] = st.text_input("Format (# = digit)", value=col.get("format", "+1-###-###-####"), key=f"ph_{i}")

            elif t == "regex":
                col["pattern"] = st.text_input("Pattern", value=col.get("pattern", "[A-Z]{3}-\\d{4}"), key=f"pat_{i}")

            col["null_ratio"] = st.slider("Null ratio", 0.0, 1.0, value=float(col.get("null_ratio", 0.0)), step=0.05, key=f"nr_{i}")

            if st.button("Remove", key=f"rm_{i}"):
                to_remove.append(i)

    for i in reversed(to_remove):
        st.session_state.columns.pop(i)

    # Build spec from UI state
    def _build_spec():
        columns = {}
        for col in st.session_state.columns:
            name = col.get("name", "").strip()
            if not name:
                continue
            entry = {"type": col["type"]}
            for k in ["min", "max", "unique", "sequential", "start", "step",
                      "rounding", "values", "distribution", "true_ratio",
                      "start_date", "end_date", "domains", "format", "pattern",
                      "null_ratio"]:
                if k in col and col[k] not in (None, [], ""):
                    entry[k] = col[k]
            columns[name] = entry
        return {"rows": rows, "seed": int(seed), "columns": columns}

    spec = _build_spec()

    st.subheader("Live Spec Preview")
    spec_json = json.dumps(spec, indent=2)
    st.json(spec)
    st.download_button("Download spec (.json)", data=spec_json, file_name="basalt_spec.json", mime="application/json")

    col_val, col_gen = st.columns(2)
    with col_val:
        if st.button("Validate"):
            r = client.validate(spec)
            body = r.json()
            if body.get("valid"):
                st.success("Spec is valid")
            else:
                st.error(body.get("error", "Invalid spec"))

    with col_gen:
        if st.button("Generate"):
            r = client.generate(spec, fmt=fmt)
            if r.status_code == 200:
                if fmt == "json":
                    data = r.json().get("data", [])
                    st.dataframe(data)
                    st.download_button("Download JSON", data=json.dumps(data, indent=2), file_name="basalt.json", mime="application/json")
                    st.download_button("Download CSV (re-generate)", data=client.generate(spec, fmt="csv").content, file_name="basalt.csv", mime="text/csv")
                else:
                    st.download_button(f"Download {fmt.upper()}", data=r.content, file_name=f"basalt.{fmt}")
            else:
                st.error(r.json().get("error", "Generation failed"))

with tab_paste:
    st.subheader("Paste or import an existing spec")
    raw = st.text_area("Spec JSON", height=300, placeholder='{"rows": 10, "seed": 42, "columns": {...}}')
    if st.button("Load spec into builder"):
        try:
            loaded = json.loads(raw)
            cols = []
            for name, cfg in loaded.get("columns", {}).items():
                entry = dict(cfg)
                entry["name"] = name
                cols.append(entry)
            st.session_state.columns = cols
            st.success("Spec loaded — switch to the Builder tab")
        except Exception as e:
            st.error(f"Invalid JSON: {e}")
