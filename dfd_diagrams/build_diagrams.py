import os
import subprocess

OUTPUT_DIR = r"c:\Users\navee\OneDrive\Desktop\PetAdoptionPlatform\dfd_diagrams"
os.makedirs(OUTPUT_DIR, exist_ok=True)

FONT_FAMILY = "'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif"

def generate_dfd_level_0():
    """
    Context Level Data Flow Diagram (DFD Level 0) for 3 Entities:
    - Admin (Top)
    - Adopter (Left)
    - Shelter (Right)
    Central Process: Pet Adoption System (0.0)
    All pet delivery & handover logistics are fully handled by the Shelter.
    """
    w, h = 960, 600
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" style="background-color: #ffffff; font-family: {FONT_FAMILY};">',
        '  <rect width="100%" height="100%" fill="#ffffff"/>',
        """  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#000000"/>
    </marker>
  </defs>
  <text x="480" y="32" font-size="16" font-weight="bold" text-anchor="middle" fill="#000000">DFD level 0 Diagram</text>
"""
    ]

    # External Entities
    # Top: Admin
    svg.append("""  <!-- Admin Entity -->
  <rect x="390" y="60" width="180" height="70" fill="#ffffff" stroke="#000000" stroke-width="1.8"/>
  <text x="480" y="102" font-size="16" font-weight="bold" text-anchor="middle" fill="#000000">Admin</text>
""")

    # Left: Adopter
    svg.append("""  <!-- Adopter Entity -->
  <rect x="60" y="280" width="180" height="70" fill="#ffffff" stroke="#000000" stroke-width="1.8"/>
  <text x="150" y="322" font-size="16" font-weight="bold" text-anchor="middle" fill="#000000">Adopter</text>
""")

    # Right: Shelter
    svg.append("""  <!-- Shelter Entity -->
  <rect x="720" y="280" width="180" height="70" fill="#ffffff" stroke="#000000" stroke-width="1.8"/>
  <text x="810" y="322" font-size="16" font-weight="bold" text-anchor="middle" fill="#000000">Shelter</text>
""")

    # Central System Process (0.0)
    svg.append("""  <!-- Central Process: Pet Adoption System -->
  <ellipse cx="480" cy="315" rx="140" ry="70" fill="#ffffff" stroke="#000000" stroke-width="1.8"/>
  <text x="480" y="310" font-size="16" font-weight="bold" text-anchor="middle" fill="#000000">Pet Adoption</text>
  <text x="480" y="332" font-size="16" font-weight="bold" text-anchor="middle" fill="#000000">System</text>
""")

    # Arrows between Admin & Center
    svg.append("""  <!-- Admin to Center -->
  <line x1="445" y1="130" x2="445" y2="245" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)"/>
  <text x="400" y="190" font-size="13" font-style="normal" text-anchor="middle" fill="#000000">Request</text>

  <!-- Center to Admin -->
  <line x1="515" y1="245" x2="515" y2="130" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)"/>
  <text x="560" y="190" font-size="13" font-style="normal" text-anchor="middle" fill="#000000">Response</text>
""")

    # Arrows between Adopter & Center
    svg.append("""  <!-- Adopter to Center -->
  <line x1="240" y1="295" x2="340" y2="295" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)"/>
  <text x="290" y="283" font-size="13" font-style="normal" text-anchor="middle" fill="#000000">Request</text>

  <!-- Center to Adopter -->
  <line x1="340" y1="335" x2="240" y2="335" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)"/>
  <text x="290" y="357" font-size="13" font-style="normal" text-anchor="middle" fill="#000000">Response</text>
""")

    # Arrows between Shelter & Center
    svg.append("""  <!-- Shelter to Center -->
  <line x1="720" y1="295" x2="620" y2="295" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)"/>
  <text x="670" y="283" font-size="13" font-style="normal" text-anchor="middle" fill="#000000">Request</text>

  <!-- Center to Shelter -->
  <line x1="620" y1="335" x2="720" y2="335" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)"/>
  <text x="670" y="357" font-size="13" font-style="normal" text-anchor="middle" fill="#000000">Response</text>
""")

    # Bottom notes emphasizing Shelter handles transport & delivery
    svg.append("""  <!-- Architecture Footer Note -->
  <rect x="230" y="470" width="500" height="50" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.2"/>
  <text x="480" y="493" font-size="12.5" font-weight="600" text-anchor="middle" fill="#334155">3-Actor Architecture: Adopter, Shelter, and Administrator</text>
  <text x="480" y="510" font-size="11.5" font-style="italic" text-anchor="middle" fill="#64748b">Pet Delivery &amp; Transport Scheduling are fully managed by the Shelter</text>
""")

    svg.append("</svg>")
    return "\n".join(svg)


def generate_dfd_level_1_or_2(title, entity_name, auth_store, processes_and_stores):
    w, h = 980, 560
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" style="background-color: #ffffff; font-family: {FONT_FAMILY};">',
        '  <rect width="100%" height="100%" fill="#ffffff"/>',
        """  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#000000"/>
    </marker>
  </defs>
"""
    ]
    svg.append(f'  <text x="490" y="34" font-size="16" font-weight="bold" text-anchor="middle" fill="#000000">{title}</text>\n')

    # Entity Box
    ent_x, ent_y, ent_w, ent_h = 35, 140, 110, 60
    svg.append(f"""  <!-- External Entity -->
  <rect x="{ent_x}" y="{ent_y}" width="{ent_w}" height="{ent_h}" fill="#ffffff" stroke="#000000" stroke-width="1.8"/>
  <text x="{ent_x + ent_w/2}" y="{ent_y + 36}" font-size="14.5" font-weight="bold" text-anchor="middle" fill="#000000">{entity_name}</text>
""")

    # Login Process 1.0
    log_cx, log_cy, log_rx, log_ry = 230, 170, 48, 30
    svg.append(f"""  <!-- Process 1.0: Login -->
  <ellipse cx="{log_cx}" cy="{log_cy}" rx="{log_rx}" ry="{log_ry}" fill="#ffffff" stroke="#000000" stroke-width="1.8"/>
  <text x="{log_cx}" y="{log_cy - 4}" font-size="12" font-weight="bold" text-anchor="middle" fill="#000000">1.0</text>
  <text x="{log_cx}" y="{log_cy + 12}" font-size="12" font-weight="normal" text-anchor="middle" fill="#000000">Login</text>
""")

    # Arrow: Entity -> Login
    svg.append(f"""  <!-- Entity to Login -->
  <line x1="{ent_x + ent_w}" y1="{ent_y + ent_h/2}" x2="{log_cx - log_rx}" y2="{log_cy}" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)"/>
  <text x="165" y="160" font-size="11" font-weight="normal" text-anchor="middle" fill="#000000">Credentials</text>
""")

    # Auth Data Store
    ds_x, ds_y, ds_w, ds_h = 160, 275, 140, 42
    svg.append(f"""  <!-- Auth Data Store -->
  <line x1="{ds_x}" y1="{ds_y}" x2="{ds_x + ds_w}" y2="{ds_y}" stroke="#000000" stroke-width="1.8"/>
  <line x1="{ds_x}" y1="{ds_y + ds_h}" x2="{ds_x + ds_w}" y2="{ds_y + ds_h}" stroke="#000000" stroke-width="1.8"/>
  <text x="{ds_x + ds_w/2}" y="{ds_y + 26}" font-size="12" font-weight="normal" text-anchor="middle" fill="#000000">{auth_store}</text>
""")

    # Arrow: Login <-> Auth Store
    svg.append(f"""  <!-- Login to Auth Store -->
  <line x1="{log_cx}" y1="{log_cy + log_ry}" x2="{log_cx}" y2="{ds_y}" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)"/>
  <text x="{log_cx + 42}" y="240" font-size="10.5" font-weight="normal" text-anchor="start" fill="#000000">Verify</text>
""")

    # Vertical bus line from Login
    bus_x = 340
    svg.append(f"""  <!-- Connection from Login to Sub-processes Bus -->
  <line x1="{log_cx + log_rx}" y1="{log_cy}" x2="{bus_x}" y2="{log_cy}" stroke="#000000" stroke-width="1.5"/>
""")

    # 5 Sub-processes
    p_rx, p_ry = 95, 26
    proc_cx = 490
    y_start = 75
    y_spacing = 88

    store_x = 730
    store_w = 170
    store_h = 42

    bus_top_y = y_start
    bus_bottom_y = y_start + (len(processes_and_stores) - 1) * y_spacing

    svg.append(f"""  <!-- Main Distribution Bus -->
  <line x1="{bus_x}" y1="{bus_top_y}" x2="{bus_x}" y2="{bus_bottom_y}" stroke="#000000" stroke-width="1.5"/>
""")

    for idx, (p_name, s_name) in enumerate(processes_and_stores):
        p_num = f"{idx + 2}.0"
        p_cy = y_start + idx * y_spacing

        svg.append(f"""  <!-- Process {p_num}: {p_name} -->
  <line x1="{bus_x}" y1="{p_cy}" x2="{proc_cx - p_rx}" y2="{p_cy}" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)"/>
  <ellipse cx="{proc_cx}" cy="{p_cy}" rx="{p_rx}" ry="{p_ry}" fill="#ffffff" stroke="#000000" stroke-width="1.8"/>
  <text x="{proc_cx}" y="{p_cy - 7}" font-size="11.5" font-weight="bold" text-anchor="middle" fill="#000000">{p_num}</text>
  <text x="{proc_cx}" y="{p_cy + 9}" font-size="11" font-weight="normal" text-anchor="middle" fill="#000000">{p_name}</text>
""")

        s_y = p_cy - store_h / 2
        svg.append(f"""  <!-- Store for Process {p_num}: {s_name} -->
  <line x1="{proc_cx + p_rx}" y1="{p_cy}" x2="{store_x}" y2="{p_cy}" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)"/>
  <line x1="{store_x}" y1="{s_y}" x2="{store_x + store_w}" y2="{s_y}" stroke="#000000" stroke-width="1.8"/>
  <line x1="{store_x}" y1="{s_y + store_h}" x2="{store_x + store_w}" y2="{s_y + store_h}" stroke="#000000" stroke-width="1.8"/>
  <text x="{store_x + store_w/2}" y="{s_y + 26}" font-size="12" font-weight="normal" text-anchor="middle" fill="#000000">{s_name}</text>
""")

    svg.append("</svg>")
    return "\n".join(svg)


diagram_configs = {
    "dfd_level_0.svg": {
        "generator": generate_dfd_level_0
    },
    "dfd_level_1_admin.svg": {
        "generator": lambda: generate_dfd_level_1_or_2(
            title="DFD level 1 Admin Diagram",
            entity_name="Admin",
            auth_store="Admin Table",
            processes_and_stores=[
                ("View Dashboard & Statistics", "Dashboard"),
                ("Manage Shelter Approvals", "Shelters"),
                ("Manage Pet Listings", "Pets"),
                ("Manage Adoption Requests", "Adoptions"),
                ("Manage Inquiries & Messages", "Messages")
            ]
        )
    },
    "dfd_level_1_shelter.svg": {
        "generator": lambda: generate_dfd_level_1_or_2(
            title="DFD level 1 Shelter Diagram",
            entity_name="Shelter",
            auth_store="Shelter Table",
            processes_and_stores=[
                ("View Shelter Dashboard", "Shelter Dashboard"),
                ("Manage Pet Profiles", "Pets Table"),
                ("Process Adoption Requests", "Adoptions Table"),
                ("Schedule & Manage Delivery", "Adoptions Table"),
                ("View & Reply Messages", "Messages Table")
            ]
        )
    },
    "dfd_level_1_adopter.svg": {
        "generator": lambda: generate_dfd_level_1_or_2(
            title="DFD level 1 Adopter Diagram",
            entity_name="Adopter",
            auth_store="Users Table",
            processes_and_stores=[
                ("Search & Browse Pets", "Pets Table"),
                ("Submit Adoption Request", "Adoptions Table"),
                ("Process Adoption Payment", "Payments Table"),
                ("Track Delivery Milestones", "Adoptions Table"),
                ("Send Messages & Inquiries", "Messages Table")
            ]
        )
    },
    "dfd_level_2_admin.svg": {
        "generator": lambda: generate_dfd_level_1_or_2(
            title="DFD level 2 Admin Diagram",
            entity_name="Admin",
            auth_store="Admin Credentials",
            processes_and_stores=[
                ("Verify Shelter Documents", "Pending Shelters"),
                ("Approve or Reject Shelter", "Shelters Table"),
                ("Audit Pet Inventory", "Pets Table"),
                ("Review Adoption Records", "Adoptions Table"),
                ("Generate System Analytics", "Analytics Reports")
            ]
        )
    },
    "dfd_level_2_shelter.svg": {
        "generator": lambda: generate_dfd_level_1_or_2(
            title="DFD level 2 Shelter Operations Diagram",
            entity_name="Shelter",
            auth_store="Shelter Accounts",
            processes_and_stores=[
                ("Add & Update Pet Details", "Pets Table"),
                ("Validate Adoption Application", "Adoptions Table"),
                ("Verify Fee & Payment Status", "Payment Records"),
                ("Schedule Delivery & Set Transit Status", "Adoptions Table"),
                ("Confirm Handover & Delivery", "Adoptions Table")
            ]
        )
    }
}

for filename, cfg in diagram_configs.items():
    content = cfg["generator"]()
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Generated {filepath}")

# Remove obsolete Transport diagrams if they exist
for old_file in ["dfd_level_1_transport.svg", "dfd_level_1_transport.png", "dfd_level_2_transport.svg", "dfd_level_2_transport.png"]:
    p = os.path.join(OUTPUT_DIR, old_file)
    if os.path.exists(p):
        os.remove(p)
        print(f"Removed legacy file {p}")

print("All DFD SVGs generated successfully.")

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

def render_png(svg_path, out_png_path, w=1080, h=650):
    with open(svg_path, "r", encoding="utf-8") as f:
        svg_str = f.read()

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
    temp_html = svg_path + ".temp.html"
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    cmd = [
        EDGE_PATH,
        "--headless",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--window-size={w},{h}",
        f"--screenshot={out_png_path}",
        f"file:///{temp_html.replace(os.sep, '/')}"
    ]
    subprocess.run(cmd, capture_output=True, text=True, timeout=35)
    if os.path.exists(temp_html):
        os.remove(temp_html)
    print(f"Rendered {out_png_path}: exists={os.path.exists(out_png_path)}")

for filename in diagram_configs.keys():
    svg_p = os.path.join(OUTPUT_DIR, filename)
    png_p = os.path.join(OUTPUT_DIR, filename.replace(".svg", ".png"))
    render_png(svg_p, png_p)

print("All DFD PNGs generated successfully.")
