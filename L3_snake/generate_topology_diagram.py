#!/usr/bin/env python3
"""
Generate VRF Snake Topology Diagram
Creates an SVG diagram showing the snake topology with external loopback cables
"""

def create_snake_diagram(output_file='vrf_snake_topology.svg'):
    """Create SVG diagram of VRF snake topology"""

    svg_content = []
    svg_content.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg_content.append('<svg width="700" height="1200" xmlns="http://www.w3.org/2000/svg">')

    # Define colors
    box_color = '#424242'
    interface_color = '#2e7d32'
    loopback_color = '#c62828'
    text_color = '#000000'

    # Box dimensions
    box_x = 100
    box_y = 100
    box_width = 250
    box_height = 900

    # Draw main DUT box
    svg_content.append(f'<rect x="{box_x}" y="{box_y}" width="{box_width}" height="{box_height}" '
                      f'fill="#f5f5f5" stroke="{box_color}" stroke-width="3"/>')

    # Interface positions
    y_start = 140
    y_spacing = 60
    interface_width = 100
    interface_height = 35

    # IXIA 1.1 (no box, just text and line)
    ixia1_y = 30
    svg_content.append(f'<text x="{box_x + box_width/2}" y="{ixia1_y}" text-anchor="middle" '
                      f'font-size="14px" font-weight="bold" fill="#01579b">IXIA 1.1</text>')
    svg_content.append(f'<text x="{box_x + box_width/2}" y="{ixia1_y + 15}" text-anchor="middle" '
                      f'font-size="11px" fill="#01579b">192.168.0.1/31</text>')

    # Connection from IXIA1 to Eth0
    svg_content.append(f'<line x1="{box_x + box_width/2}" y1="{ixia1_y + 20}" '
                      f'x2="{box_x + box_width/2}" y2="{y_start}" '
                      f'stroke="#01579b" stroke-width="2"/>')

    # Define interfaces
    interfaces = [
        ('Vrf1', 'Eth0', '192.168.0.0/31', 0),
        ('Vrf1', 'Eth8', '192.168.0.2/31', 8),
        ('Vrf2', 'Eth16', '192.168.0.3/31', 16),
        ('Vrf2', 'Eth24', '192.168.0.4/31', 24),
        ('Vrf3', 'Eth32', '192.168.0.5/31', 32),
        ('Vrf3', 'Eth40', '192.168.0.6/31', 40),
    ]

    y_pos = y_start
    loopback_x = box_x + box_width + 80

    # Draw first 6 interfaces
    for i, (vrf, eth, ip, eth_num) in enumerate(interfaces):
        # Draw interface box
        int_x = box_x + (box_width - interface_width) / 2
        svg_content.append(f'<rect x="{int_x}" y="{y_pos}" width="{interface_width}" height="{interface_height}" '
                          f'fill="#c8e6c9" stroke="{interface_color}" stroke-width="2" rx="5"/>')

        # Add VRF label on left
        if i % 2 == 0:
            svg_content.append(f'<text x="{box_x + 15}" y="{y_pos + 22}" '
                              f'font-size="11px" font-weight="bold" fill="{text_color}">{vrf}</text>')

        # Add interface text
        svg_content.append(f'<text x="{int_x + interface_width/2}" y="{y_pos + 18}" text-anchor="middle" '
                          f'font-size="13px" font-weight="bold" fill="{text_color}">{eth}</text>')
        if ip:
            svg_content.append(f'<text x="{int_x + interface_width/2}" y="{y_pos + 30}" text-anchor="middle" '
                              f'font-size="9px" fill="{text_color}">{ip}</text>')

        # Draw external loopback for Eth8, Eth24, Eth40 (continuous line)
        if eth_num in [8, 24, 40]:
            start_y = y_pos + interface_height/2
            next_y = y_pos + y_spacing + interface_height/2

            # Single continuous path: right -> curve down -> left
            path = f'M {int_x + interface_width} {start_y} '
            path += f'L {loopback_x} {start_y} '
            path += f'Q {loopback_x + 20} {(start_y + next_y)/2} {loopback_x} {next_y} '
            path += f'L {int_x + interface_width} {next_y}'

            svg_content.append(f'<path d="{path}" stroke="{loopback_color}" stroke-width="2" fill="none"/>')

        y_pos += y_spacing

    # Add middle section indicator
    y_pos += 20
    svg_content.append(f'<text x="{box_x + box_width/2}" y="{y_pos}" text-anchor="middle" '
                      f'font-size="20px" fill="{text_color}">⋮</text>')
    svg_content.append(f'<text x="{box_x + box_width/2}" y="{y_pos + 18}" text-anchor="middle" '
                      f'font-size="11px" fill="{text_color}">Vrf4 - Vrf30</text>')
    svg_content.append(f'<text x="{box_x + box_width/2}" y="{y_pos + 30}" text-anchor="middle" '
                      f'font-size="20px" fill="{text_color}">⋮</text>')

    # Continue with last VRFs
    y_pos += 70
    last_interfaces = [
        ('Vrf31', 'Eth480', '', 480),
        ('Vrf31', 'Eth488', '', 488),
        ('Vrf32', 'Eth496', '', 496),
        ('Vrf32', 'Eth504', '192.168.0.65/31', 504),
    ]

    for i, (vrf, eth, ip, eth_num) in enumerate(last_interfaces):
        int_x = box_x + (box_width - interface_width) / 2
        svg_content.append(f'<rect x="{int_x}" y="{y_pos}" width="{interface_width}" height="{interface_height}" '
                          f'fill="#c8e6c9" stroke="{interface_color}" stroke-width="2" rx="5"/>')

        if i % 2 == 0:
            svg_content.append(f'<text x="{box_x + 15}" y="{y_pos + 22}" '
                              f'font-size="11px" font-weight="bold" fill="{text_color}">{vrf}</text>')

        svg_content.append(f'<text x="{int_x + interface_width/2}" y="{y_pos + 18}" text-anchor="middle" '
                          f'font-size="13px" font-weight="bold" fill="{text_color}">{eth}</text>')
        if ip:
            svg_content.append(f'<text x="{int_x + interface_width/2}" y="{y_pos + 30}" text-anchor="middle" '
                              f'font-size="9px" fill="{text_color}">{ip}</text>')

        # Draw external loopback for Eth488 (continuous line)
        if eth_num == 488:
            start_y = y_pos + interface_height/2
            next_y = y_pos + y_spacing + interface_height/2

            # Single continuous path
            path = f'M {int_x + interface_width} {start_y} '
            path += f'L {loopback_x} {start_y} '
            path += f'Q {loopback_x + 20} {(start_y + next_y)/2} {loopback_x} {next_y} '
            path += f'L {int_x + interface_width} {next_y}'

            svg_content.append(f'<path d="{path}" stroke="{loopback_color}" stroke-width="2" fill="none"/>')

        y_pos += y_spacing

    # IXIA 2.1 (no box, just text and line - placed outside the DUT box)
    ixia2_y = box_y + box_height + 50
    svg_content.append(f'<line x1="{box_x + box_width/2}" y1="{y_pos - y_spacing + interface_height}" '
                      f'x2="{box_x + box_width/2}" y2="{box_y + box_height}" '
                      f'stroke="#01579b" stroke-width="2"/>')

    svg_content.append(f'<line x1="{box_x + box_width/2}" y1="{box_y + box_height}" '
                      f'x2="{box_x + box_width/2}" y2="{ixia2_y - 20}" '
                      f'stroke="#01579b" stroke-width="2"/>')

    svg_content.append(f'<text x="{box_x + box_width/2}" y="{ixia2_y}" text-anchor="middle" '
                      f'font-size="14px" font-weight="bold" fill="#01579b">IXIA 2.1</text>')
    svg_content.append(f'<text x="{box_x + box_width/2}" y="{ixia2_y + 15}" text-anchor="middle" '
                      f'font-size="11px" fill="#01579b">192.168.0.65/31</text>')

    # Close SVG
    svg_content.append('</svg>')

    # Save the drawing
    with open(output_file, 'w') as f:
        f.write('\n'.join(svg_content))

    print(f"Diagram saved to {output_file}")

if __name__ == "__main__":
    create_snake_diagram()

