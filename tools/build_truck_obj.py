import math, os

os.makedirs('web/models', exist_ok=True)

class OBJBuilder:
    def __init__(self):
        self.vertices = []
        self.normals = []
        self.uvs = []
        self.groups = {}
        self.current_group = "default"

    def set_group(self, name):
        self.current_group = name
        if name not in self.groups:
            self.groups[name] = []

    def add_v(self, x, y, z):
        self.vertices.append((x, y, z))
        return len(self.vertices)

    def add_vn(self, nx, ny, nz):
        self.normals.append((nx, ny, nz))
        return len(self.normals)

    def add_vt(self, u, v):
        self.uvs.append((u, v))
        return len(self.uvs)

    def add_quad(self, v1, v2, v3, v4, vt1, vt2, vt3, vt4, vn):
        if self.current_group not in self.groups:
            self.groups[self.current_group] = []
        self.groups[self.current_group].append((v1, vt1, vn, v2, vt2, vn, v3, vt3, vn))
        self.groups[self.current_group].append((v1, vt1, vn, v3, vt3, vn, v4, vt4, vn))

    def add_box(self, x, y, z, w, h, d, group="cab"):
        self.set_group(group)
        hw, hh, hd = w/2, h/2, d/2
        
        # Front Face
        v1 = self.add_v(x - hw, y - hh, z - hd)
        v2 = self.add_v(x + hw, y - hh, z - hd)
        v3 = self.add_v(x + hw, y + hh, z - hd)
        v4 = self.add_v(x - hw, y + hh, z - hd)
        vn_f = self.add_vn(0, 0, -1)
        vt1 = self.add_vt(0, 0); vt2 = self.add_vt(1, 0); vt3 = self.add_vt(1, 1); vt4 = self.add_vt(0, 1)
        self.add_quad(v1, v2, v3, v4, vt1, vt2, vt3, vt4, vn_f)

        # Back Face
        v5 = self.add_v(x + hw, y - hh, z + hd)
        v6 = self.add_v(x - hw, y - hh, z + hd)
        v7 = self.add_v(x - hw, y + hh, z + hd)
        v8 = self.add_v(x + hw, y + hh, z + hd)
        vn_b = self.add_vn(0, 0, 1)
        self.add_quad(v5, v6, v7, v8, vt1, vt2, vt3, vt4, vn_b)

        # Left Face
        vn_l = self.add_vn(-1, 0, 0)
        self.add_quad(v6, v1, v4, v7, vt1, vt2, vt3, vt4, vn_l)

        # Right Face
        vn_r = self.add_vn(1, 0, 0)
        self.add_quad(v2, v5, v8, v3, vt1, vt2, vt3, vt4, vn_r)

        # Top Face
        vn_t = self.add_vn(0, 1, 0)
        self.add_quad(v4, v3, v8, v7, vt1, vt2, vt3, vt4, vn_t)

        # Bottom Face
        vn_bt = self.add_vn(0, -1, 0)
        self.add_quad(v6, v5, v2, v1, vt1, vt2, vt3, vt4, vn_bt)

    def add_cylinder(self, x, y, z, r, length, segments=16, axis="z", group="chrome"):
        self.set_group(group)
        # Cylinder along axis
        prev_v1 = None
        for i in range(segments + 1):
            angle = (i / segments) * math.pi * 2
            dx = math.cos(angle) * r
            dy = math.sin(angle) * r
            if axis == "z":
                v_front = self.add_v(x + dx, y + dy, z - length/2)
                v_back = self.add_v(x + dx, y + dy, z + length/2)
                vn = self.add_vn(math.cos(angle), math.sin(angle), 0)
            elif axis == "x":
                v_front = self.add_v(x - length/2, y + dy, z + dx)
                v_back = self.add_v(x + length/2, y + dy, z + dx)
                vn = self.add_vn(0, math.sin(angle), math.cos(angle))
            u = i / segments
            vt_f = self.add_vt(u, 0)
            vt_b = self.add_vt(u, 1)

            if prev_v1 is not None:
                self.groups[self.current_group].append((prev_v1[0], prev_v1[2], prev_v1[4], v_front, vt_f, vn, v_back, vt_b, vn))
                self.groups[self.current_group].append((prev_v1[0], prev_v1[2], prev_v1[4], v_back, vt_b, vn, prev_v1[1], prev_v1[3], prev_v1[4]))
            prev_v1 = (v_front, v_back, vt_f, vt_b, vn)

    def save(self, filepath):
        with open(filepath, 'w') as f:
            f.write("# Aster Viento High-Definition 3D Model\n")
            for v in self.vertices:
                f.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")
            for vt in self.uvs:
                f.write(f"vt {vt[0]:.4f} {vt[1]:.4f}\n")
            for vn in self.normals:
                f.write(f"vn {vn[0]:.4f} {vn[1]:.4f} {vn[2]:.4f}\n")
            for grp, tris in self.groups.items():
                f.write(f"g {grp}\n")
                f.write(f"usemtl {grp}\n")
                for tri in tris:
                    f.write(f"f {tri[0]}/{tri[1]}/{tri[2]} {tri[3]}/{tri[4]}/{tri[5]} {tri[6]}/{tri[7]}/{tri[8]}\n")
        print(f"Saved {filepath} with {len(self.vertices)} vertices and {sum(len(t) for t in self.groups.values())} triangles.")

# Build 1: High-Poly European Semi Cab
cab = OBJBuilder()
# Chassis rails
cab.add_box(-0.6, 0.65, -0.6, 0.22, 0.35, 6.2, "chassis")
cab.add_box(0.6, 0.65, -0.6, 0.22, 0.35, 6.2, "chassis")
# Main sculpted cab
cab.add_box(0, 1.9, -1.3, 2.55, 1.95, 2.6, "cab_paint")
# High-rise Globetrotter roof
cab.add_box(0, 3.15, -1.35, 2.48, 0.9, 2.35, "cab_paint")
cab.add_box(0, 3.7, -1.4, 2.42, 0.38, 1.4, "cab_trim")
# Aerodynamic corner wind deflectors
cab.add_box(-1.28, 1.85, -2.4, 0.15, 1.7, 0.6, "cab_paint")
cab.add_box(1.28, 1.85, -2.4, 0.15, 1.7, 0.6, "cab_paint")
# Front Grille & Louver Mask
cab.add_box(0, 1.55, -2.62, 2.35, 1.45, 0.18, "cab_grille")
# Sunvisor
cab.add_box(0, 2.95, -2.65, 2.44, 0.22, 0.38, "cab_trim")
# Chrome Roof Air Horns
cab.add_cylinder(-0.85, 3.75, -2.1, 0.08, 0.9, 12, "z", "chrome")
cab.add_cylinder(0.85, 3.75, -2.1, 0.08, 0.9, 12, "z", "chrome")
# Cylindrical Chrome Fuel Tank
cab.add_cylinder(-1.18, 0.65, -0.4, 0.44, 2.4, 20, "z", "chrome")
cab.add_box(1.18, 0.65, -0.4, 0.55, 0.5, 2.0, "chassis")
# Side Aerodynamic Skirts
cab.add_box(-1.26, 0.65, -0.6, 0.16, 0.58, 2.4, "cab_paint")
cab.add_box(1.26, 0.65, -0.6, 0.16, 0.58, 2.4, "cab_paint")
# Front Bumper
cab.add_box(0, 0.75, -2.7, 2.6, 0.65, 0.45, "cab_trim")
# Save Cab Model
cab.save('web/models/truck_cab.obj')

# Build 2: 3D Corrugated Semi-Trailer
trailer = OBJBuilder()
# Chassis & I-Beams
trailer.add_box(0, 0.85, 5.0, 1.6, 0.28, 10.5, "chassis")
# Main Container Box
trailer.add_box(0, 2.7, 5.0, 2.6, 3.1, 9.8, "trailer_body")
# 3D Corrugation Flutes (Left & Right Sides)
for z in [x * 0.28 for x in range(32)]:
    trailer.add_box(-1.32, 2.7, 0.5 + z, 0.05, 2.95, 0.14, "trailer_corrugated")
    trailer.add_box(1.32, 2.7, 0.5 + z, 0.05, 2.95, 0.14, "trailer_corrugated")
# Rear Hazard Chevron Underrun Bumper
trailer.add_box(0, 0.55, 9.9, 2.5, 0.24, 0.12, "trailer_bumper")
trailer.save('web/models/truck_trailer.obj')

# Build 3: Heavy-Duty Concave Alloy Wheel Rim & Tire
wheel = OBJBuilder()
wheel.add_cylinder(0, 0, 0, 0.56, 0.38, 24, "x", "tire")
wheel.add_cylinder(0.12, 0, 0, 0.38, 0.14, 20, "x", "alloy_rim")
wheel.add_cylinder(0.18, 0, 0, 0.16, 0.06, 16, "x", "chrome_hub")
# 10 3D Chrome Lug Nuts
for i in range(10):
    a = (i / 10) * math.pi * 2
    ny = math.cos(a) * 0.26
    nz = math.sin(a) * 0.26
    wheel.add_box(0.18, ny, nz, 0.04, 0.04, 0.04, "chrome_nuts")
wheel.save('web/models/wheel_alloy.obj')

print("All HD 3D truck models generated successfully.")
