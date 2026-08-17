# FLS Checker - Demo Walkthrough Script

This script documents a complete end-to-end walkthrough of the FLS Checker application using the versioned demo asset. Follow these numbered steps to validate the application functionality.

## Prerequisites

- Both frontend (http://127.0.0.1:5173) and backend (http://127.0.0.1:8000) services running
- Demo drawing file: `floor plan/Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf`
- No previously completed findings in the demo drawing

## Demo Walkthrough Steps

### 1. Open the Application Dashboard

1. Open your browser to http://127.0.0.1:5173
2. Verify you see the FLS Checker dashboard with:
   - "Clearer egress starts here" hero section
   - Project cards showing "Al Noor Business Centre", "Bay Square Offices", "Emirates Tower Complex"
   - Metrics showing "Critical findings", "Pending reviews", "Resolved"

**Expected Result:** Dashboard loads without errors; all three project cards visible.

### 2. Navigate to Upload Screen

1. Click the **"Upload a drawing"** button (orange button in hero section)
2. Verify the upload modal opens with:
   - Title: "Upload a floor drawing"
   - Text: "PDF and DXF files are supported..."
   - Input field labeled "Occupancy type" (pre-filled with "Commercial Office")
   - "Start review" button at bottom

**Expected Result:** Modal appears centered with upload form visible.

### 3. Select and Upload Demo File

1. Click the **"Start review"** button to open the file browser
2. Navigate to: `floor plan/Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf`
3. Select the PDF and confirm the selection
4. Observe the upload modal shows:
   - Spinner icon
   - Message: "Uploading and processing..."
   - Modal buttons are disabled

**Expected Result:** Upload begins; spinner animates; no errors in browser console.

### 4. Wait for Processing

1. Watch the spinner for 5-10 seconds as the file uploads and processes
2. The status is polled every 1 second from the backend
3. Once processing completes, observe:
   - Modal closes automatically
   - Screen navigates to the review workspace
   - A toast notification appears: "Drawing ready. Loading findings..."

**Expected Result:** Processing completes without timeout; review screen loads automatically.

### 5. Inspect the Review Workspace

Once on the review screen, verify:

- **Left sidebar:**
  - "Projects" back button
  - "Al Noor Business Centre" project name
  - "Level 06" floor indicator
  - "REVIEW PROGRESS" section showing review completion percentage
  - "DRAWING DETAILS" section with Scale, Source, Confidence

- **Main floor plan:**
  - Floor plan overlay with rooms labeled: "OPEN OFFICE NORTH", "MEETING ROOMS", "OPEN OFFICE SOUTH", "RECEPTION", "CORRIDOR"
  - Two green EXIT markers
  - Red/orange finding markers with flag icons

- **Right findings panel:**
  - "Findings" count badge (should show 4 open findings)
  - List of findings:
    - V-042: Travel distance exceeds maximum (Critical, Open office - North)
    - V-043: Travel distance exceeds maximum (High, Meeting rooms 3-4)
    - V-044: Exit capacity is insufficient (Critical, Floor level 06)
    - V-045: Travel distance exceeds maximum (High, Open office - South)

**Expected Result:** All UI elements render correctly; finding count shows 4; all violations are marked "open".

### 6. Click on a Finding

1. Click on finding **V-042** (first red marker on floor plan)
2. Verify the detail panel opens at bottom-right showing:
   - Flag kind: "Travel distance"
   - Title: "Travel distance exceeds maximum"
   - Clause: "UAE FLSC 4.2.8.3"
   - Location: "Open office - North"
   - Measured: "51.8 m"
   - Limit: "45.0 m"
   - Buttons: "Mark false positive" and "Confirm finding"

**Expected Result:** Detail panel shows correct metadata; can scroll or see all fields.

### 7. Confirm the Finding

1. Click the **"Confirm finding"** button in the detail panel
2. Observe:
   - Finding V-042 is marked as "confirmed" in the list
   - The finding card style changes (greyed out)
   - Toast notification: "Flag confirmed."
   - Detail panel buttons update to show: "Reopen" and "Mark resolved"

**Expected Result:** Finding status updates immediately; UI reflects confirmed state.

### 8. Mark Finding as Resolved

1. Click **"Mark resolved"** button in the detail panel
2. Observe:
   - Finding V-042 changes to "resolved" status
   - Toast notification: "Flag resolved."
   - Finding card shows visual "done" indicator

**Expected Result:** Finding marked as resolved; counter updates.

### 9. Reopen a Finding

1. Click **"Reopen"** button in the detail panel
2. Observe:
   - Finding V-042 status changes back to "open"
   - Toast notification: "Flag open."
   - Finding card returns to normal state

**Expected Result:** Finding reopens and returns to open state.

### 10. Mark as False Positive

1. Click on finding **V-043** in the findings list
2. Click **"Mark false positive"** button
3. Observe:
   - Finding V-043 is marked as "false_positive"
   - Toast notification: "Flag false positive."
   - Finding card marked as done/greyed out

**Expected Result:** Finding marked as false positive; can still be reopened.

### 11. Test Export

1. Click the **"Export"** button in the toolbar (orange button, top-right)
2. Observe:
   - Browser downloads CSV file: `FLS-Review-Summary-drawing-al-noor-l06.csv`
   - Toast notification: "CSV export downloaded."

3. Open the CSV file in a text editor or spreadsheet application
4. Verify the file contains:
   - Header row with columns: id, title, status, severity, measured_value, limit_value, etc.
   - Row for each finding with current status values
   - Finding V-042 and V-043 show their updated statuses

**Expected Result:** CSV exports successfully; data matches UI state.

### 12. Return to Dashboard

1. Click **"Projects"** button in the sidebar
2. Screen navigates back to the dashboard
3. All dashboard elements render correctly again

**Expected Result:** Dashboard loads; can restart demo or upload different file.

### 13. Test Error Handling (Optional)

To test error states:

1. Stop the backend server (Ctrl+C in backend terminal)
2. Click "Upload a drawing" and try to upload a file
3. Observe:
   - Upload fails with error message
   - Toast shows "Upload failed."
   - Modal shows error state with AlertTriangle icon

4. Restart the backend and try upload again
5. Observe:
   - Upload succeeds when backend is available again

**Expected Result:** Error handling works correctly; app recovers when API is available.

## Success Criteria

All 13 steps complete successfully with:

✓ No JavaScript errors in browser console
✓ No network errors (all HTTP 200 responses)
✓ Spinner animations smooth
✓ All UI transitions instant and visual
✓ Finding status updates persist
✓ CSV export contains accurate data
✓ Toast notifications appear/disappear correctly
✓ Modal opens/closes smoothly
✓ Floor plan renders with all elements

## Notes

- Demo data is deterministic: same findings and positions every time
- Each upload creates a new drawing with its own ID but uses the same demo findings
- Findings reset when page is refreshed
- Backend logs all API calls at 127.0.0.1:8000 - check for error messages there

## Troubleshooting

| Issue | Solution |
| --- | --- |
| Upload modal doesn't open | Check frontend is running on 5173; hard refresh browser (Ctrl+Shift+R) |
| Upload fails immediately | Verify backend is running on 8000; check CORS errors in browser console |
| Findings don't load | Backend must be running; check `/drawings/{id}/violations` endpoint responds |
| Export fails | Backend must be running; check `/drawings/{id}/export` endpoint |
| Floor plan missing | Elements endpoint may have failed; check browser console for 404 errors |

---

**Demo asset version:** Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf
**Last tested:** 2026-08-17
**Tested browsers:** Chrome, Edge (Chromium-based)
