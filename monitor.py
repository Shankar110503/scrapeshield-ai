from .models import FieldSpec, HealthReport

def check_health(rows, schema):
    if not rows:
        return HealthReport(False, [f.name for f in schema], 0, "No rows returned.")
    missing = [f.name for f in schema if not any(str(r.get(f.name, "")).strip() for r in rows)]
    return HealthReport(not missing, missing, len(rows),
                        "Extraction healthy." if not missing else "Missing fields: " + ", ".join(missing))
