
list of tools:
Based on the provided paper, Visual SKETCHPAD includes the following tools, categorized for clarity:

**Core Mechanism:**
*   **Python Code Generation:** SKETCHPAD enables LMs to generate Python code that calls other specialist models or plotting packages.

**Tools for Mathematical Tasks:**
*   **`matplotlib`:** Used for:
    *   Plotting mathematical functions.
    *   Generating and modifying geometry diagrams (e.g., drawing auxiliary lines).
    *   **Location:** Examples and templates in `agent/prompt.py` (lines 463, 505, 549, 586, 634, 850) and `agent/math_data.py` (line 11)

*   **`networkx`:** Used for drawing graph structures from adjacency matrices.
    *   **Location:** Examples and templates in `agent/prompt.py` (lines 504, 584) and `agent/math_data.py` (line 10)

*   **Python `chess` library:** Used for drawing visual representations of chess boards from Forsyth-Edwards Notation (FEN).
    *   **Location:** Examples and templates in `agent/prompt.py` (lines 546-547) and `agent/math_data.py` (lines 89-90)

**Tools for Vision Tasks (Vision Specialists & Image Manipulation Modules):**
The paper describes these as Python functions the LM can call, often wrapping underlying specialist models.

1.  **`detection(image, objects)` Module:**
    *   **Underlying Model:** Grounding-DINO
    *   **Functionality:** Performs open-vocabulary object detection, plots detected bounding boxes with number labels on the image, and returns box coordinates.
    *   **Location:** `agent/tools.py` (line 92)
    *   **Server Implementation:** `vision_experts/GroundingDINO/grounding_dino_server.py` (line 45)

2.  **`segment_and_mark(image, anno_mode)` Module:**
    *   **Underlying Models:** SegmentAnything and Semantic-SAM (inspired by SoM)
    *   **Functionality:** Segments the image and adds colorful segmentation masks to segmented objects, with each segment also labeled with a number. Returns the annotated image and bounding boxes of masks.
    *   **Location:** `agent/tools.py` (line 35)
    *   **Server Implementation:** `vision_experts/simplified_som/testing.py` (line 7)

3.  **`depth(image)` Module:**
    *   **Underlying Model:** DepthAnything
    *   **Functionality:** Performs depth estimation and returns a depth map (visualized using a colormap like Inferno).
    *   **Location:** `agent/tools.py` (line 136)

4.  **`sliding_window_detection(image, objects)` Module:**
    *   **Functionality:** A visual search method that runs a sliding window over the image. It uses a detection model (likely Grounding-DINO, as per its description of using "the detection model") on zoomed-in patches to find objects that might be too small for direct detection on the full image. Returns a list of annotated image patches.
    *   **Location:** `agent/tools.py` (line 220)

5.  **`zoom_in_image_by_bbox(image, box, padding)` Module:**
    *   **Functionality:** Crops the image based on a given bounding box, allowing the model to "zoom in" on specific regions for detailed examination.
    *   **Location:** `agent/tools.py` (line 196)

6.  **`overlay_images(background_img, overlay_img, alpha, bounding_box)` Module:**
    *   **Functionality:** Overlays one image onto another with a specified transparency (alpha value), useful for visualizing heatmaps or segmentation on the original image.
    *   **Location:** `agent/tools.py` (line 286)

**Additional Helper Functions:**
*   **`crop_image(image, x, y, width, height)`** - Helper function for cropping images based on normalized coordinates.
    *   **Location:** `agent/tools.py` (line 160)

In summary, SKETCHPAD equips LMs with a suite of programmatic tools for both mathematical visualization (via common Python plotting libraries) and advanced visual perception/manipulation (via specialized vision models wrapped in callable Python functions). The main tool implementations are centralized in `agent/tools.py`, with underlying vision models served from the `vision_experts/` directory.