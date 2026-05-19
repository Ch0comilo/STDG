"""Headless render-test for each page using streamlit's testing API."""
import sys, os, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(__file__))

from streamlit.testing.v1 import AppTest

at = AppTest.from_file("app/app.py", default_timeout=240)
# Toggle TerriData for this run
import os
mode = os.environ.get("MODE", "default")
at.session_state["include_terridata"] = (mode == "terridata")
print(f"=== MODE: {mode} (terridata={at.session_state['include_terridata']}) ===")
at.run()
print("Initial run OK")
print("  exceptions:", len(at.exception))
for e in at.exception:
    print("    -", e.value)

for page_id in ["panorama", "clima", "territorio", "modelo", "tecnico"]:
    at.session_state["nav_page"] = page_id
    try:
        at.run()
        print(f"page {page_id}: OK ({len(at.exception)} exceptions)")
        for e in at.exception:
            print(f"    - {type(e).__name__}: {str(e)[:200]}")
    except Exception as ex:
        print(f"page {page_id}: FAIL {type(ex).__name__}: {ex}")
