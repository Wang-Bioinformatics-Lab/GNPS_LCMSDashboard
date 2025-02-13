def generate_svg_progress(data):
    svg_width = 400  # Total width of the SVG
    bar_height = 30  # Height of the progress bar
    spacing = 50     # Spacing between bars
    svg_elements = []  # List to store SVG elements
    
    svg_elements.append('<svg width="500" height="300" xmlns="http://www.w3.org/2000/svg">')

    y_position = 20  # Y position to start rendering
    
    for key, statuses in data.items():
        text_y = y_position + 15  # Position text slightly above the bar
        
        # Render the dataset name
        svg_elements.append(f'<text x="10" y="{text_y}" font-size="16" fill="black">{key}</text>')
        y_position += 20

        # ---- Download Progress ----
        download_status = statuses.get("downloadstatus", "unknown")

        if isinstance(download_status, dict) and "percent" in download_status:
            percent = download_status["percent"]
            bar_fill_width = int((percent / 100) * svg_width)

            # Background bar with grey color
            svg_elements.append(f'<rect x="10" y="{y_position}" width="{svg_width}" height="{bar_height}" fill="#ddd" rx="5" ry="5"/>')
            
            # Filled progress bar
            svg_elements.append(f'<rect x="10" y="{y_position}" width="{bar_fill_width}" height="{bar_height}" fill="green" rx="5" ry="5"/>')

            # Percentage text
            svg_elements.append(f'<text x="{svg_width + 20}" y="{y_position + 20}" font-size="16" fill="black">{percent}%</text>')

        else:
            # Simply display text status if percentage is not present
            svg_elements.append(f'<text x="10" y="{y_position + 20}" font-size="16" fill="black">Download Status: {download_status}</text>')

        y_position += spacing

        # ---- Read Status ----
        read_status = statuses.get("readstatus", "unknown")

        color = "green" if read_status == "done" else "orange"
        svg_elements.append(f'<text x="10" y="{y_position}" font-size="16" fill="{color}">Read Status: {read_status}</text>')

        y_position += spacing

    svg_elements.append('</svg>')

    return "\n".join(svg_elements)