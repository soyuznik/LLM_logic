"""LLM Generated UML Diagram Builder using Tkinter."""

import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import json
import math

# --- Geometry Helper for Custom Arrowheads ---
def rotate_point(x, y, cx, cy, angle_rad):
    """Rotates a point (x,y) around (cx,cy) by angle_rad."""
    cos_val = math.cos(angle_rad)
    sin_val = math.sin(angle_rad)
    nx = (cos_val * (x - cx)) - (sin_val * (y - cy)) + cx
    ny = (sin_val * (x - cx)) + (cos_val * (y - cy)) + cy
    return nx, ny

def get_arrow_points(x1, y1, x2, y2, shape="triangle", size=15):
    """Calculates polygon coordinates for a rotated shape at the end of the line (x2, y2)."""
    angle = math.atan2(y2 - y1, x2 - x1)
    
    # Define shapes pointing to the right (0 radians) relative to (0,0)
    # The tip is at (0,0), the base is to the left (negative x)
    if shape == "triangle":
        # Tip, Top-Back, Bottom-Back
        points = [(0, 0), (-size, -size/1.5), (-size, size/1.5)]
    elif shape == "diamond":
        # Tip, Top, Back, Bottom
        points = [(0, 0), (-size, -size/2), (-size*2, 0), (-size, size/2)]
    else:
        return []

    rotated_points = []
    for px, py in points:
        # Rotate logic essentially treats (0,0) as the tip (x2,y2)
        # We need to rotate the offsets first, then add to x2,y2
        rx = (px * math.cos(angle)) - (py * math.sin(angle))
        ry = (px * math.sin(angle)) + (py * math.cos(angle))
        rotated_points.extend([x2 + rx, y2 + ry])
        
    return rotated_points

# --- Main UML Box Class ---
class UMLBox:
    def __init__(self, canvas, x, y, name="NewClass", fields=None, methods=None, box_id=None):
        self.canvas = canvas
        self.name = name
        self.fields = fields if fields else []
        self.methods = methods if methods else []
        self.lines = []
        self.id = box_id if box_id else id(self)

        # Visual configuration
        self.width = 140
        self.text_height = 16
        self.padding = 5
        self.header_bg = "#e3f2fd" # Light Blue
        self.body_bg = "#ffffff"   # White
        self.outline_color = "#1565c0"

        # Group ID for moving all items together
        self.group_tag = f"box_{self.id}"

        # Initialize graphics
        self.draw(x, y)

        # Bindings
        self.canvas.tag_bind(self.group_tag, "<Button-1>", self.on_click)
        self.canvas.tag_bind(self.group_tag, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.group_tag, "<Double-Button-1>", self.on_double_click)

    def draw(self, x, y):
        """Draws the box compartments."""
        # Calculate height requirements
        field_h = len(self.fields) * self.text_height + self.padding * 2
        method_h = len(self.methods) * self.text_height + self.padding * 2
        if len(self.fields) == 0: field_h = 10
        if len(self.methods) == 0: method_h = 10
        
        name_h = 30
        total_h = name_h + field_h + method_h

        # Clean up old drawing if exists
        self.canvas.delete(self.group_tag)

        # 1. Main Background Rectangle
        self.rect_item = self.canvas.create_rectangle(
            x, y, x + self.width, y + total_h,
            fill=self.body_bg, outline=self.outline_color, width=2, 
            tags=(self.group_tag, "uml_box")
        )

        # 2. Header (Name)
        self.canvas.create_rectangle(
            x, y, x + self.width, y + name_h,
            fill=self.header_bg, outline=self.outline_color, width=1,
            tags=(self.group_tag, "uml_box")
        )
        self.canvas.create_text(
            x + self.width/2, y + name_h/2,
            text=self.name, font=("Helvetica", 10, "bold"),
            tags=(self.group_tag, "uml_box")
        )

        # 3. Fields
        current_y = y + name_h + self.padding
        for field in self.fields:
            self.canvas.create_text(
                x + 5, current_y,
                text=field, anchor="nw", font=("Courier", 9),
                tags=(self.group_tag, "uml_box")
            )
            current_y += self.text_height

        # Divider between Fields and Methods
        line_y = y + name_h + field_h
        self.canvas.create_line(
            x, line_y, x + self.width, line_y,
            fill=self.outline_color, tags=(self.group_tag, "uml_box")
        )

        # 4. Methods
        current_y = line_y + self.padding
        for method in self.methods:
            self.canvas.create_text(
                x + 5, current_y,
                text=method, anchor="nw", font=("Courier", 9),
                tags=(self.group_tag, "uml_box")
            )
            current_y += self.text_height
        
        # Ensure boxes are above lines
        self.canvas.tag_raise(self.group_tag)

    def on_click(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def on_drag(self, event):
        dx = event.x - self.start_x
        dy = event.y - self.start_y
        self.canvas.move(self.group_tag, dx, dy)
        self.start_x = event.x
        self.start_y = event.y
        
        for line in self.lines:
            line.update_position()

    def on_double_click(self, event):
        EditorWindow(self.canvas.winfo_toplevel(), self)

    def get_coords(self):
        coords = self.canvas.coords(self.rect_item)
        x1, y1, x2, y2 = coords
        return (x1 + x2) / 2, (y1 + y2) / 2

    def to_dict(self):
        coords = self.canvas.coords(self.rect_item)
        return {
            "id": self.id,
            "name": self.name,
            "fields": self.fields,
            "methods": self.methods,
            "x": coords[0],
            "y": coords[1]
        }

# --- Editor Window for Details ---
class EditorWindow(tk.Toplevel):
    def __init__(self, parent, box):
        super().__init__(parent)
        self.title(f"Edit {box.name}")
        self.box = box
        self.geometry("300x400")

        tk.Label(self, text="Class Name:").pack(anchor="w", padx=5)
        self.entry_name = tk.Entry(self)
        self.entry_name.insert(0, box.name)
        self.entry_name.pack(fill="x", padx=5)

        tk.Label(self, text="Fields (one per line):").pack(anchor="w", padx=5)
        self.text_fields = tk.Text(self, height=5)
        self.text_fields.insert("1.0", "\n".join(box.fields))
        self.text_fields.pack(fill="x", padx=5)

        tk.Label(self, text="Methods (one per line):").pack(anchor="w", padx=5)
        self.text_methods = tk.Text(self, height=5)
        self.text_methods.insert("1.0", "\n".join(box.methods))
        self.text_methods.pack(fill="x", padx=5)

        tk.Button(self, text="Save", command=self.save).pack(pady=10)

    def save(self):
        self.box.name = self.entry_name.get()
        f_raw = self.text_fields.get("1.0", tk.END).strip()
        m_raw = self.text_methods.get("1.0", tk.END).strip()
        
        self.box.fields = f_raw.split("\n") if f_raw else []
        self.box.methods = m_raw.split("\n") if m_raw else []
        
        # Redraw box at current position
        coords = self.box.canvas.coords(self.box.rect_item)
        self.box.draw(coords[0], coords[1])
        # Update attached lines
        for line in self.box.lines:
            line.update_position()
            
        self.destroy()

# --- Connection Line Class ---
class UMLLine:
    def __init__(self, canvas, box1, box2, rel_type="Association"):
        self.canvas = canvas
        self.box1 = box1
        self.box2 = box2
        self.rel_type = rel_type
        
        self.line_id = None
        self.head_id = None
        self.box1.lines.append(self)
        self.box2.lines.append(self)
        
        self.update_position()

    def update_position(self):
        x1, y1 = self.box1.get_coords()
        x2, y2 = self.box2.get_coords()
        
        if self.line_id: self.canvas.delete(self.line_id)
        if self.head_id: self.canvas.delete(self.head_id)

        # Style Configuration
        dash = None
        arrow = None
        fill = "black"
        width = 2
        
        # Calculate visual properties based on Relationship Type
        if self.rel_type == "Association":
            arrow = tk.LAST
        elif self.rel_type == "Inheritance":
            pass # Custom head
        elif self.rel_type == "Realization":
            dash = (4, 2)
        elif self.rel_type == "Dependency":
            dash = (4, 2)
            arrow = tk.LAST
        elif self.rel_type == "Aggregation":
            pass # Custom head
        elif self.rel_type == "Composition":
            pass # Custom head

        # Draw the line
        self.line_id = self.canvas.create_line(
            x1, y1, x2, y2, width=width, fill=fill, arrow=arrow, dash=dash
        )
        # Push line to back!
        self.canvas.tag_lower(self.line_id)

        # Draw Custom Heads (Triangle/Diamond)
        poly_points = []
        poly_color = "white" # Default fill
        
        if self.rel_type in ["Inheritance", "Realization"]:
            poly_points = get_arrow_points(x1, y1, x2, y2, "triangle")
            poly_color = "white"
            
        elif self.rel_type in ["Aggregation", "Composition"]:
            poly_points = get_arrow_points(x1, y1, x2, y2, "diamond")
            poly_color = "white" if self.rel_type == "Aggregation" else "black"

        if poly_points:
            self.head_id = self.canvas.create_polygon(
                poly_points, outline="black", fill=poly_color, width=2
            )
            # Push head to back (but above line if needed, usually doesn't matter for filled)
            # self.canvas.tag_lower(self.head_id) 

    def to_dict(self):
        return {
            "start": self.box1.id,
            "end": self.box2.id,
            "type": self.rel_type
        }

# --- Main Application ---
class UMLEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Advanced Python UML Editor")
        self.geometry("1000x700")

        self.boxes = []
        self.lines = []
        self.connect_mode = False
        self.selected_box = None

        # UI Setup
        self.create_toolbar()
        
        self.canvas = tk.Canvas(self, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w").pack(fill="x", side="bottom")

    def create_toolbar(self):
        bar = tk.Frame(self, bg="#eeeeee", height=40)
        bar.pack(fill="x", side="top")

        tk.Button(bar, text="+ Class", command=self.add_class).pack(side="left", padx=5, pady=5)
        
        # Connection Type Selector
        tk.Label(bar, text="Rel:").pack(side="left", padx=2)
        self.rel_type_var = tk.StringVar(value="Association")
        rel_types = ["Association", "Inheritance", "Realization", "Dependency", "Aggregation", "Composition"]
        ttk.OptionMenu(bar, self.rel_type_var, "Association", *rel_types).pack(side="left")

        self.btn_connect = tk.Button(bar, text="Connect", command=self.toggle_connect)
        self.btn_connect.pack(side="left", padx=5)

        tk.Button(bar, text="Export PNG/PS", command=self.export).pack(side="right", padx=5)
        tk.Button(bar, text="Load", command=self.load).pack(side="right", padx=5)
        tk.Button(bar, text="Save", command=self.save).pack(side="right", padx=5)
        tk.Button(bar, text="Clear", command=self.clear, bg="#ffcccb").pack(side="right", padx=5)

    def add_class(self, x=50, y=50, name="Class", fields=None, methods=None, box_id=None):
        b = UMLBox(self.canvas, x, y, name, fields, methods, box_id)
        self.boxes.append(b)

    def toggle_connect(self):
        self.connect_mode = not self.connect_mode
        if self.connect_mode:
            self.btn_connect.config(relief="sunken", bg="#ddd")
            self.status_var.set("Select SOURCE class box...")
        else:
            self.btn_connect.config(relief="raised", bg="SystemButtonFace")
            self.selected_box = None
            self.status_var.set("Ready")

    def on_canvas_click(self, event):
        if not self.connect_mode: return
        
        # Check collision with boxes
        item = self.canvas.find_closest(event.x, event.y)[0]
        tags = self.canvas.gettags(item)
        
        # Get the Box object
        clicked_box = None
        for b in self.boxes:
            # We look for the group tag in the clicked item's tags
            if b.group_tag in tags:
                clicked_box = b
                break
        
        if not clicked_box: return

        if not self.selected_box:
            self.selected_box = clicked_box
            self.status_var.set(f"Source: {clicked_box.name}. Select TARGET...")
        else:
            if clicked_box != self.selected_box:
                l = UMLLine(self.canvas, self.selected_box, clicked_box, self.rel_type_var.get())
                self.lines.append(l)
                self.status_var.set(f"Connected {self.selected_box.name} -> {clicked_box.name}")
                self.toggle_connect()
            else:
                self.status_var.set("Cannot connect to self!")

    def clear(self):
        self.canvas.delete("all")
        self.boxes = []
        self.lines = []

    def save(self):
        data = {
            "boxes": [b.to_dict() for b in self.boxes],
            "lines": [l.to_dict() for l in self.lines]
        }
        f = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if f:
            with open(f, 'w') as file: json.dump(data, file, indent=2)

    def load(self):
        f = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not f: return
        self.clear()
        with open(f, 'r') as file:
            data = json.load(file)
        
        id_map = {}
        for b in data['boxes']:
            self.add_class(b['x'], b['y'], b['name'], b['fields'], b['methods'], b['id'])
            id_map[b['id']] = self.boxes[-1]
            
        for l in data['lines']:
            start = id_map.get(l['start'])
            end = id_map.get(l['end'])
            if start and end:
                self.lines.append(UMLLine(self.canvas, start, end, l['type']))

    def export(self):
        f = filedialog.asksaveasfilename(defaultextension=".ps", filetypes=[("PostScript", "*.ps")])
        if f:
            self.canvas.postscript(file=f, colormode="color")
            messagebox.showinfo("Export", "Saved as PostScript. Convert to PNG using GIMP or online tools.")

if __name__ == "__main__":
    app = UMLEditor()
    app.mainloop()