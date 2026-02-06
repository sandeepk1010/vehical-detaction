# Date-Wise Database View Feature

## Overview
The date-wise view provides a calendar-like interface to browse vehicle detection records grouped by date. This allows quick visualization of detection patterns and drill-down to hourly details.

## Features

### 1. Date-Wise Page Layout
The "By Date" tab in the sidebar opens a two-column interface:

**Left Panel (Date Cards):**
- Display all unique dates with detections
- Show formatted date (e.g., "Thu, Feb 6, 2026")
- Display detection count badge
- Show top 3 license plates as badges
- Clickable to load details

**Right Panel (Detail Section):**
- Initially empty
- Populates when a date is selected
- Shows all records for that date in tabular format:
  - **Time**: Detection timestamp (HH:MM:SS)
  - **Plate**: License plate number
  - **Camera**: Source camera (Camera 1 or Camera 2)
  - **Color**: Vehicle color

### 2. Backend APIs

#### `/api/db/date-wise` (GET)
Returns grouped database records by date.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "date": "2026-02-06",
      "count": 5,
      "top_plates": ["KA15K3343", "MA15CK13343", "MH170K9099"],
      "total_plates": 3
    },
    {
      "date": "2026-02-05",
      "count": 2,
      "top_plates": ["KA15K3344"],
      "total_plates": 1
    }
  ]
}
```

#### `/api/db/date/<date_str>` (GET)
Returns all records for a specific date.

**Parameters:**
- `date_str`: Date in format `YYYY-MM-DD` (from URL path)

**Response:**
```json
{
  "success": true,
  "date": "2026-02-06",
  "count": 5,
  "data": [
    {
      "id": 1,
      "time": "13:48:24",
      "license_plate": "KA15K3343",
      "vehicle_color": "Gray",
      "camera": "Camera 1",
      "created_at": "2026-02-06 13:48:24"
    },
    ...
  ]
}
```

### 3. Frontend Implementation

**JavaScript Functions:**

- `loadDateWiseData()`: Fetches `/api/db/date-wise` and renders date cards
- `showDateDetails(date)`: Fetches `/api/db/date/<date>` and renders detail table
- `formatDate(dateStr)`: Converts ISO date format to readable format

**UI Elements:**

- `.datewise-container`: Two-column grid layout
- `.date-card`: Interactive date card with hover effects
- `.record-row`: Table-like grid display for records
- `.records-table`: Container for all records on selected date

### 4. Responsive Design

**Desktop (>768px):**
- Two-column layout: 1fr (date cards) | 2fr (details)
- Natural flow with visible padding and spacing

**Mobile (<768px):**
- Single-column layout
- Dates stack vertically
- Details expand below
- Adjusted font sizes and spacing

## Database Query

The date-wise aggregation uses:
```sql
SELECT 
  DATE(created_at) as date,
  COUNT(*) as count,
  GROUP_CONCAT(DISTINCT license_plate, ', ') as top_plates
FROM vehicle_detections
GROUP BY DATE(created_at)
ORDER BY date DESC
```

For detail records:
```sql
SELECT *
FROM vehicle_detections
WHERE DATE(created_at) = ?
ORDER BY created_at DESC
```

## Usage

1. **Navigate to Date View:**
   - Click "By Date" in sidebar navigation
   - Page shows all dates with detections

2. **View Details:**
   - Click any date card in left panel
   - Right panel populates with all records for that date

3. **Identify Patterns:**
   - Quick view of busiest days (by count badge)
   - See which plates appear frequently (plate badges)
   - Drill down to specific time and camera for each detection

## Data Flow

```
Database (vehicle_detections table)
    ↓
[/api/db/date-wise endpoint]
    ↓
[loadDateWiseData() renders date cards]
    ↓
[User clicks date card]
    ↓
[/api/db/date/<date> endpoint]
    ↓
[showDateDetails() renders records table]
```

## Integration Points

- **Database:** `vehicle_detection.db` (SQLite)
- **Flask Routes:** Added in `vehicle_ui.py`
- **Frontend:** Tab in `templates/dashboard.html`, functions in `static/script.js`
- **Styling:** `.datewise-container` and related classes in `static/styles.css`

## Performance Considerations

- Date-wise query optimized with GROUP_CONCAT for top plates
- Detail records fetched on-demand (not all at once)
- Responsive pagination handled by frontend
- Suitable for 10,000+ records without noticeable lag

## Future Enhancements

Possible additions:
- Time-based filtering (today, this week, this month)
- Export to CSV by date range
- Heatmap view showing busiest hours
- Plate analytics (count, frequency, timeline)
- Export records for specific date
