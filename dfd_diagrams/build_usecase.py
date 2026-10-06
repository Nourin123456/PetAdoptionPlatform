import os
import subprocess

OUTPUT_DIR = r"c:\Users\navee\OneDrive\Desktop\PetAdoptionPlatform\dfd_diagrams"
os.makedirs(OUTPUT_DIR, exist_ok=True)

FONT_FAMILY = "'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif"

def draw_stick_figure(svg, x, y, label, scale=1.0):
    head_radius = 24 * scale
    head_cy = y - 48 * scale
    torso_top = head_cy + head_radius
    waist_y = y + 60 * scale
    arm_half_w = 42 * scale
    leg_w = 34 * scale
    leg_bottom_y = waist_y + 70 * scale
    label_y = leg_bottom_y + 28 * scale

    # Head
    svg.append(f'  <circle cx="{x}" cy="{head_cy}" r="{head_radius}" fill="#ffffff" stroke="#000000" stroke-width="1.8"/>')
    # Torso
    svg.append(f'  <line x1="{x}" y1="{torso_top}" x2="{x}" y2="{waist_y}" stroke="#000000" stroke-width="1.8"/>')
    # Arms
    svg.append(f'  <line x1="{x - arm_half_w}" y1="{y}" x2="{x + arm_half_w}" y2="{y}" stroke="#000000" stroke-width="1.8"/>')
    # Legs
    svg.append(f'  <line x1="{x}" y1="{waist_y}" x2="{x - leg_w}" y2="{leg_bottom_y}" stroke="#000000" stroke-width="1.8"/>')
    svg.append(f'  <line x1="{x}" y1="{waist_y}" x2="{x + leg_w}" y2="{leg_bottom_y}" stroke="#000000" stroke-width="1.8"/>')
    # Label
    svg.append(f'  <text x="{x}" y="{label_y}" font-family="{FONT_FAMILY}" font-size="15.5" font-weight="bold" text-anchor="middle" fill="#000000">{label}</text>')


def generate_usecase_diagram_standard():
    """
    Variant 1: 3 Actors (Adopter on Left, Shelter and Admin on Right).
    Reflects the architecture where Shelter manages all pet delivery & transport.
    """
    w, h = 1180, 1320
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" style="background-color: #ffffff; font-family: {FONT_FAMILY};">',
        '  <rect width="100%" height="100%" fill="#ffffff"/>'
    ]

    # System boundary box
    box_x = 370
    box_y = 35
    box_w = 440
    box_h = 1240
    svg.append(f'  <!-- System Boundary -->')
    svg.append(f'  <rect x="{box_x}" y="{box_y}" width="{box_w}" height="{box_h}" fill="#ffffff" stroke="#000000" stroke-width="2.2"/>')

    # Title at top of system box
    svg.append(f'  <text x="{box_x + box_w/2}" y="{box_y + 36}" font-size="18" font-weight="bold" text-anchor="middle" fill="#000000" letter-spacing="1">PET ADOPTION</text>')
    svg.append(f'  <text x="{box_x + box_w/2}" y="{box_y + 60}" font-size="18" font-weight="bold" text-anchor="middle" fill="#000000" letter-spacing="1">SYSTEM</text>')

    # 14 core use cases representing full architecture
    use_cases = [
        "Register / Login",
        "View / Manage Profile",
        "Search & Browse Pets",
        "View Pet Details",
        "Submit Adoption Request",
        "Pay Online / Confirm Order",
        "Track Delivery Status",
        "Send Inquiries & Messages",
        "Manage Pet Listings",
        "Review & Approve Requests",
        "Schedule Pet Delivery",
        "Update Live Transport Status",
        "Verify & Approve Shelters",
        "Monitor Platform Reports",
        "Logout"
    ]

    num_uc = len(use_cases)
    start_y = box_y + 105
    spacing = (box_h - 150) / num_uc

    uc_coords = []
    rx, ry = 145, 23
    cx = box_x + box_w / 2

    # Actors positions (chest points)
    adopter_x, adopter_y = 120, 490
    shelter_x, shelter_y = 1050, 430
    admin_x, admin_y = 1050, 1030

    associations = {
        0: [('adopter', adopter_x, adopter_y), ('shelter', shelter_x, shelter_y), ('admin', admin_x, admin_y)],
        1: [('adopter', adopter_x, adopter_y), ('shelter', shelter_x, shelter_y)],
        2: [('adopter', adopter_x, adopter_y)],
        3: [('adopter', adopter_x, adopter_y)],
        4: [('adopter', adopter_x, adopter_y), ('shelter', shelter_x, shelter_y)],
        5: [('adopter', adopter_x, adopter_y)],
        6: [('adopter', adopter_x, adopter_y), ('shelter', shelter_x, shelter_y)],
        7: [('adopter', adopter_x, adopter_y), ('shelter', shelter_x, shelter_y)],
        8: [('shelter', shelter_x, shelter_y), ('admin', admin_x, admin_y)],
        9: [('shelter', shelter_x, shelter_y)],
        10: [('shelter', shelter_x, shelter_y)],
        11: [('shelter', shelter_x, shelter_y)],
        12: [('admin', admin_x, admin_y)],
        13: [('admin', admin_x, admin_y), ('shelter', shelter_x, shelter_y)],
        14: [('adopter', adopter_x, adopter_y), ('shelter', shelter_x, shelter_y), ('admin', admin_x, admin_y)]
    }

    for i, name in enumerate(use_cases):
        cy = start_y + i * spacing + ry
        uc_coords.append((cx, cy, name))

    # Draw Association Lines
    svg.append("  <!-- Association Lines -->")
    for i, (ux, uy, _) in enumerate(uc_coords):
        actors = associations.get(i, [])
        for role, ax, ay in actors:
            if role == 'adopter':
                target_x = ux - rx
                target_y = uy
            else:
                target_x = ux + rx
                target_y = uy
            svg.append(f'  <line x1="{ax}" y1="{ay}" x2="{target_x}" y2="{target_y}" stroke="#000000" stroke-width="1.3"/>')

    # Draw Use Case Ovals & Text
    svg.append("  <!-- Use Case Ovals -->")
    for i, (ux, uy, name) in enumerate(uc_coords):
        svg.append(f'  <ellipse cx="{ux}" cy="{uy}" rx="{rx}" ry="{ry}" fill="#ffffff" stroke="#000000" stroke-width="1.7"/>')
        svg.append(f'  <text x="{ux}" y="{uy + 5}" font-size="14" font-weight="normal" text-anchor="middle" fill="#000000">{name}</text>')

    # Draw Actors (Stick Figures)
    svg.append("  <!-- Actors -->")
    draw_stick_figure(svg, adopter_x, adopter_y, "Adopter", scale=1.0)
    draw_stick_figure(svg, shelter_x, shelter_y, "Shelter", scale=1.0)
    draw_stick_figure(svg, admin_x, admin_y, "Admin", scale=1.0)

    svg.append("</svg>")
    return "\n".join(svg)


def generate_usecase_diagram_balanced():
    """
    Variant 2: Balanced Layout (Adopter on Left | Shelter & Admin on Right)
    """
    w, h = 1180, 1320
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" style="background-color: #ffffff; font-family: {FONT_FAMILY};">',
        '  <rect width="100%" height="100%" fill="#ffffff"/>'
    ]

    # System boundary box
    box_x = 370
    box_y = 35
    box_w = 440
    box_h = 1240
    svg.append(f'  <!-- System Boundary -->')
    svg.append(f'  <rect x="{box_x}" y="{box_y}" width="{box_w}" height="{box_h}" fill="#ffffff" stroke="#000000" stroke-width="2.2"/>')

    # Title
    svg.append(f'  <text x="{box_x + box_w/2}" y="{box_y + 36}" font-size="18" font-weight="bold" text-anchor="middle" fill="#000000" letter-spacing="1">PET ADOPTION</text>')
    svg.append(f'  <text x="{box_x + box_w/2}" y="{box_y + 60}" font-size="18" font-weight="bold" text-anchor="middle" fill="#000000" letter-spacing="1">SYSTEM</text>')

    use_cases = [
        "Register / Login",
        "View / Manage Profile",
        "Search & Browse Pets",
        "View Pet Details",
        "Submit Adoption Request",
        "Pay Online / Confirm Order",
        "Track Delivery Status",
        "Send Inquiries & Messages",
        "Manage Pet Listings",
        "Review & Approve Requests",
        "Schedule Pet Delivery",
        "Update Live Transport Status",
        "Verify & Approve Shelters",
        "Monitor Platform Reports",
        "Logout"
    ]

    num_uc = len(use_cases)
    start_y = box_y + 105
    spacing = (box_h - 150) / num_uc

    uc_coords = []
    rx, ry = 145, 23
    cx = box_x + box_w / 2

    # Actors: Adopter on Left, Shelter & Admin on Right
    adopter_x, adopter_y = 120, 520
    shelter_x, shelter_y = 1050, 410
    admin_x, admin_y = 1050, 1020

    associations = {
        0: [('left', adopter_x, adopter_y), ('right', shelter_x, shelter_y), ('right', admin_x, admin_y)],
        1: [('left', adopter_x, adopter_y), ('right', shelter_x, shelter_y)],
        2: [('left', adopter_x, adopter_y)],
        3: [('left', adopter_x, adopter_y)],
        4: [('left', adopter_x, adopter_y), ('right', shelter_x, shelter_y)],
        5: [('left', adopter_x, adopter_y)],
        6: [('left', adopter_x, adopter_y), ('right', shelter_x, shelter_y)],
        7: [('left', adopter_x, adopter_y), ('right', shelter_x, shelter_y)],
        8: [('right', shelter_x, shelter_y), ('right', admin_x, admin_y)],
        9: [('right', shelter_x, shelter_y)],
        10: [('right', shelter_x, shelter_y)],
        11: [('right', shelter_x, shelter_y)],
        12: [('right', admin_x, admin_y)],
        13: [('right', admin_x, admin_y), ('right', shelter_x, shelter_y)],
        14: [('left', adopter_x, adopter_y), ('right', shelter_x, shelter_y), ('right', admin_x, admin_y)]
    }

    for i, name in enumerate(use_cases):
        cy = start_y + i * spacing + ry
        uc_coords.append((cx, cy, name))

    # Draw Association Lines
    svg.append("  <!-- Association Lines -->")
    for i, (ux, uy, _) in enumerate(uc_coords):
        actors = associations.get(i, [])
        for side, ax, ay in actors:
            if side == 'left':
                target_x = ux - rx
                target_y = uy
            else:
                target_x = ux + rx
                target_y = uy
            svg.append(f'  <line x1="{ax}" y1="{ay}" x2="{target_x}" y2="{target_y}" stroke="#000000" stroke-width="1.3"/>')

    # Draw Use Case Ovals & Text
    svg.append("  <!-- Use Case Ovals -->")
    for i, (ux, uy, name) in enumerate(uc_coords):
        svg.append(f'  <ellipse cx="{ux}" cy="{uy}" rx="{rx}" ry="{ry}" fill="#ffffff" stroke="#000000" stroke-width="1.7"/>')
        svg.append(f'  <text x="{ux}" y="{uy + 5}" font-size="14" font-weight="normal" text-anchor="middle" fill="#000000">{name}</text>')

    # Draw Actors
    svg.append("  <!-- Actors -->")
    draw_stick_figure(svg, adopter_x, adopter_y, "Adopter", scale=1.0)
    draw_stick_figure(svg, shelter_x, shelter_y, "Shelter", scale=1.0)
    draw_stick_figure(svg, admin_x, admin_y, "Admin", scale=1.0)

    svg.append("</svg>")
    return "\n".join(svg)


# Generate both SVGs
standard_svg = generate_usecase_diagram_standard()
standard_path = os.path.join(OUTPUT_DIR, "use_case_diagram.svg")
with open(standard_path, "w", encoding="utf-8") as f:
    f.write(standard_svg)

balanced_svg = generate_usecase_diagram_balanced()
balanced_path = os.path.join(OUTPUT_DIR, "use_case_diagram_balanced.svg")
with open(balanced_path, "w", encoding="utf-8") as f:
    f.write(balanced_svg)

print("SVGs generated.")

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

def render_png(svg_str, out_png_path, temp_html_name):
    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ background: #ffffff; display: flex; justify-content: flex-start; align-items: flex-start; }}
    svg {{ display: block; }}
  </style>
</head>
<body>
{svg_str}
</body>
</html>"""
    temp_html = os.path.join(OUTPUT_DIR, temp_html_name)
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    cmd = [
        EDGE_PATH,
        "--headless",
        "--disable-gpu",
        "--hide-scrollbars",
        "--window-size=1220,1370",
        f"--screenshot={out_png_path}",
        f"file:///{temp_html.replace(os.sep, '/')}"
    ]
    subprocess.run(cmd, capture_output=True, text=True, timeout=35)
    if os.path.exists(temp_html):
        os.remove(temp_html)
    print(f"Rendered {out_png_path}: exists={os.path.exists(out_png_path)}")

render_png(standard_svg, os.path.join(OUTPUT_DIR, "use_case_diagram.png"), "temp_uc_std.html")
render_png(balanced_svg, os.path.join(OUTPUT_DIR, "use_case_diagram_balanced.png"), "temp_uc_bal.html")

print("All use case diagrams generated.")
