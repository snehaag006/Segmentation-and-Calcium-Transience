import cv2
import os
import numpy as np
from cellpose.models import CellposeModel
from cellpose import io
from nd2reader import ND2Reader

try:
    import tkinter as tk
    from tkinter import messagebox
    from tkinter import filedialog
    GUI_AVAILABLE = True
except ImportError:
    print("Tkinter is not available. Skipping plot prompt.")
    GUI_AVAILABLE = False

def get_user_inputs():
    if not GUI_AVAILABLE:
        raise RuntimeError("Tkinter is not available. Cannot open input dialog.")

    result = {"video_path": None, "diameter": 15.0, "csv_filename": None, "channel_index": 0}

    def on_submit():
        try:
            result["video_path"] = video_entry.get().strip()
            result["diameter"] = float(diameter_entry.get().strip())
            result["csv_filename"] = csv_entry.get().strip()
            result["channel_index"] = int(channel_entry.get().strip())
            input_root.quit()
            input_root.destroy()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for diameter and channel index.")

    input_root = tk.Tk()
    input_root.title("Input Parameters")
    input_root.geometry("500x350")  # Increased window size for better text display

    def browse_file():
        filepath = filedialog.askopenfilename(filetypes=[("ND2 files", "*.nd2"), ("All files", "*.*")])
        video_entry.delete(0, tk.END)
        video_entry.insert(0, filepath)

    tk.Label(input_root, text="Video Path:").pack(pady=5)
    path_frame = tk.Frame(input_root)
    path_frame.pack()
    video_entry = tk.Entry(path_frame, width=40)
    video_entry.pack(side="left")
    browse_button = tk.Button(path_frame, text="Browse", command=browse_file)
    browse_button.pack(side="left", padx=5)

    tk.Label(input_root, text="Cell Diameter (e.g., 15):").pack(pady=5)
    diameter_entry = tk.Entry(input_root, width=20)
    diameter_entry.pack()

    tk.Label(input_root, text="Output CSV Filename (no extension):").pack(pady=5)
    csv_entry = tk.Entry(input_root, width=30)
    csv_entry.pack()

    tk.Label(input_root, text="Channel Index (e.g., 0):").pack(pady=5)
    channel_entry = tk.Entry(input_root, width=10)
    channel_entry.pack()

    tk.Button(input_root, text="Submit", command=on_submit).pack(pady=10)

    input_root.mainloop()
    return result["video_path"], result["diameter"], result["csv_filename"], result["channel_index"]

# Load Cellpose model
model = CellposeModel(model_type='cyto')

# Get user inputs via GUI
video_path, diameter, csv_filename, channel_index = get_user_inputs()
if not os.path.exists(video_path):
    raise FileNotFoundError(f"Video file not found at: {video_path}")
if not os.access(video_path, os.R_OK):
    raise PermissionError(f"Video file is not readable: {video_path}")

output_dir = 'cellpose_segmented_frames'
os.makedirs(output_dir, exist_ok=True)

frame_num = 0
fluorescence_data = {}  # key: cell_id, value: list of frame-wise intensities

# Determine input type
is_nd2 = video_path.endswith(".nd2")

print("Scanning frames to select the one with highest fluorescence...")

max_brightness = -1
reference_frame = None
temp_iterator = ND2Reader(video_path) if is_nd2 else cv2.VideoCapture(video_path)

if is_nd2:
    temp_iterator.iter_axes = 't'
    if 'z' in temp_iterator.axes:
        temp_iterator.default_coords['z'] = 0
    for temp_frame in temp_iterator:
        temp_frame = np.array(temp_frame)
        temp_frame = cv2.normalize(temp_frame, None, 0, 255, cv2.NORM_MINMAX)
        temp_frame = temp_frame.astype(np.uint8)
        brightness = np.mean(temp_frame)
        if brightness > max_brightness:
            max_brightness = brightness
            reference_frame = temp_frame.copy()
else:
    while temp_iterator.isOpened():
        ret, temp_frame = temp_iterator.read()
        if not ret:
            break
        brightness = np.mean(temp_frame[:, :, 1])
        if brightness > max_brightness:
            max_brightness = brightness
            reference_frame = temp_frame.copy()
    temp_iterator.release()

if reference_frame is None:
    raise RuntimeError("Failed to find a valid frame for mask generation.")

print("Generating mask from brightest frame...")
masks, flows, diams = model.eval(reference_frame, diameter=diameter, channels=[0, 0])
saved_mask = masks.copy()

if is_nd2:
    nd2 = ND2Reader(video_path)
    nd2.iter_axes = 't'
    if 'z' in nd2.axes:
        nd2.default_coords['z'] = 0
    frame_iterator = (frame for frame in nd2)
else:
    cap = cv2.VideoCapture(video_path)
    frame_iterator = iter(lambda: cap.read()[1] if cap.isOpened() else None, None)

for frame in frame_iterator:

    if 'stop' in globals() and callable(stop) and stop():
        print("Segmentation manually stopped by user.")
        break

    if frame is None:
        break

    # Remove grayscale conversion block and replace
    if is_nd2:
        frame = np.array(frame)
        frame = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX)
        frame = frame.astype(np.uint8)

    # Cellpose expects 3-channel input; use frame directly
    image = frame

    cv2.imwrite("debug_enhanced_frame.png", frame)

    # Use precomputed masks
    masks = saved_mask

    unique_cells = np.unique(masks)
    print(f"Detected cells in frame {frame_num}: {unique_cells}")
    print(f"Masks shape: {masks.shape}")
    print(f"Masks unique values: {np.unique(masks)}")
    cv2.imwrite(os.path.join(output_dir, f"mask_{frame_num:04d}.png"), (masks > 0).astype(np.uint8) * 255)
    
    # Calculate fluorescence (mean pixel intensity) for each mask
    if len(unique_cells) <= 1:
        print(f"Warning: No cells detected in frame {frame_num}")
    for cell_id in unique_cells:
        if cell_id == 0:
            continue
        cell_mask = (masks == cell_id)
        mean_intensity = round(float(np.mean(frame[cell_mask])), 4)
        if cell_id not in fluorescence_data:
            fluorescence_data[cell_id] = []
        # Extend the list to match current frame number
        while len(fluorescence_data[cell_id]) < frame_num:
            fluorescence_data[cell_id].append(np.nan)
        fluorescence_data[cell_id].append(mean_intensity)

    # Create colored overlay using OpenCV contours
    contours, _ = cv2.findContours(masks.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    overlay = frame.copy()
    cv2.drawContours(overlay, contours, -1, (0, 255, 0), 2)  # green outline with thickness of 2
    out_path = os.path.join(output_dir, f"frame_{frame_num:04d}.png")
    cv2.imwrite(out_path, overlay)

    frame_num += 1

if not is_nd2:
    cap.release()

import csv
# Write fluorescence data to CSV (rows: cell_id, columns: frame_0, frame_1, ...)
csv_output_path = f"{csv_filename}.csv"
with open(csv_output_path, 'w', newline='') as csvfile:
    frame_columns = [f"frame_{i}" for i in range(frame_num)]
    fieldnames = ['cell_id'] + frame_columns
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for cell_id, values in fluorescence_data.items():
        # Pad with NaNs if any missing frames
        while len(values) < frame_num:
            values.append(np.nan)
        row = {'cell_id': int(cell_id)}
        row.update({f"frame_{i}": values[i] for i in range(frame_num)})
        writer.writerow(row)

print(f"Segmentation complete. {frame_num} frames processed.")
print(f"Fluorescence data saved to '{csv_output_path}'")

# Prompt user to plot mean fluorescence for each cell
import matplotlib.pyplot as plt

# Create GUI prompt
def ask_user_to_plot():
    if not GUI_AVAILABLE:
        return False

    result = {"choice": None}

    def on_yes():
        result["choice"] = True
        root.destroy()

    def on_no():
        result["choice"] = False
        root.destroy()

    root = tk.Tk()
    root.title("Plot Fluorescence Traces?")
    root.geometry("300x100")
    root.protocol("WM_DELETE_WINDOW", on_no)

    tk.Label(root, text="Do you want to plot mean fluorescence of each cell?").pack(pady=10)
    tk.Button(root, text="Yes", command=on_yes, width=10).pack(side="left", padx=30)
    tk.Button(root, text="No", command=on_no, width=10).pack(side="right", padx=30)

    root.mainloop()
    return result["choice"]

if ask_user_to_plot():
    for cell_id, values in fluorescence_data.items():
        plt.figure(figsize=(10, 4))
        plt.plot(range(frame_num), values, label=f"Cell {cell_id}")
        plt.xlabel("Frame")
        plt.ylabel("Mean Fluorescence")
        plt.title(f"Fluorescence Trace - Cell {cell_id}")
        plt.legend()
        plt.tight_layout()
        plt.show()