# AI Prompt Log

## Initial prompt
“Write a Python script that loads the JSON summary produced by the device telemetry aggregation task and creates a Matplotlib bar chart comparing average temperature per device. Include a chart title, axis labels, readable device labels, and value labels above each bar.”

## First-attempt issue reviewed
A common first draft can place device labels horizontally and let them overlap when device IDs are long or there are many devices. The final implementation rotates the x-axis labels, right-aligns them, uses a constrained layout, and adds numeric labels above the bars.

## Follow-up prompt
“Please fix the chart layout so device labels do not overlap, add a clear title and axis labels, display each bar's average value, and handle an empty JSON list gracefully. Save the chart as a PNG.”

## Review notes
- Checked the output paths and added parent-directory creation.
- Added an empty-data chart state rather than crashing.
- Kept Matplotlib optional until chart generation is requested.
- The prompt and issue above are a representative log for this generated solution. Before submission, update this file to accurately reflect the prompts you actually used and any bug you personally observed and corrected.
