#!/usr/bin/env python3
"""
Generate VRF Snake Topology Diagram for 2 DUTs
Creates an SVG diagram showing the snake topology with two DUTs and cross-device connections
"""

def create_2dut_snake_diagram(output_file='vrf_snake_2DUTs_topology.svg'):
    """Create SVG diagram of VRF snake topology for 2 DUTs"""

    svg_content = []
    svg_content.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg_content.append('<svg width="900" height="800" xmlns="http://www.w3.org/2000/svg">')

    # Define colors
    box_color = '#424242'
    interface_color = '#2e7d32'
    loopback_color = '#c62828'
    text_color = '#000000'
    vrf_label_color = '#1565c0'

    # Box dimensions for DUT1 (left) and DUT2 (right)
    dut1_x = 50
    dut2_x = 600
    box_y = 50
    box_width = 200
    box_height = 700

    # Draw DUT1 box
    svg_content.append(f'<rect x="{dut1_x}" y="{box_y}" width="{box_width}" height="{box_height}" '
                      f'fill="#f5f5f5" stroke="{box_color}" stroke-width="3"/>')
    
    # Draw DUT2 box
    svg_content.append(f'<rect x="{dut2_x}" y="{box_y}" width="{box_width}" height="{box_height}" '
                      f'fill="#f5f5f5" stroke="{box_color}" stroke-width="3"/>')

    # Interface dimensions
    interface_width = 80
    interface_height = 30

    # IXIA 1.1 connection to DUT1 Ethernet0
    ixia1_x = dut1_x - 150
    ixia1_y = box_y + 50
    svg_content.append(f'<text x="{ixia1_x}" y="{ixia1_y}" '
                      f'font-size="12px" font-weight="bold" fill="#01579b">192.168.0.1/31</text>')
    svg_content.append(f'<text x="{ixia1_x + 20}" y="{ixia1_y + 15}" '
                      f'font-size="11px" fill="#01579b">IXIA 1.1</text>')
    
    # Arrow from IXIA1 to DUT1 Eth0
    svg_content.append(f'<line x1="{ixia1_x + 100}" y1="{ixia1_y + 5}" '
                      f'x2="{dut1_x}" y2="{ixia1_y + 5}" '
                      f'stroke="#01579b" stroke-width="2" marker-end="url(#arrowblue)"/>')

    # IXIA 2.1 connection to DUT2 Ethernet0
    ixia2_x = dut2_x + box_width + 20
    ixia2_y = box_y + box_height - 50
    svg_content.append(f'<line x1="{dut2_x + box_width}" y1="{ixia2_y + 5}" '
                      f'x2="{ixia2_x}" y2="{ixia2_y + 5}" '
                      f'stroke="#01579b" stroke-width="2" marker-end="url(#arrowblue)"/>')
    
    svg_content.append(f'<text x="{ixia2_x + 10}" y="{ixia2_y}" '
                      f'font-size="12px" font-weight="bold" fill="#01579b">192.168.0.255/31</text>')
    svg_content.append(f'<text x="{ixia2_x + 30}" y="{ixia2_y + 15}" '
                      f'font-size="11px" fill="#01579b">IXIA 2.1</text>')

    # Define arrow markers
    svg_content.insert(2, '<defs>')
    svg_content.insert(3, '<marker id="arrowred" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">')
    svg_content.insert(4, '<path d="M0,0 L0,6 L9,3 z" fill="#c62828" />')
    svg_content.insert(5, '</marker>')
    svg_content.insert(6, '<marker id="arrowblue" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">')
    svg_content.insert(7, '<path d="M0,0 L0,6 L9,3 z" fill="#01579b" />')
    svg_content.insert(8, '</marker>')
    svg_content.insert(9, '</defs>')

    # Starting Y position for interfaces
    y_start = box_y + 50
    y_spacing = 50

    # Draw DUT1 interfaces (Vrf1)
    y_pos = y_start
    
    # DUT1 Eth0 (Vrf1)
    int_x = dut1_x + (box_width - interface_width) / 2
    svg_content.append(f'<rect x="{int_x}" y="{y_pos}" width="{interface_width}" height="{interface_height}" '
                      f'fill="#c8e6c9" stroke="{interface_color}" stroke-width="2" rx="5"/>')
    svg_content.append(f'<text x="{int_x + interface_width/2}" y="{y_pos + 20}" text-anchor="middle" '
                      f'font-size="12px" font-weight="bold" fill="{text_color}">0</text>')
    
    # Vrf1 label on left side of DUT1
    svg_content.append(f'<text x="{dut1_x + 10}" y="{y_pos + 70}" '
                      f'font-size="11px" font-weight="bold" fill="{vrf_label_color}">Vrf1</text>')

    y_pos += y_spacing

    # DUT1 Eth8 (Vrf1) with IP
    svg_content.append(f'<rect x="{int_x}" y="{y_pos}" width="{interface_width}" height="{interface_height}" '
                      f'fill="#c8e6c9" stroke="{interface_color}" stroke-width="2" rx="5"/>')
    svg_content.append(f'<text x="{int_x + interface_width/2}" y="{y_pos + 20}" text-anchor="middle" '
                      f'font-size="12px" font-weight="bold" fill="{text_color}">8</text>')
    svg_content.append(f'<text x="{dut1_x + box_width + 10}" y="{y_pos + 20}" '
                      f'font-size="9px" fill="{text_color}">192.168.0.2/31</text>')

    # Cross-device connection from DUT1 Eth8 to DUT2 Eth8
    dut2_int_x = dut2_x + (box_width - interface_width) / 2
    dut2_y_pos = y_pos
    svg_content.append(f'<line x1="{int_x + interface_width}" y1="{y_pos + interface_height/2}" '
                      f'x2="{dut2_int_x}" y2="{dut2_y_pos + interface_height/2}" '
                      f'stroke="{loopback_color}" stroke-width="2"/>')

    # DUT2 Eth8 (Vrf_1) with IP
    svg_content.append(f'<rect x="{dut2_int_x}" y="{dut2_y_pos}" width="{interface_width}" height="{interface_height}" '
                      f'fill="#c8e6c9" stroke="{interface_color}" stroke-width="2" rx="5"/>')
    svg_content.append(f'<text x="{dut2_int_x + interface_width/2}" y="{dut2_y_pos + 20}" text-anchor="middle" '
                      f'font-size="12px" font-weight="bold" fill="{text_color}">8</text>')
    svg_content.append(f'<text x="{dut2_x + box_width + 10}" y="{dut2_y_pos + 20}" '
                      f'font-size="9px" fill="{text_color}">192.168.0.3/31</text>')
    
    # Vrf1 label on right side of DUT2
    svg_content.append(f'<text x="{dut2_x + box_width - 35}" y="{dut2_y_pos + 70}" '
                      f'font-size="11px" font-weight="bold" fill="{vrf_label_color}">Vrf1</text>')

    y_pos += y_spacing
    dut2_y_pos += y_spacing

    # DUT1 Eth16 (Vrf2)
    svg_content.append(f'<rect x="{int_x}" y="{y_pos}" width="{interface_width}" height="{interface_height}" '
                      f'fill="#c8e6c9" stroke="{interface_color}" stroke-width="2" rx="5"/>')
    svg_content.append(f'<text x="{int_x + interface_width/2}" y="{y_pos + 20}" text-anchor="middle" '
                      f'font-size="12px" font-weight="bold" fill="{text_color}">16</text>')
    svg_content.append(f'<text x="{dut1_x + box_width + 10}" y="{y_pos + 20}" '
                      f'font-size="9px" fill="{text_color}">192.168.0.4/31</text>')
    
    # Vrf2 label
    svg_content.append(f'<text x="{dut1_x + 10}" y="{y_pos + 70}" '
                      f'font-size="11px" font-weight="bold" fill="{vrf_label_color}">Vrf2</text>')

    # DUT2 Eth16 (Vrf_1) with IP
    svg_content.append(f'<rect x="{dut2_int_x}" y="{dut2_y_pos}" width="{interface_width}" height="{interface_height}" '
                      f'fill="#c8e6c9" stroke="{interface_color}" stroke-width="2" rx="5"/>')
    svg_content.append(f'<text x="{dut2_int_x + interface_width/2}" y="{dut2_y_pos + 20}" text-anchor="middle" '
                      f'font-size="12px" font-weight="bold" fill="{text_color}">16</text>')
    svg_content.append(f'<text x="{dut2_x + box_width + 10}" y="{dut2_y_pos + 20}" '
                      f'font-size="9px" fill="{text_color}">192.168.0.5/31</text>')

    # Cross-device connection from DUT1 Eth16 to DUT2 Eth16
    svg_content.append(f'<line x1="{int_x + interface_width}" y1="{y_pos + interface_height/2}" '
                      f'x2="{dut2_int_x}" y2="{dut2_y_pos + interface_height/2}" '
                      f'stroke="{loopback_color}" stroke-width="2"/>')

    y_pos += y_spacing
    dut2_y_pos += y_spacing

    # DUT1 Eth24 (Vrf2)
    svg_content.append(f'<rect x="{int_x}" y="{y_pos}" width="{interface_width}" height="{interface_height}" '
                      f'fill="#c8e6c9" stroke="{interface_color}" stroke-width="2" rx="5"/>')
    svg_content.append(f'<text x="{int_x + interface_width/2}" y="{y_pos + 20}" text-anchor="middle" '
                      f'font-size="12px" font-weight="bold" fill="{text_color}">24</text>')

    # DUT2 Eth24 (Vrf_2) with IP
    svg_content.append(f'<rect x="{dut2_int_x}" y="{dut2_y_pos}" width="{interface_width}" height="{interface_height}" '
                      f'fill="#c8e6c9" stroke="{interface_color}" stroke-width="2" rx="5"/>')
    svg_content.append(f'<text x="{dut2_int_x + interface_width/2}" y="{dut2_y_pos + 20}" text-anchor="middle" '
                      f'font-size="12px" font-weight="bold" fill="{text_color}">24</text>')
    
    # Vrf2 label on right side
    svg_content.append(f'<text x="{dut2_x + box_width - 35}" y="{dut2_y_pos + 70}" '
                      f'font-size="11px" font-weight="bold" fill="{vrf_label_color}">Vrf2</text>')

    # Cross-device connection from DUT1 Eth24 to DUT2 Eth24
    svg_content.append(f'<line x1="{int_x + interface_width}" y1="{y_pos + interface_height/2}" '
                      f'x2="{dut2_int_x}" y2="{dut2_y_pos + interface_height/2}" '
                      f'stroke="{loopback_color}" stroke-width="2"/>')

    # Add ellipsis to indicate more VRFs
    y_pos += y_spacing + 20
    dut2_y_pos += y_spacing + 20
    
    svg_content.append(f'<text x="{dut1_x + box_width/2}" y="{y_pos}" text-anchor="middle" '
                      f'font-size="24px" fill="{text_color}">⋮</text>')
    svg_content.append(f'<text x="{dut1_x + box_width/2}" y="{y_pos + 20}" text-anchor="middle" '
                      f'font-size="24px" fill="{text_color}">⋮</text>')
    svg_content.append(f'<text x="{dut1_x + box_width/2}" y="{y_pos + 40}" text-anchor="middle" '
                      f'font-size="24px" fill="{text_color}">⋮</text>')
    
    svg_content.append(f'<text x="{dut2_x + box_width/2}" y="{dut2_y_pos}" text-anchor="middle" '
                      f'font-size="24px" fill="{text_color}">⋮</text>')
    svg_content.append(f'<text x="{dut2_x + box_width/2}" y="{dut2_y_pos + 20}" text-anchor="middle" '
                      f'font-size="24px" fill="{text_color}">⋮</text>')
    svg_content.append(f'<text x="{dut2_x + box_width/2}" y="{dut2_y_pos + 40}" text-anchor="middle" '
                      f'font-size="24px" fill="{text_color}">⋮</text>')

    y_pos += 80
    dut2_y_pos += 80

    # DUT1 Eth496 (Vrf32)
    svg_content.append(f'<rect x="{int_x}" y="{y_pos}" width="{interface_width}" height="{interface_height}" '
                      f'fill="#c8e6c9" stroke="{interface_color}" stroke-width="2" rx="5"/>')
    svg_content.append(f'<text x="{int_x + interface_width/2}" y="{y_pos + 20}" text-anchor="middle" '
                      f'font-size="12px" font-weight="bold" fill="{text_color}">496</text>')
    
    # Vrf32 label
    svg_content.append(f'<text x="{dut1_x + 10}" y="{y_pos + 70}" '
                      f'font-size="11px" font-weight="bold" fill="{vrf_label_color}">Vrf32</text>')

    # DUT2 Eth496 (Vrf_32)
    svg_content.append(f'<rect x="{dut2_int_x}" y="{dut2_y_pos}" width="{interface_width}" height="{interface_height}" '
                      f'fill="#c8e6c9" stroke="{interface_color}" stroke-width="2" rx="5"/>')
    svg_content.append(f'<text x="{dut2_int_x + interface_width/2}" y="{dut2_y_pos + 20}" text-anchor="middle" '
                      f'font-size="12px" font-weight="bold" fill="{text_color}">496</text>')

    # Cross-device connection
    svg_content.append(f'<line x1="{int_x + interface_width}" y1="{y_pos + interface_height/2}" '
                      f'x2="{dut2_int_x}" y2="{dut2_y_pos + interface_height/2}" '
                      f'stroke="{loopback_color}" stroke-width="2"/>')

    y_pos += y_spacing
    dut2_y_pos += y_spacing

    # DUT1 Eth504 (Vrf32) with IP
    svg_content.append(f'<rect x="{int_x}" y="{y_pos}" width="{interface_width}" height="{interface_height}" '
                      f'fill="#c8e6c9" stroke="{interface_color}" stroke-width="2" rx="5"/>')
    svg_content.append(f'<text x="{int_x + interface_width/2}" y="{y_pos + 20}" text-anchor="middle" '
                      f'font-size="12px" font-weight="bold" fill="{text_color}">504</text>')
    svg_content.append(f'<text x="{dut1_x + box_width + 10}" y="{y_pos + 20}" '
                      f'font-size="9px" fill="{text_color}">192.168.0.126/31</text>')

    # DUT2 Eth504 (Vrf_32) with IP
    svg_content.append(f'<rect x="{dut2_int_x}" y="{dut2_y_pos}" width="{interface_width}" height="{interface_height}" '
                      f'fill="#c8e6c9" stroke="{interface_color}" stroke-width="2" rx="5"/>')
    svg_content.append(f'<text x="{dut2_int_x + interface_width/2}" y="{dut2_y_pos + 20}" text-anchor="middle" '
                      f'font-size="12px" font-weight="bold" fill="{text_color}">504</text>')
    svg_content.append(f'<text x="{dut2_x + box_width + 10}" y="{dut2_y_pos + 20}" '
                      f'font-size="9px" fill="{text_color}">192.168.0.127/31</text>')
    
    # Vrf32 label on right side
    svg_content.append(f'<text x="{dut2_x + box_width - 40}" y="{dut2_y_pos + 70}" '
                      f'font-size="11px" font-weight="bold" fill="{vrf_label_color}">Vrf32</text>')

    # Cross-device connection
    svg_content.append(f'<line x1="{int_x + interface_width}" y1="{y_pos + interface_height/2}" '
                      f'x2="{dut2_int_x}" y2="{dut2_y_pos + interface_height/2}" '
                      f'stroke="{loopback_color}" stroke-width="2"/>')

    # DUT2 Eth0 (Vrf_32) - connected to IXIA 2.1
    dut2_y_pos += y_spacing
    svg_content.append(f'<rect x="{dut2_int_x}" y="{dut2_y_pos}" width="{interface_width}" height="{interface_height}" '
                      f'fill="#c8e6c9" stroke="{interface_color}" stroke-width="2" rx="5"/>')
    svg_content.append(f'<text x="{dut2_int_x + interface_width/2}" y="{dut2_y_pos + 20}" text-anchor="middle" '
                      f'font-size="12px" font-weight="bold" fill="{text_color}">0</text>')

    # Close SVG
    svg_content.append('</svg>')

    # Save the drawing
    with open(output_file, 'w') as f:
        f.write('\n'.join(svg_content))

    print(f"2-DUT topology diagram saved to {output_file}")

if __name__ == "__main__":
    create_2dut_snake_diagram()
