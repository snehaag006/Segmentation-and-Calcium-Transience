# 🧪 Segmentation and Mean Fluorescence Analysis

This project is a Python-based tool for performing **cell segmentation and quantification of mean fluorescence intensity** from microscopy video files (including `.nd2` files). It uses the **Cellpose deep learning model** for segmentation and supports a user-friendly **Tkinter GUI** for input selection.

---

## 🎯 Key Features

- 📁 **Video Input Support**: Accepts `.nd2` files or standard video formats.
- 🔬 **Brightest Frame Detection**: Automatically selects the brightest frame for mask generation.
- 🧠 **Deep Learning Segmentation**: Uses the pretrained `cyto` model from Cellpose.
- 📈 **Fluorescence Quantification**: Calculates mean fluorescence intensity for each segmented cell over time.
- 📝 **CSV Export**: Saves results in a structured CSV file (`cell_id × frames`).
- 🖼️ **Frame & Mask Export**: Saves segmented overlays and masks for each frame.
- 📊 **Optional Plotting**: Offers post-processing plots of fluorescence traces for each cell.
- 🖱️ **GUI Input**: Simple user interface for parameter input via `Tkinter`.

---

## 🚀 Example Workflow

1. User selects input file via GUI and provides:
   - Cell diameter
   - Output CSV filename
   - Fluorescence channel index
2. Code:
   - Detects the brightest frame and uses it for segmentation
   - Processes each frame to apply the saved mask
   - Calculates mean fluorescence for each detected cell
   - Saves results to CSV
3. Optionally, fluorescence traces for each cell are plotted.

---

## 📂 Output Structure

- `cellpose_segmented_frames/`: Overlaid frames with contours
- `mask_####.png`: Binary masks for each frame
- `<your_filename>.csv`: Output with rows as cell IDs and columns as frame-wise mean intensities

---

## ⚙️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/snehaag006/segmentation-mean-fluorescence.git
cd segmentation-mean-fluorescence
```

###2. Install dependencies
```bash
pip install -r requirements.txt
```
📌 Note: Tkinter comes bundled with most Python installations. If you face issues on Linux, install via sudo apt install python3-tk.

🧪 Sample Input (Optional)

You can test the script with .nd2 files exported from imaging software such as Nikon NIS-Elements or standard .mp4/.avi videos converted from microscopy software.

🧠 Technologies Used
	•	Python 3
	•	Cellpose for segmentation
	•	NumPy & Pandas for analysis
	•	OpenCV for image processing
	•	Matplotlib for plotting
	•	Tkinter for GUI input
	•	ND2Reader for .nd2 file handling

 🙌 Contributions

Contributions are welcome! Feel free to fork this repo, submit issues, or open pull requests to improve functionality or compatibility.

✨ Acknowledgements
	•	Cellpose for the segmentation model
	•	ND2Reader for .nd2 file support
