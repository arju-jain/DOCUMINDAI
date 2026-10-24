"""DocuMind AI - Automated End-to-End Browser UI Test Suite
Executes real browser UI workflows against the live running FastAPI/Static web app
using Playwright and system-installed Google Chrome / Microsoft Edge.
"""

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
SCREENSHOT_DIR = BASE_DIR / "reports" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# Locate installed browser executable
CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_browser_executable() -> str:
    for candidate in CHROME_CANDIDATES:
        if os.path.exists(candidate):
            return candidate
    raise RuntimeError("No compatible Chrome or Edge browser binary found on host system.")


def is_backend_running(url: str = "http://127.0.0.1:8000/api/health") -> bool:
    try:
        req = urllib.request.urlopen(url, timeout=2)
        return req.getcode() == 200
    except Exception:
        return False


def run_e2e_tests():
    print("=" * 60)
    print("DOCUMIND AI — AUTOMATED BROWSER WORKFLOW VERIFICATION")
    print("=" * 60)

    browser_exe = find_browser_executable()
    print(f"[INIT] Using browser binary: {browser_exe}")

    server_process = None
    if not is_backend_running():
        print("[INIT] Starting FastAPI backend on http://127.0.0.1:8000 ...")
        python_exe = sys.executable
        server_process = subprocess.Popen(
            [python_exe, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=str(BASE_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # Wait up to 10 seconds for server startup
        for _ in range(20):
            time.sleep(0.5)
            if is_backend_running():
                print("[INIT] Backend server is healthy and responding.")
                break
        else:
            raise RuntimeError("Backend server failed to start within timeout.")
    else:
        print("[INIT] Backend server already active on http://127.0.0.1:8000.")

    test_results = {}
    console_errors = []
    page_errors = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=browser_exe,
                headless=True,
                args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
            )
            context = browser.new_context(
                viewport={"width": 1440, "height": 900},
                accept_downloads=True,
            )
            page = context.new_page()

            # Listen to console messages and page errors
            def on_console(msg):
                if msg.type == "error":
                    # Ignore harmless favicon 404 or expected network test rejections
                    if "favicon" not in msg.text.lower():
                        console_errors.append(msg.text)
                print(f"  [CONSOLE {msg.type.upper()}] {msg.text}")

            def on_page_error(exc):
                page_errors.append(str(exc))
                print(f"  [PAGE ERROR] {str(exc)}")

            page.on("console", on_console)
            page.on("pageerror", on_page_error)

            # -----------------------------------------------------------------
            # TEST 1: Initial Page Load & Dashboard KPIs
            # -----------------------------------------------------------------
            print("\n[TEST 1] Loading Dashboard at http://127.0.0.1:8000/ ...")
            response = page.goto("http://127.0.0.1:8000/", wait_until="networkidle", timeout=15000)
            assert response.status == 200, f"Expected HTTP 200, got {response.status}"
            assert "DocuMind AI" in page.title(), f"Unexpected title: {page.title()}"

            # Wait for Lucide icons or main layout
            page.wait_for_selector("#sectionDashboard.active", timeout=5000)
            status_text = page.inner_text("#apiStatusText")
            print(f"  API Connection Status Widget: {status_text}")
            
            # Save screenshot
            ss_dashboard = SCREENSHOT_DIR / "01_dashboard_loaded.png"
            page.screenshot(path=str(ss_dashboard))
            print(f"  Saved screenshot: {ss_dashboard.name}")
            test_results["test_01_dashboard_load"] = "PASS"

            # -----------------------------------------------------------------
            # TEST 2: PDF Document Upload & Extraction
            # -----------------------------------------------------------------
            print("\n[TEST 2] Testing PDF Upload & Extraction (inv_01_techcorp.pdf) ...")
            # Switch to Extract view
            page.click("#navExtract")
            page.wait_for_selector("#sectionExtract.active", timeout=5000)

            sample_pdf = BASE_DIR / "evaluation" / "dataset" / "inv_01_techcorp.pdf"
            assert sample_pdf.exists(), f"Sample PDF not found: {sample_pdf}"

            # Set file into fileInput
            page.set_input_files("#fileInput", str(sample_pdf))
            page.wait_for_selector("#selectedFileName", timeout=5000)
            filename_displayed = page.inner_text("#selectedFileName")
            print(f"  Selected file displayed: {filename_displayed}")
            assert "inv_01_techcorp.pdf" in filename_displayed

            # Click Extract & Validate
            page.click("#btnExtractValidate")
            # Wait for results table to populate (navigates automatically to Results section)
            page.wait_for_selector("#sectionResults.active", timeout=15000)
            page.wait_for_selector("#resultsTableBody tr[data-field-name]", timeout=15000)

            # Verify extracted values
            table_text = page.inner_text("#resultsTableBody")
            print(f"  Extracted fields rendered. Snippet:\n{table_text[:200]}...")
            assert "TechCorp Solutions Inc" in table_text
            assert "TC-2026-881" in table_text
            assert "1375" in table_text or "1,375" in table_text

            ss_extracted = SCREENSHOT_DIR / "02_pdf_extracted_results.png"
            page.screenshot(path=str(ss_extracted))
            print(f"  Saved screenshot: {ss_extracted.name}")
            test_results["test_02_pdf_extraction"] = "PASS"

            # -----------------------------------------------------------------
            # TEST 3: Inline Field Editing & Dynamic Recalculation
            # -----------------------------------------------------------------
            print("\n[TEST 3] Testing Inline Field Editing ...")
            # Find the vendor_name row edit button
            vendor_row = page.locator("tr[data-field-name='vendor_name']")
            assert vendor_row.count() > 0, "vendor_name row not found"
            
            edit_btn = vendor_row.locator(".btn-action-edit")
            edit_btn.click()

            # Wait for inline input
            input_box = vendor_row.locator(".inline-edit-input")
            input_box.wait_for(state="visible", timeout=3000)
            input_box.fill("TechCorp Solutions Inc (Verified)")

            # Click save button
            save_btn = vendor_row.locator("button.btn-primary")
            save_btn.click()

            # Verify updated text
            page.wait_for_timeout(500)
            updated_text = vendor_row.inner_text()
            print(f"  Updated vendor_name row text: {updated_text.strip()}")
            assert "Verified" in updated_text

            ss_edit = SCREENSHOT_DIR / "03_inline_field_edited.png"
            page.screenshot(path=str(ss_edit))
            print(f"  Saved screenshot: {ss_edit.name}")
            test_results["test_03_inline_field_editing"] = "PASS"

            # -----------------------------------------------------------------
            # TEST 4: Evaluation Benchmark Dashboard
            # -----------------------------------------------------------------
            print("\n[TEST 4] Testing Evaluation Benchmark View ...")
            page.click("#navEvaluation")
            page.wait_for_selector("#sectionEvaluation.active", timeout=5000)

            # Trigger evaluation fetch if not loaded automatically
            if page.locator("#btnRefreshEvaluation").is_visible():
                page.click("#btnRefreshEvaluation")
                page.wait_for_timeout(1000)

            eval_accuracy = page.inner_text("#evalOverallAccuracy")
            eval_docs = page.inner_text("#evalDocsCount")
            print(f"  Evaluation Metrics: Accuracy={eval_accuracy}, Docs={eval_docs}")
            assert "100" in eval_accuracy, f"Expected 100% accuracy, got {eval_accuracy}"

            ss_eval = SCREENSHOT_DIR / "04_evaluation_view.png"
            page.screenshot(path=str(ss_eval))
            print(f"  Saved screenshot: {ss_eval.name}")
            test_results["test_04_evaluation_dashboard"] = "PASS"

            # -----------------------------------------------------------------
            # TEST 5: CSV and JSON Exports
            # -----------------------------------------------------------------
            print("\n[TEST 5] Testing CSV and JSON Export Triggers ...")
            page.click("#navResults")
            page.wait_for_selector("#sectionResults.active", timeout=5000)

            btn_csv = page.locator("#btnDownloadCSV")
            btn_json = page.locator("#btnDownloadJSON")
            assert not btn_csv.is_disabled(), "CSV export button should be enabled"
            assert not btn_json.is_disabled(), "JSON export button should be enabled"

            # Trigger CSV download
            with page.expect_download(timeout=10000) as download_info:
                btn_csv.click()
            csv_download = download_info.value
            print(f"  CSV Download triggered: {csv_download.suggested_filename}")
            assert "csv" in csv_download.suggested_filename.lower()

            # Trigger JSON download
            with page.expect_download(timeout=10000) as download_info_json:
                btn_json.click()
            json_download = download_info_json.value
            print(f"  JSON Download triggered: {json_download.suggested_filename}")
            assert "json" in json_download.suggested_filename.lower()

            test_results["test_05_export_downloads"] = "PASS"

            # -----------------------------------------------------------------
            # TEST 6: Scanned Image Upload & OCR (inv_03_summit_cloud.png)
            # -----------------------------------------------------------------
            print("\n[TEST 6] Testing Scanned Image OCR (inv_03_summit_cloud.png) ...")
            page.click("#navExtract")
            page.wait_for_selector("#sectionExtract.active", timeout=5000)

            sample_png = BASE_DIR / "evaluation" / "dataset" / "inv_03_summit_cloud.png"
            assert sample_png.exists(), f"Sample PNG not found: {sample_png}"

            page.set_input_files("#fileInput", str(sample_png))
            page.wait_for_selector("#selectedFileName", timeout=5000)
            page.click("#btnExtractValidate")

            # Wait for results
            page.wait_for_selector("#sectionResults.active", timeout=15000)
            page.wait_for_selector("#resultsTableBody tr[data-field-name]", timeout=15000)
            
            ocr_table_text = page.inner_text("#resultsTableBody")
            print(f"  OCR extracted fields snippet:\n{ocr_table_text[:200]}...")
            assert "Summit Cloud Systems" in ocr_table_text
            assert "572" in ocr_table_text

            ss_ocr = SCREENSHOT_DIR / "05_image_ocr_results.png"
            page.screenshot(path=str(ss_ocr))
            print(f"  Saved screenshot: {ss_ocr.name}")
            test_results["test_06_image_ocr_flow"] = "PASS"

            # -----------------------------------------------------------------
            # TEST 7: Invalid File Upload Error Handling
            # -----------------------------------------------------------------
            print("\n[TEST 7] Testing Invalid File Format Handling ...")
            page.click("#navExtract")
            page.wait_for_selector("#sectionExtract.active", timeout=5000)

            dummy_txt = BASE_DIR / "reports" / "invalid_test.txt"
            dummy_txt.write_text("This is an unsupported plain text file.", encoding="utf-8")
            try:
                page.set_input_files("#fileInput", str(dummy_txt))
                page.wait_for_selector("#uploadErrorAlert", state="visible", timeout=5000)
                err_text = page.inner_text("#uploadErrorMessage")
                print(f"  Validation error displayed correctly: {err_text}")
                assert len(err_text) > 0

                ss_err = SCREENSHOT_DIR / "06_invalid_file_error.png"
                page.screenshot(path=str(ss_err))
                print(f"  Saved screenshot: {ss_err.name}")
                test_results["test_07_invalid_file_handling"] = "PASS"
            finally:
                if dummy_txt.exists():
                    dummy_txt.unlink()

            browser.close()

    finally:
        if server_process:
            print("[CLEANUP] Stopping background backend server process...")
            server_process.terminate()
            server_process.wait()

    # Verify no unhandled page errors occurred
    print("\n" + "=" * 60)
    print("BROWSER TEST EXECUTION SUMMARY")
    print("=" * 60)
    all_passed = True
    for test_name, status in test_results.items():
        print(f"  {test_name.ljust(35)} : {status}")
        if status != "PASS":
            all_passed = False

    print(f"\nUncaught Page Errors: {len(page_errors)}")
    for err in page_errors:
        print(f"  - {err}")

    assert all_passed, "One or more browser tests failed."
    assert len(page_errors) == 0, f"Uncaught JavaScript page errors encountered: {page_errors}"

    # Save summary report to JSON
    report_path = BASE_DIR / "reports" / "browser_test_report.json"
    report_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "browser": browser_exe,
        "results": test_results,
        "page_errors": page_errors,
        "console_errors": console_errors,
        "status": "ALL_PASSED",
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print(f"\n[REPORT] Saved browser test report to: {report_path}")
    print("ALL BROWSER WORKFLOW TESTS COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    run_e2e_tests()
