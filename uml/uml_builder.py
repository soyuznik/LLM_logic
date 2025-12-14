"""LLM Generated UML Diagram Builder using Tkinter."""

import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import json
import math
import copy

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
        rx = (px * math.cos(angle)) - (py * math.sin(angle))
        ry = (px * math.sin(angle)) + (py * math.cos(angle))
        rotated_points.extend([x2 + rx, y2 + ry])
        
    return rotated_points

# --- Free Text Label Class ---
class UMLLabel:
    def __init__(self, app, x, y, text="New Label", label_id=None):
        self.app = app
        self.canvas = app.canvas
        self.text = text
        self.id = label_id if label_id else id(self)
        self.x = x
        self.y = y
        self.group_tag = f"label_{self.id}"
        self.selected = False

        self.draw()

        # Bindings
        self.canvas.tag_bind(self.group_tag, "<Button-1>", self.on_click)
        self.canvas.tag_bind(self.group_tag, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.group_tag, "<ButtonRelease-1>", self.on_release)
        self.canvas.tag_bind(self.group_tag, "<Double-Button-1>", self.on_double_click)

    def draw(self):
        self.canvas.delete(self.group_tag)
        
        # Selection highlight
        bg_color = "#ffcccc" if self.selected else "white"
        outline_color = "red" if self.selected else ""
        
        # Create text to measure it
        t_id = self.canvas.create_text(
            self.x, self.y, 
            text=self.text, 
            font=("Helvetica", 10), 
            anchor="center",
            tags=(self.group_tag, "uml_obj")
        )
        
        bbox = self.canvas.bbox(t_id)
        if bbox:
            # Draw background rectangle for easier clicking/selection
            pad = 5
            self.bg_item = self.canvas.create_rectangle(
                bbox[0]-pad, bbox[1]-pad, bbox[2]+pad, bbox[3]+pad,
                fill=bg_color, outline=outline_color, width=1 if self.selected else 0,
                tags=(self.group_tag, "uml_obj")
            )
            self.canvas.tag_lower(self.bg_item, t_id)

    def update_visuals(self):
        """Updates visual state without recreating items to preserve drag context."""
        bg_color = "#ffcccc" if self.selected else "white"
        outline_color = "red" if self.selected else ""
        width = 1 if self.selected else 0
        if hasattr(self, 'bg_item'):
            self.canvas.itemconfig(self.bg_item, fill=bg_color, outline=outline_color, width=width)

    def on_click(self, event):
        self.app.start_undo_record() # Record state before potential move
        self.start_x = event.x
        self.start_y = event.y
        self.app.select_object(self)
        # Prevent canvas click
        return "break"

    def on_drag(self, event):
        dx = event.x - self.start_x
        dy = event.y - self.start_y
        self.canvas.move(self.group_tag, dx, dy)
        self.x += dx
        self.y += dy
        self.start_x = event.x
        self.start_y = event.y

    def on_release(self, event):
        self.app.finalize_undo_record()

    def on_double_click(self, event):
        self.app.start_undo_record()
        new_text = LabelEditor(self.canvas.winfo_toplevel(), self.text).result
        if new_text is not None:
            self.text = new_text
            self.draw()
            self.app.finalize_undo_record()
        else:
            self.app.cancel_undo_record()

    def to_dict(self):
        return {
            "id": self.id,
            "type": "label",
            "text": self.text,
            "x": self.x,
            "y": self.y
        }

# --- Main UML Box Class ---
class UMLBox:
    def __init__(self, app, x, y, name="NewClass", fields=None, methods=None, box_id=None):
        self.app = app
        self.canvas = app.canvas
        self.name = name
        self.fields = fields if fields else []
        self.methods = methods if methods else []
        self.lines = []
        self.id = box_id if box_id else id(self)
        self.selected = False

        # Visual configuration
        self.width = 160
        self.padding = 5
        self.header_bg = "#e3f2fd" # Light Blue
        self.body_bg = "#ffffff"   # White
        self.outline_color = "#1565c0"
        self.selected_color = "#ff0000"

        # Group ID for moving all items together
        self.group_tag = f"box_{self.id}"

        # Initialize graphics
        self.draw(x, y)

        # Bindings
        self.canvas.tag_bind(self.group_tag, "<Button-1>", self.on_click)
        self.canvas.tag_bind(self.group_tag, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.group_tag, "<ButtonRelease-1>", self.on_release)
        self.canvas.tag_bind(self.group_tag, "<Double-Button-1>", self.on_double_click)

    def draw(self, x=None, y=None):
        """Draws the box compartments with text wrapping. 
           If x,y not provided, uses current position."""
        
        # If x/y not provided, try to get from existing object or default
        if x is None or y is None:
            try:
                coords = self.canvas.coords(self.rect_item)
                x, y = coords[0], coords[1]
            except:
                pass # Should have been initialized with x,y first time
        
        self.canvas.delete(self.group_tag)
        
        border_color = self.selected_color if self.selected else self.outline_color
        border_width = 2 if self.selected else 2

        # 1. Main Background Rectangle (Placeholder, resized later)
        self.rect_item = self.canvas.create_rectangle(
            x, y, x + self.width, y + 100,
            fill=self.body_bg, outline=border_color, width=border_width, 
            tags=(self.group_tag, "uml_box", "uml_obj")
        )

        current_y = y

        # 2. Header (Name)
        name_item = self.canvas.create_text(
            x + self.width/2, current_y + self.padding + 10,
            text=self.name, font=("Helvetica", 10, "bold"), width=self.width - 10, justify="center",
            tags=(self.group_tag, "uml_box", "uml_obj")
        )
        bbox = self.canvas.bbox(name_item)
        header_h = (bbox[3] - bbox[1]) + (self.padding * 2) if bbox else 30
        
        # Header Background
        self.header_item = self.canvas.create_rectangle(
            x, y, x + self.width, y + header_h,
            fill=self.header_bg, outline=border_color, width=1,
            tags=(self.group_tag, "uml_box", "uml_obj")
        )
        self.canvas.tag_raise(name_item) # Bring text back on top
        current_y += header_h

        # 3. Fields
        for field in self.fields:
            f_item = self.canvas.create_text(
                x + 5, current_y + self.padding,
                text=field, anchor="nw", font=("Courier", 9), width=self.width - 10,
                tags=(self.group_tag, "uml_box", "uml_obj")
            )
            bbox = self.canvas.bbox(f_item)
            h = (bbox[3] - bbox[1]) + self.padding if bbox else 15
            current_y += h
        
        # Add small padding at bottom of fields
        current_y += self.padding

        # Divider
        self.canvas.create_line(
            x, current_y, x + self.width, current_y,
            fill=border_color, tags=(self.group_tag, "uml_box", "uml_obj")
        )

        # 4. Methods
        current_y += self.padding
        for method in self.methods:
            m_item = self.canvas.create_text(
                x + 5, current_y,
                text=method, anchor="nw", font=("Courier", 9), width=self.width - 10,
                tags=(self.group_tag, "uml_box", "uml_obj")
            )
            bbox = self.canvas.bbox(m_item)
            h = (bbox[3] - bbox[1]) + self.padding if bbox else 15
            current_y += h
            
        current_y += self.padding

        # Resize Main Rectangle
        self.canvas.coords(self.rect_item, x, y, x + self.width, current_y)
        
        # Ensure boxes are above lines
        self.canvas.tag_raise(self.group_tag)

    def update_visuals(self):
        """Updates visual state without recreating items to preserve drag context."""
        border_color = self.selected_color if self.selected else self.outline_color
        border_width = 2 if self.selected else 2
        if hasattr(self, 'rect_item'):
            self.canvas.itemconfig(self.rect_item, outline=border_color, width=border_width)
        if hasattr(self, 'header_item'):
            self.canvas.itemconfig(self.header_item, outline=border_color)

    def on_click(self, event):
        if self.app.connect_mode:
            self.app.handle_connect_click(self)
            return "break"
        
        self.app.start_undo_record() # Snapshot state
        self.start_x = event.x
        self.start_y = event.y
        self.app.select_object(self)
        return "break" # Prevent canvas click

    def on_drag(self, event):
        if self.app.connect_mode: return

        dx = event.x - self.start_x
        dy = event.y - self.start_y
        self.canvas.move(self.group_tag, dx, dy)
        self.start_x = event.x
        self.start_y = event.y
        
        for line in self.lines:
            line.update_position()

    def on_release(self, event):
        # Finalize undo record (check if changed)
        if not self.app.connect_mode:
            self.app.finalize_undo_record()

    def on_double_click(self, event):
        if self.app.connect_mode: return
        self.app.start_undo_record()
        EditorWindow(self.canvas.winfo_toplevel(), self)
        # Note: EditorWindow handles saving and calling finalize_undo_record via callback or manual handling

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

# --- Simple Label Editor Popup ---
class LabelEditor(tk.Toplevel):
    def __init__(self, parent, text):
        super().__init__(parent)
        self.title("Edit Label")
        self.geometry("300x150")
        self.result = None
        
        tk.Label(self, text="Label Text:").pack(pady=5)
        self.entry = tk.Entry(self, width=40)
        self.entry.insert(0, text)
        self.entry.pack(pady=5, padx=10)
        
        tk.Button(self, text="Save", command=self.save).pack(pady=10)
        self.bind("<Return>", lambda e: self.save())
        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)

    def save(self):
        self.result = self.entry.get()
        self.destroy()

# --- Editor Window for Details ---
class EditorWindow(tk.Toplevel):
    def __init__(self, parent, box):
        super().__init__(parent)
        self.title(f"Edit {box.name}")
        self.box = box
        self.geometry("350x450")

        tk.Label(self, text="Class Name:").pack(anchor="w", padx=5)
        self.entry_name = tk.Entry(self)
        self.entry_name.insert(0, box.name)
        self.entry_name.pack(fill="x", padx=5)

        tk.Label(self, text="Fields (one per line):").pack(anchor="w", padx=5)
        self.text_fields = tk.Text(self, height=8)
        self.text_fields.insert("1.0", "\n".join(box.fields))
        self.text_fields.pack(fill="x", padx=5)

        tk.Label(self, text="Methods (one per line):").pack(anchor="w", padx=5)
        self.text_methods = tk.Text(self, height=8)
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
            
        self.box.app.finalize_undo_record()
        self.destroy()

# --- Connection Line Class ---
class UMLLine:
    def __init__(self, app, box1, box2, rel_type="Association"):
        self.app = app
        self.canvas = app.canvas
        self.box1 = box1
        self.box2 = box2
        self.rel_type = rel_type
        
        self.id = id(self)
        self.group_tag = f"line_{self.id}"
        self.selected = False

        self.line_id = None
        self.head_id = None
        
        self.box1.lines.append(self)
        self.box2.lines.append(self)
        
        self.update_position()
        
        # Bindings
        self.canvas.tag_bind(self.group_tag, "<Button-1>", self.on_click)

    def draw(self):
        # Alias for select_object to call
        self.update_position()

    def update_visuals(self):
        """Updates visual state without recreating items."""
        fill = "red" if self.selected else "black"
        width = 4 if self.selected else 2
        if self.line_id:
            self.canvas.itemconfig(self.line_id, fill=fill, width=width)
        if self.head_id:
            self.canvas.itemconfig(self.head_id, outline=fill)

    def on_click(self, event):
        self.app.start_undo_record()
        self.app.select_object(self)
        return "break"

    def update_position(self):
        x1, y1 = self.box1.get_coords()
        x2, y2 = self.box2.get_coords()
        
        if self.line_id: self.canvas.delete(self.line_id)
        if self.head_id: self.canvas.delete(self.head_id)
        
        # Remove old tags if any (items deleted anyway)

        # Style Configuration
        dash = None
        arrow = None
        
        # Selection highlight
        fill = "red" if self.selected else "black"
        width = 4 if self.selected else 2
        
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
            x1, y1, x2, y2, width=width, fill=fill, arrow=arrow, dash=dash,
            tags=(self.group_tag, "uml_obj")
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
                poly_points, outline=fill, fill=poly_color, width=2,
                tags=(self.group_tag, "uml_obj")
            )
            # Match selection color for outline

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
        self.title("UML Editor Pro")
        self.geometry("1100x750")

        self.boxes = []
        self.lines = []
        self.labels = []
        
        self.connect_mode = False
        self.selected_connect_box = None
        self.selected_object = None # For deletion

        # Undo/Redo Stacks
        self.undo_stack = []
        self.redo_stack = []
        self.recording_state = None

        # UI Setup
        self.create_toolbar()
        
        self.canvas = tk.Canvas(self, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Key Bindings
        self.bind("<Delete>", self.delete_selected)
        self.bind("<BackSpace>", self.delete_selected)
        self.bind("<Control-z>", self.undo)
        self.bind("<Control-y>", self.redo)

        self.status_var = tk.StringVar(value="Ready. Use Toolbar to add items. Select item + DEL to delete.")
        tk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w").pack(fill="x", side="bottom")

    def create_toolbar(self):
        bar = tk.Frame(self, bg="#eeeeee", height=40)
        bar.pack(fill="x", side="top")

        tk.Button(bar, text="+ Class", command=self.add_class_action).pack(side="left", padx=5, pady=5)
        tk.Button(bar, text="+ Label", command=self.add_label_action).pack(side="left", padx=5, pady=5)
        
        # Connection Type Selector
        tk.Label(bar, text="| Rel:").pack(side="left", padx=2)
        self.rel_type_var = tk.StringVar(value="Association")
        # Removed Realization from default menu, but backend supports it
        rel_types = ["Association", "Inheritance", "Dependency", "Aggregation", "Composition"]
        ttk.OptionMenu(bar, self.rel_type_var, "Association", *rel_types).pack(side="left")

        self.btn_connect = tk.Button(bar, text="Connect Mode", command=self.toggle_connect)
        self.btn_connect.pack(side="left", padx=5)

        # Right side buttons
        tk.Button(bar, text="Clear", command=self.clear_action, bg="#ffcccb").pack(side="right", padx=5)
        tk.Button(bar, text="Save JSON", command=self.save).pack(side="right", padx=5)
        tk.Button(bar, text="Load JSON", command=self.load).pack(side="right", padx=5)
        tk.Button(bar, text="Undo (Ctrl+Z)", command=self.undo).pack(side="right", padx=5)

    # --- Undo/Redo Logic ---
    def get_state(self):
        """Returns serializable state of the diagram."""
        return json.dumps({
            "boxes": [b.to_dict() for b in self.boxes],
            "lines": [l.to_dict() for l in self.lines],
            "labels": [l.to_dict() for l in self.labels]
        })

    def load_state_from_json(self, json_str):
        """Restores diagram from state string."""
        self.clear_internal()
        data = json.loads(json_str)
        
        id_map = {}
        for b in data.get('boxes', []):
            box = UMLBox(self, b['x'], b['y'], b['name'], b['fields'], b['methods'], b['id'])
            self.boxes.append(box)
            id_map[b['id']] = box
            
        for l in data.get('lines', []):
            start = id_map.get(l['start'])
            end = id_map.get(l['end'])
            if start and end:
                self.lines.append(UMLLine(self, start, end, l['type']))

        for lb in data.get('labels', []):
            # Check for missing keys for backward compat if any
            self.labels.append(UMLLabel(self, lb['x'], lb['y'], lb['text'], lb.get('id')))

    def save_state_to_history(self, state=None):
        if state is None:
            state = self.get_state()
        self.undo_stack.append(state)
        self.redo_stack.clear()
        # Limit stack size if needed
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)

    def start_undo_record(self):
        """Called before a potential change starts (e.g. click to drag)."""
        self.recording_state = self.get_state()

    def finalize_undo_record(self):
        """Called after an action completes. Checks if state actually changed."""
        if self.recording_state:
            current = self.get_state()
            if current != self.recording_state:
                self.undo_stack.append(self.recording_state)
                self.redo_stack.clear()
            self.recording_state = None

    def cancel_undo_record(self):
        self.recording_state = None

    def undo(self, event=None):
        if not self.undo_stack:
            self.status_var.set("Nothing to Undo")
            return
        
        current_state = self.get_state()
        self.redo_stack.append(current_state)
        
        prev_state = self.undo_stack.pop()
        self.load_state_from_json(prev_state)
        self.status_var.set("Undone.")

    def redo(self, event=None):
        if not self.redo_stack:
            self.status_var.set("Nothing to Redo")
            return
            
        current_state = self.get_state()
        self.undo_stack.append(current_state)
        
        next_state = self.redo_stack.pop()
        self.load_state_from_json(next_state)
        self.status_var.set("Redone.")

    # --- Actions ---
    def add_class_action(self):
        self.save_state_to_history()
        self.boxes.append(UMLBox(self, 50, 50))

    def add_label_action(self):
        self.save_state_to_history()
        self.labels.append(UMLLabel(self, 100, 50))

    def clear_action(self):
        if messagebox.askyesno("Clear", "Delete everything?"):
            self.save_state_to_history()
            self.clear_internal()

    def clear_internal(self):
        self.canvas.delete("all")
        self.boxes = []
        self.lines = []
        self.labels = []
        self.selected_object = None

    def select_object(self, obj):
        # Deselect previous
        if self.selected_object and self.selected_object != obj:
            self.selected_object.selected = False
            # Use lightweight update if possible
            if hasattr(self.selected_object, 'update_visuals'):
                self.selected_object.update_visuals()
            elif hasattr(self.selected_object, 'draw'):
                self.selected_object.draw()

        self.selected_object = obj
        obj.selected = True
        
        # Use lightweight update if possible
        if hasattr(obj, 'update_visuals'):
            obj.update_visuals()
        else:
            obj.draw()
        
        self.status_var.set(f"Selected: {obj.name if hasattr(obj, 'name') else 'Object'}")
        self.canvas.focus_set() # Enable keyboard events

    def delete_selected(self, event=None):
        if not self.selected_object: return
        
        self.save_state_to_history()
        
        obj = self.selected_object
        
        if isinstance(obj, UMLBox):
            # Remove attached lines
            to_remove = [l for l in self.lines if l.box1 == obj or l.box2 == obj]
            for l in to_remove:
                self.canvas.delete(l.line_id)
                self.canvas.delete(l.head_id)
                self.lines.remove(l)
                # Remove from other boxes' line lists
                if l.box1 in self.boxes: l.box1.lines.remove(l)
                if l.box2 in self.boxes: l.box2.lines.remove(l)
            
            self.canvas.delete(obj.group_tag)
            self.boxes.remove(obj)
            
        elif isinstance(obj, UMLLabel):
            self.canvas.delete(obj.group_tag)
            self.labels.remove(obj)
            
        elif isinstance(obj, UMLLine):
            self.canvas.delete(obj.group_tag)
            self.lines.remove(obj)
            if obj.box1 in self.boxes: obj.box1.lines.remove(obj)
            if obj.box2 in self.boxes: obj.box2.lines.remove(obj)
            
        self.selected_object = None
        self.status_var.set("Deleted.")

    # --- Connection Logic ---
    def toggle_connect(self):
        self.connect_mode = not self.connect_mode
        if self.connect_mode:
            self.btn_connect.config(relief="sunken", bg="#ddd")
            self.status_var.set("Connect Mode: Click Source Class...")
            # Deselect any selected object
            if self.selected_object:
                self.selected_object.selected = False
                if hasattr(self.selected_object, 'update_visuals'):
                    self.selected_object.update_visuals()
                else:
                    self.selected_object.draw()
                self.selected_object = None
        else:
            self.btn_connect.config(relief="raised", bg="SystemButtonFace")
            self.selected_connect_box = None
            self.status_var.set("Ready")

    def handle_connect_click(self, clicked_box):
        if not self.selected_connect_box:
            self.selected_connect_box = clicked_box
            self.status_var.set(f"Source: {clicked_box.name}. Click Target Class...")
        else:
            if clicked_box != self.selected_connect_box:
                self.save_state_to_history()
                l = UMLLine(self, self.selected_connect_box, clicked_box, self.rel_type_var.get())
                self.lines.append(l)
                self.status_var.set(f"Connected {self.selected_connect_box.name} -> {clicked_box.name}")
                # Optional: stay in connect mode or exit? Let's stay
                self.selected_connect_box = None
                self.status_var.set("Connect Mode: Click Source Class...")
            else:
                self.status_var.set("Cannot connect to self!")

    def on_canvas_click(self, event):
        # Deselect if clicking on empty space
        item = self.canvas.find_closest(event.x, event.y)
        tags = self.canvas.gettags(item)
        if "uml_obj" not in tags:
            if self.selected_object:
                self.selected_object.selected = False
                if hasattr(self.selected_object, 'update_visuals'):
                    self.selected_object.update_visuals()
                else:
                    self.selected_object.draw()
                self.selected_object = None
            self.status_var.set("Ready")

    # --- IO ---
    def save(self):
        data = json.loads(self.get_state())
        f = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if f:
            with open(f, 'w') as file: json.dump(data, file, indent=2)

    def load(self):
        f = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not f: return
        
        self.save_state_to_history() # Save current before loading new
        with open(f, 'r') as file:
            content = file.read()
            self.load_state_from_json(content)

if __name__ == "__main__":
    app = UMLEditor()
    app.mainloop()