Background:
## TL;DR: Visual SKETCHPAD

**What it is:** A framework that gives large language models the ability to draw intermediate visual sketches during reasoning, mimicking how humans draw auxiliary lines in geometry or mark up images to solve problems.

**The gap:** Current multimodal LMs only use text for chain-of-thought reasoning, but humans leverage visual sketches to facilitate problem-solving and reduce cognitive load.

**How it works:** The LM generates Python code that calls specialist vision models (object detection, segmentation, depth estimation) or plotting libraries (matplotlib, networkx) to create visual artifacts. The LM then reasons based on these visual outputs in an iterative process.

**Key results:** 
- 12.7% average improvement on math tasks (geometry, functions, graphs, chess)
- 8.6% average improvement on vision tasks  
- Sets new SOTA on multiple benchmarks (V*Bench: 80.3%, BLINK spatial reasoning: 83.9%)
- Works out-of-the-box with existing LMs (no training required)

**Tools included:**
- **Math:** matplotlib (function plotting, geometry), networkx (graphs), chess library
- **Vision:** Grounding-DINO (detection), SAM (segmentation), DepthAnything (depth), sliding window search, image manipulation

**3D Extension Opportunity:** The current framework is limited to 2D visual reasoning. Extending to 3D would enable reasoning about spatial relationships, 3D geometry, robotics navigation, and complex 3D scene understanding - areas where visual sketching in 3D space could provide even greater cognitive benefits for multimodal reasoning.

---

# Technical Breakthrough Update

**Status**: Core feasibility for 3D scene modification has been validated through browser console testing.

**What Worked:**
```javascript
// Successfully added colored cubes to Minecraft world
const geometry = new THREE.BoxGeometry(1, 1, 1);
const material = new THREE.MeshBasicMaterial({color: new THREE.Color(`hsl(${hue}, 100%, 50%)`)});
const cube = new THREE.Mesh(geometry, material);
cube.position.set(x, y, z);
window.world.scene.add(cube);
```

**Key Validations:**
- 3D scene modification works via `window.world.scene.add()`
- Can place markers at arbitrary 3D coordinates
- Multiple colored objects render simultaneously 
- Visual feedback pipeline is functional
- Risk assessment: HIGH risk → LOW risk

**Next Steps**: Implement WebSocket integration to expose this capability as MCP tools.

## ✅ **CONFIRMED TECHNICAL ARCHITECTURE**

**Pipeline Validation**: The complete data flow has been validated end-to-end!

```
Agent Loop (Python) 
    ↓ MCP calls (✅ working)
MCP Server (TypeScript) 
    ↓ WebSocket commands (✅ existing infrastructure)
Minecraft Web Client (Browser/Three.js)
    ↓ ✅ PROVEN: Scene modification via window.world.scene.add()
Visual 3D markers rendered in world
    ↓ ✅ WORKING: Screenshot capture
Screenshots back to LLM (✅ validated)
```

**Key Confirmations:**
- ✅ **MCP → WebSocket**: Existing infrastructure handles commands
- ✅ **WebSocket → Three.js**: Direct scene access via `window.world.scene` 
- ✅ **Three.js → Visual**: BoxGeometry + materials render perfectly
- ✅ **Visual → Screenshot**: Capture system returns annotated images
- ✅ **Screenshot → LLM**: Image pipeline works for visual reasoning

**Remaining Work**: Just WebSocket command handlers (implementation, not architecture)!

## Immediate Next Actions

Phase 0's core technical risk has been addressed. Focus shifts to implementation:

### **Short-term priorities:**
1. **Implement WebSocket command handler** for `annotate_3d_position`
   - Add handler in `src/wsCommandClient.ts` 
   - Use validated approach: `window.world.scene.add(new THREE.Mesh(...))`
   - Test via MCP: `python simple_client.py --msg "annotate_3d_position(100, 64, 200, 'test', 'red')"`

2. **Add MCP tool definition** in `minecraft-mcp-server.ts`
   - Expose `annotate_3d_position` as callable MCP tool
   - Include parameter validation (x, y, z coordinates, label, color)
   - Return screenshot after annotation placement

### **This week:**
3. **Implement remaining tools**: `zoom_and_orient` and `detect_blocks_in_view`
4. **Validate full tool integration** with LLM agent loop
5. **Begin collection software integration** (F5/F6 recording)

---



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



# Research paper idea:
Collect high quality 50K Visual SKETCHPAD trajectories for 3d zoom+annotation+mouse movement data from minecraft and show that  the minecraft data transfers to web agents.


Plan:
- collect 50 examples manually.
- finetune gpt-4.1-nano on 50 examples
- use finetuned gpt-4.1-nano model to obtain 1000 trajectories = SFT data
- SFT Gemma 27B on 1K trajectories
- GRPO Gemma 3 27B to obtain 50K good trajectories = this is the dataset.
- finetune models on this and show it transfers to web agents and swe bench and whatever

Current status:
- LLMs can use MCP to move around and take screenshots of minecraft.
- I have a collection software in python that is half working.
- I don't have any of the minecraft Visual SKETCHPAD tools implemented yet (and the specific tools needed are still to be determined through experimentation).

# Phases


# Phase 0: discover and validate tools [Core feasibility validated]

**✅ In Scope:**
- 3D Visual SKETCHPAD tools (`annotate_3d_position` validated, others in progress)
- MCP integration for Minecraft
- Simple trajectory recording/playback
- Core technical feasibility discovered through successful testing

**❌ Out of Scope:**
- Perfect tool implementations
- Tools for other games/environments beyond Minecraft
- Advanced computer vision models (stick to existing depth/detection models for initial experiments)
- Complex UI overlays or visualization

**Status Update:** Core technical feasibility has been validated. 3D scene modification via Three.js works as expected. Risk assessment: HIGH risk → LOW risk.

# Phase 1: Collect 50 examples

**✅ In Scope:**
- Manual collection using basic tools
- Simple task definitions (e.g., "build a house", "navigate to location")
- Basic quality control (does it complete the task?)
- Simple data format standardization

**❌ Out of Scope:**
- Complex task taxonomies
- Automated quality metrics
- Multiple human annotators
- Sophisticated data validation pipelines

Prerequisites to start this phase:

- have a working set of validated 3D reasoning tools (may differ from initial candidates)
- tools demonstrate effective spatial reasoning capabilities in practice

# Phase 2: Finetune gpt-4.1-nano on 50 examples

**✅ In Scope:**
- Basic finetuning on 50 examples
- Simple prompt engineering
- Basic evaluation (does it follow the format?)

**❌ Out of Scope:**
- Extensive hyperparameter tuning
- Multiple model variants
- Complex evaluation metrics
- Prompt optimization across multiple domains

Prerequisites to start this phase:

- need to collect 50 examples manually...

# Phase 3: Collect 1000 trajectories with finetuned gpt-4.1-nano

**✅ In Scope:**
- Automated collection with finetuned GPT-4.1-nano
- Basic filtering (remove crashes/incomplete trajectories)
- Scale to 1K examples

**❌ Out of Scope:**
- Perfect trajectory quality
- Complex reward-based filtering
- Multiple collection strategies
- Human-in-the-loop validation

Prerequisites to start this phase:

- The agent interface should be working (it is developed in tendem with the tools so that's fine).


# Phase 4: SFT Gemma 27B on 1K trajectories

**✅ In Scope:**
- Adapt existing training scripts for multimodal data
- Basic SFT on 1K trajectories
- Standard training metrics (loss, perplexity)

**❌ Out of Scope:**
- Advanced training techniques (LoRA, quantization optimizations)
- Multiple model sizes (stick to 27B)
- Complex curriculum learning
- Extensive ablation studies

Prerequisites to start this phase:

- Validate that OpenAIAsyncMessageChain format is compatible with training pipeline
- May need minimal adaptation since conversation format should be natively supported
- Test loading and processing of trajectory JSON files with embedded images


# Phase 5: GRPO Gemma 3 27B to obtain 50K good trajectories = this is the dataset.

**✅ In Scope:**
- Basic GRPO implementation
- Simple trajectory validation (task completion, no crashes)
- Scale to multiple Minecraft instances
- Generate 50K trajectories

**❌ Out of Scope:**
- Sophisticated reward models
- Human preference learning
- Multiple environment types
- Perfect trajectory quality assessment

- need to implement trajectory validation and reject bad trajectories.
- need to scale existing minecraft setup to more than 1 host.

# Phase 6: finetune models on this data

**✅ In Scope:**
- Train final models on 50K dataset
- Basic model variants (with/without Minecraft data)
- Standard training pipeline

**❌ Out of Scope:**
- Architecture modifications
- Multiple training paradigms
- Extensive model analysis
- Constitutional AI or safety training

Prerequisites to start this phase:

- need to implement 



# Phase 7: evaluate these models and compare vs models not trained on it.

**✅ In Scope:**
- Transfer evaluation on **2-3 key benchmarks**: WebArena, SWE-Bench, maybe one spatial reasoning benchmark
- Direct comparison: models trained on Minecraft data vs. not
- Basic transfer analysis

**❌ Out of Scope:**
- Comprehensive benchmarking across 10+ domains
- Detailed ablation studies on what transfers
- Human evaluation studies
- Comparison with 20+ baseline models
- Analysis of failure modes across all domains

show it transfers to web agents and swe bench and whatever


Prerequisites to start this phase:

- have evaluation software in place

## Key Principles for Staying in Scope:

1. **Minimum Viable Research:** Focus on proving the core hypothesis (3D Minecraft skills transfer to web agents)
2. **Single Path:** Don't explore multiple approaches in parallel
3. **Existing Tools:** Leverage existing models/frameworks rather than building from scratch
4. **Core Metrics:** Focus on transfer performance, not optimizing everything
5. **Proof of Concept:** Show it works, don't perfect every component

⚠️ **Updated Scope Creep Warning**: 
- Fancy graphics are now proven possible (rainbow cubes, complex markers, animations)
- Resist the temptation to over-engineer visual effects
- Stick to simple colored spheres for Phase 0 implementation
- Save advanced graphics for future work - focus on collecting 50 trajectories first

The biggest scope creep risks are in **Phase 0** (over-engineering tools) and **Phase 7** (evaluating on too many benchmarks). Keep the focus narrow and deep.


Suggested project structure:
visual_sketchpad_3d/
├── README.md
├── requirements.txt
├── setup.py
├── config/
│   ├── __init__.py
│   ├── minecraft_config.yaml
│   ├── training_config.yaml
│   └── evaluation_config.yaml
│
├── core/                                    # Core Visual SKETCHPAD framework
│   ├── __init__.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── sketchpad_agent.py              # Main agent logic
│   │   ├── prompt_templates.py             # Prompts for 3D reasoning
│   │   └── reasoning_engine.py             # Thought-Action-Observation loop
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base_tools.py                   # Abstract tool interfaces
│   │   ├── 2d_tools.py                     # Original 2D tools (detection, segmentation, etc.)
│   │   └── 3d_tools.py                     # New 3D tools (depth, spatial reasoning, etc.)
│   └── utils/
│       ├── __init__.py
│       ├── image_utils.py
│       └── coordinate_utils.py
│
├── minecraft/                               # Minecraft-specific components
│   ├── __init__.py
│   ├── mcp_client/
│   │   ├── __init__.py
│   │   ├── minecraft_client.py             # MCP connection to Minecraft
│   │   ├── screenshot_manager.py           # Handle screenshots/video capture
│   │   └── movement_controller.py          # Mouse/keyboard control
│   ├── tools/                              # 3D Minecraft Visual SKETCHPAD tools
│   │   ├── __init__.py
│   │   ├── spatial_annotation.py          # 3D annotation tools
│   │   ├── depth_mapping.py               # 3D depth estimation in Minecraft
│   │   ├── zoom_controller.py             # 3D zoom/camera control
│   │   ├── block_detection.py             # Minecraft-specific object detection
│   │   ├── path_planning.py               # 3D navigation planning
│   │   └── inventory_management.py        # Tool/item management
│   ├── data_collection/
│   │   ├── __init__.py
│   │   ├── trajectory_collector.py        # Main data collection orchestrator
│   │   ├── manual_collection.py           # For collecting initial 50 examples
│   │   ├── automated_collection.py        # For scaling to 50K with finetuned model
│   │   └── trajectory_validator.py        # Quality control for trajectories
│   └── evaluation/
│       ├── __init__.py
│       ├── minecraft_benchmarks.py        # Minecraft-specific evaluation tasks
│       └── skill_assessment.py            # Assess 3D reasoning skills
│
├── training/                               # Training pipeline
│   ├── __init__.py
│   ├── data_processing/
│   │   ├── __init__.py
│   │   ├── trajectory_processor.py        # Process raw trajectories for training
│   │   ├── data_augmentation.py           # Augment 3D trajectory data
│   │   └── data_validation.py             # Validate training data quality
│   ├── sft/                               # Supervised Fine-Tuning
│   │   ├── __init__.py
│   │   ├── sft_trainer.py                 # SFT training for Gemma 27B
│   │   ├── data_loader.py                 # Data loading for SFT
│   │   └── evaluation.py                  # SFT evaluation metrics
│   ├── grpo/                              # Generalized Reward Preference Optimization
│   │   ├── __init__.py
│   │   ├── grpo_trainer.py                # GRPO training logic
│   │   ├── reward_model.py                # Reward model for trajectory quality
│   │   └── preference_learning.py         # Learn from trajectory preferences
│   └── utils/
│       ├── __init__.py
│       ├── model_utils.py                 # Model loading/saving utilities
│       └── training_utils.py              # Common training utilities
│
├── transfer_evaluation/                    # Transfer learning evaluation
│   ├── __init__.py
│   ├── web_agents/
│   │   ├── __init__.py
│   │   ├── web_agent_adapter.py           # Adapt 3D skills to web navigation
│   │   ├── web_benchmarks.py              # WebArena, Mind2Web, etc.
│   │   └── web_evaluation.py              # Evaluation on web agent tasks
│   ├── swe_bench/
│   │   ├── __init__.py
│   │   ├── swe_adapter.py                 # Adapt to code editing tasks
│   │   └── swe_evaluation.py              # SWE-Bench evaluation
│   ├── general_reasoning/
│   │   ├── __init__.py
│   │   ├── math_reasoning.py              # 3D geometry, spatial math
│   │   ├── visual_reasoning.py            # 3D visual reasoning tasks
│   │   └── spatial_reasoning.py           # General spatial reasoning
│   └── transfer_analysis/
│       ├── __init__.py
│       ├── skill_transfer.py              # Analyze which skills transfer
│       └── ablation_studies.py            # Ablation studies on transfer
│
├── data/                                   # Data storage and management
│   ├── trajectories/                      # Self-contained conversation trajectories
│   │   ├── manual_50/                     # Initial 50 manual examples (*.json files)
│   │   ├── sft_1k/                        # 1K trajectories from finetuned GPT-4.1-nano
│   │   └── grpo_50k/                      # Final 50K high-quality trajectories
│   ├── processed/                         # Processed training data (if needed)
│   │   ├── sft_data/                      # May be unnecessary with direct JSON loading
│   │   └── grpo_data/
│   ├── models/                            # Saved model checkpoints
│   │   ├── gpt4_nano_ft/                  # Finetuned GPT-4.1-nano
│   │   ├── gemma_sft/                     # SFT Gemma 27B
│   │   └── gemma_grpo/                    # GRPO Gemma 27B
│   └── benchmarks/                        # Benchmark datasets
│       ├── minecraft_tasks/
│       ├── web_agent_tasks/
│       └── swe_bench_tasks/
│
├── experiments/                            # Experiment scripts and results
│   ├── __init__.py
│   ├── data_collection_experiments/
│   │   ├── collect_manual_50.py
│   │   ├── scale_to_1k.py
│   │   └── scale_to_50k.py
│   ├── training_experiments/
│   │   ├── sft_experiment.py
│   │   └── grpo_experiment.py
│   ├── transfer_experiments/
│   │   ├── web_agent_transfer.py
│   │   ├── swe_bench_transfer.py
│   │   └── general_reasoning_transfer.py
│   └── results/                           # Experiment results and analysis
│       ├── data_collection_results/
│       ├── training_results/
│       └── transfer_results/
│
├── visualization/                          # Visualization and analysis tools
│   ├── __init__.py
│   ├── trajectory_visualizer.py           # Visualize 3D trajectories
│   ├── skill_analysis.py                  # Analyze learned skills
│   └── transfer_analysis.py               # Visualize transfer learning results
│
├── scripts/                               # Utility scripts
│   ├── setup_minecraft.py                # Set up Minecraft environment
│   ├── data_preprocessing.py             # Preprocess collected data
│   ├── model_inference.py                # Run inference with trained models
│   └── evaluation_runner.py              # Run all evaluations
│
└── tests/                                 # Unit tests
    ├── __init__.py
    ├── test_minecraft_tools.py
    ├── test_training_pipeline.py
    ├── test_transfer_evaluation.py
    └── test_data_collection.py



# Phase 0 MVP: Core 3D Visual SKETCHPAD Tools [Feasibility validated]

## MVP Goal Status
Core technical feasibility for 3D visual reasoning tools has been validated through browser console testing. Focus now shifts to WebSocket integration and tool implementation.

---

## Tool Implementation Status

*Technical feasibility has been validated through browser console testing. The Three.js scene modification approach works as expected.*

### 1. **`annotate_3d_position(x, y, z, label, color="red")` [✅ PROVEN FEASIBLE]**
```python
# Mark a 3D coordinate in the world with a visual indicator
annotate_3d_position(100, 64, 200, "target_location", "blue")
# → Places a colored marker/particle effect at that world coordinate
# → Returns: screenshot with annotation overlay
```

**✅ VALIDATED Implementation:** 
- **BREAKTHROUGH**: Successfully tested via `window.world.scene.add(cube)` in browser console
- **WORKING CODE**: Added 121 colored cubes in rainbow pattern + large red cube
- **PROVEN APPROACH**: Three.js BoxGeometry + MeshBasicMaterial + scene.add()
- **CONFIRMED**: Multiple colored objects can be rendered simultaneously at arbitrary 3D coordinates
- **NEXT STEP**: Implement WebSocket command handler to expose this capability to MCP tools

### 2. **`zoom_and_orient(target_x, target_y, target_z, distance=5)` [TO BE VALIDATED]**
```python
# Point camera toward target and move to optimal viewing distance
zoom_and_orient(120, 65, 180, distance=10)
# → Moves player camera to look at coordinate (120,65,180) from 10 blocks away
# → Returns: new screenshot from adjusted viewpoint
```

**Initial Implementation:**
- Calculate viewing angle and position using basic trigonometry
- Use MCP to adjust player look direction and position
- **Simplest version:** Just rotate camera, don't move player
- **Backup options:** If camera control proves difficult, consider teleportation or multi-angle screenshots

### 3. **`detect_blocks_in_view(block_types=["chest", "door", "stairs"])` [CANDIDATE APPROACH]**
```python
# Identify specific block types in current view and mark them
detect_blocks_in_view(["oak_door", "chest"])
# → Returns: screenshot with bounding boxes around detected blocks
# → Also returns: list of 3D coordinates of detected blocks
```

**Experimental Implementation:**
- Use MCP to get block data in viewing range
- Project 3D block coordinates to 2D screen coordinates  
- Draw bounding boxes on screenshot
- **Simplest version:** Use Minecraft's built-in block detection via MCP
- **Alternative considerations:** Computer vision models, ray-casting, or semantic segmentation

---

## **Supporting Infrastructure (Minimal, Flexible)**

### **`display(image)`** 
- Shows annotated screenshots to the LLM
- **Implementation:** Save image, return file path

### **`get_player_state()`**
- Returns current position, rotation, inventory
- **Implementation:** Use existing MCP client

### **Basic Coordinate System (To Be Refined)**
- World coordinates (x, y, z) 
- Screen coordinates (pixel x, y)
- Simple projection between them
- **Note:** May require significant adjustment based on practical limitations

---

## **✅ UPDATED TIMELINE (ACCELERATED DUE TO BREAKTHROUGH):**

### **Tool Implementation Timeline (FAST TRACK):**
- **Day 1-2:** ✅ **COMPLETE** - Core feasibility proven via browser testing
- **Day 3-4:** Implement WebSocket handler for `annotate_3d_position` 
- **Day 5-6:** Implement `zoom_and_orient` and `detect_blocks_in_view`
- **Week 2:** Full tool validation and first trajectory collection

### **Backup Tool Concepts (NOW PROVEN POSSIBLE):**
- **Path visualization:** Easy to implement with proven Three.js approach
- **Inventory annotation:** Can use same marker system
- **Multi-perspective views:** Camera control validated through existing MCP tools
- **Structural analysis:** Object detection feasible via MCP block scanning
- **Distance/measurement tools:** Coordinate math + visual indicators

### **Potential Pivots:**
- If 3D annotation proves too complex → Focus on 2D overlays with depth cues
- If camera control is unreliable → Use multiple fixed viewpoints
- If block detection is insufficient → Integrate computer vision models
- If tools are too Minecraft-specific → Generalize for broader 3D reasoning

---

## **What's NOT in MVP (But May Become Necessary):**

❌ **Complex Computer Vision:** No advanced ML models (initially)
❌ **Sophisticated Graphics:** No fancy overlays or UI (unless required)
❌ **Multiple Environments:** Only basic Minecraft worlds (for now)
❌ **Advanced Navigation:** No pathfinding algorithms (unless essential)
❌ **Inventory Management:** No complex item interactions (initially)
❌ **Multi-step Planning:** No complex task decomposition (phase 1 focus)
❌ **Error Recovery:** No sophisticated failure handling (basic MVP)

---

## **Flexible Success Criteria:**

✅ **Identify at least 2-3 effective 3D reasoning tools** (may not be the initial candidates)
✅ **LLM can perform basic spatial reasoning** (through whatever tools work)  
✅ **Tools integrate with MCP and trajectory collection** (technical validation)
✅ **Foundation established for scaling to 50 examples** (pipeline readiness)
✅ **Completed within 2-4 weeks** (allowing for iteration time)

### **Validation Criteria for Each Tool:**
- **Does the LLM use it correctly in practice?**
- **Does it enable spatial reasoning that wasn't possible before?**
- **Is it technically reliable in the Minecraft environment?**
- **Can it be easily reproduced in trajectory collection?**

---

## **Hypothetical Example Trajectory (Subject to Tool Evolution):**
```
Human: "Find the nearest chest and mark it"

LLM Thought: I need to detect chests in my current view, then annotate the nearest one.

Action 1: detect_blocks_in_view(["chest"])  # [assuming this tool proves effective]
Observation: Found chest at coordinates (105, 64, 195), 15 blocks away

Action 2: annotate_3d_position(105, 64, 195, "nearest_chest", "green")  # [if annotation works well]
Observation: Screenshot showing green marker on the chest

Action 3: zoom_and_orient(105, 64, 195, distance=3)  # [if camera control is reliable]
Observation: Close-up view of the marked chest

Answer: "The nearest chest is at (105, 64, 195), now marked in green."
```

*Note: This trajectory assumes our initial tool candidates prove effective. The actual tools and workflow may evolve significantly during implementation and testing.*

---

## **Discovery-Focused Implementation Strategy:**

### **Week 1: Rapid Prototyping**
- Implement simplest possible versions of all 3 candidate tools
- Test basic functionality, expect significant gaps

### **Week 2: Empirical Testing** 
- Try tools in realistic scenarios
- Document what works, what doesn't, and why
- Begin identifying necessary modifications

### **Week 3: Iteration Based on Evidence**
- Modify existing tools based on testing
- Prototype alternative approaches for failing components
- Consider entirely different tool concepts if needed

### **Week 4: Validation & Refinement**
- Finalize tool set that demonstrably enables 3D reasoning
- Ensure tools work reliably for trajectory collection
- Document lessons learned for future phases

This experimental approach treats Phase 0 as **tool discovery and validation** rather than implementation of predetermined solutions, acknowledging that effective 3D reasoning tools may differ significantly from our initial hypotheses.


# Collection Software MVP (Phase 0)

## 🎯 **MVP Goal:** 
Experiment with trajectory recording formats to find an approach suitable for training, expecting iteration on the data structure.

The collection software will be integrated into the existing pygame-based minecraft client.

---

## **Integration Architecture (Experimental!)**

### **Existing pygame MinecraftController Foundation:**
- **WebSocket connection** to Minecraft client (localhost:8081)
- **pygame UI** with joysticks, buttons, camera controls  
- **Real-time screenshot capture** capability via WebSocket
- **Player state tracking** (position, rotation, movement, actions)
- **Event handling system** for keyboard shortcuts (F5/F6 already mentioned)
- **Command sending pipeline** for all Minecraft actions

### **Recording Integration Approach:**
**Key insight:** Add recording as a *background feature* to the existing controller, not a separate system.

**Recording State Management:** Extend MinecraftController with recording flags, current trajectory, task description, and trajectory counter.

**F5/F6 Hotkey Integration:** Hook into existing keyboard event handling to start/stop recording seamlessly during gameplay.

**Background Data Capture:** Leverage existing screenshot and state tracking systems to automatically capture observations during tool execution.

**Tool Call Integration:** Add hooks to existing 3D tool execution pipeline to automatically record tool calls and results in conversation format.

### **OpenAIAsyncMessageChain Format Integration:**
*Trajectories stored as conversation chains with embedded images, compatible with training pipeline.*

**Conversation Structure:** 
- User messages contain screenshots + context
- Assistant messages contain reasoning + tool calls  
- Tool results become additional user messages
- Entire trajectory serialized as single JSON with base64 images

### **User Workflow (Integrated Experience):**

#### **Normal Gameplay + Recording:**
1. **Start pygame client** → Normal Minecraft control interface loads
2. **F5 key** → Task input prompt, recording starts in background
3. **Continue normal gameplay** → Use joysticks, buttons, camera controls as usual
4. **LLM calls 3D tools** → Automatically captured via integrated hooks
5. **F6 key** → Recording stops, trajectory saved as conversation JSON

#### **UI Integration (Added to Existing Interface):**
- **Recording status indicator** → Visual feedback in pygame window
- **Task description display** → Show current task being recorded  
- **Trajectory counter** → Track number of completed recordings
- **Seamless operation** → No disruption to normal Minecraft control experience

### **Integration Points (Added to MinecraftController):**

#### **Recording Management:**
- **Start/stop recording methods** → Triggered by F5/F6 hotkeys
- **Task description input** → Simple prompt for trajectory labeling
- **Automatic state capture** → Leverage existing screenshot/position systems
- **Conversation chain management** → OpenAIAsyncMessageChain lifecycle

#### **Tool Execution Hooks:**
- **Pre-tool capture** → Screenshot and state before tool execution
- **Tool call recording** → Automatic logging of 3D reasoning tools
- **Post-tool capture** → Screenshot and state after tool execution  
- **Result integration** → Tool outputs added to conversation chain

#### **File Management:**
- **Automatic directory creation** → Ensure data/manual_50/ exists
- **Sequential naming** → traj_001.json, traj_002.json, etc.
- **JSON serialization** → Direct OpenAIAsyncMessageChain export
- **Self-contained files** → No separate image folder management

---

## **Proposed File Structure (To Be Validated!):**
```
data/
├── manual_50/
│   ├── traj_001.json          # Complete conversation chain with embedded images
│   ├── traj_002.json          # No separate image folders needed!
│   ├── traj_003.json
│   └── ...
├── metadata/                   # Optional metadata if needed
│   ├── task_descriptions.json
│   └── collection_stats.json
```

**Key Benefits of This Approach (Hypothesis):**
- **Simplified file management:** No image folder coordination
- **Atomic trajectories:** Each JSON file is completely self-contained
- **Training pipeline compatibility:** Direct input to model training
- **Automatic image handling:** Base64 encoding handled by framework
- **Version control friendly:** Single file per trajectory
- **Backup/transfer simple:** Just copy JSON files

**Potential Drawbacks (To Monitor):**
- Large file sizes due to embedded images
- Memory usage during loading
- Possible JSON parsing complexity

---

## **What's NOT in Initial Experiment (But May Become Necessary):**

❌ **Real-time Validation:** No quality checking during collection (initially)
❌ **Replay System:** No ability to replay trajectories (may be needed later)
❌ **Data Compression:** Accept large file sizes initially  
❌ **Multiple Formats:** Only OpenAIAsyncMessageChain JSON (may need alternatives)
❌ **Monitoring Dashboard:** No web interface or progress tracking (basic logging only)
❌ **Error Recovery:** If collection crashes, start over (improve in iteration)
❌ **Parallel Collection:** Single threaded only (scale later if needed)
❌ **Advanced Metadata:** No task difficulty, success metrics, etc (add if required)
❌ **Data Versioning:** No git-like tracking of changes (simple file management)
❌ **Automatic Backup:** No cloud sync or redundancy (manual backup initially)

---

## Updated Success Criteria:

✅ **3D scene modification proven feasible** (browser console test successful)
- **Can record 1 complete trajectory in conversation format** (prove concept works)
- **Serialized data can be deserialized without loss** (round-trip integrity)
- **Images are properly embedded and viewable** (no broken image links)  
- **Data format is compatible with training pipeline** (actual usability test)
- **Takes <2 days to implement basic version** (accelerated timeline)
- **Works reliably with MCP and 3D tools** (practical integration)

**Backup Success Criteria (If OpenAIAsyncMessageChain Doesn't Work):**
- Fall back to simpler JSON + separate image files approach
- Implement custom serialization that mimics conversation format
- Use existing trajectory formats from other agent frameworks

---

## **Scope Creep Trap Areas (Even More Important with New Approach!):**

### **🚫 Complex Data Validation**
```python
# SCOPE CREEP (don't do this yet):
def validate_conversation_trajectory(chain):
    if not has_proper_message_alternation(chain): return False
    if images_are_corrupted_in_base64(chain): return False  
    if tool_calls_dont_match_schema(chain): return False
    # ... 50 more validation rules
    
# EXPERIMENTAL APPROACH (do this):
async def save_trajectory(chain):
    trajectory_json = chain.to_json()  # Just serialize it!
    with open(f"traj_{uuid4()}.json", "w") as f:
        f.write(trajectory_json)
```

### **🚫 Advanced Conversation Management**
```python
# SCOPE CREEP:
class SmartTrajectoryBuilder:
    def auto_merge_duplicate_observations(self): ...
    def compress_redundant_tool_calls(self): ...
    def smart_conversation_branching(self): ...
    def optimize_image_embeddings(self): ...

# EXPERIMENTAL APPROACH: 
# Use OpenAIAsyncMessageChain as-is, learn what works first
```

### **🚫 Perfect Format Optimization**
```python
# SCOPE CREEP:
def optimize_trajectory_format():
    compressed_images = compress_all_base64()
    deduplicated_context = remove_redundancy()
    optimized_schema = create_custom_format()
    # ... spend weeks perfecting storage format

# EXPERIMENTAL APPROACH:
# Accept large files initially, optimize only if it becomes a real problem
```

---

## **Iterative Implementation Strategy:**
## **The 3 Plans We Drafted:**

### **1. Three.js Implementation Plan**
[RENDERER_DRAWING_GUIDE.md](RENDERER_DRAWING_GUIDE.md)
- **Purpose**: Browser-side 3D cube rendering in Minecraft world
- **Scope**: WebSocket message handling, Three.js geometry/material creation, scene.add() calls
- **Layer**: Browser client (where the visual markers actually appear)

### **2. MCP Server Implementation Plan** 
[ANNOTATE_3D_POSITION_MCP_IMPLEMENTATION.md](ANNOTATE_3D_POSITION_MCP_IMPLEMENTATION.md)
- **Purpose**: Add `annotate_3d_position` tool to `minecraft-mcp-server.ts`
- **Scope**: Tool definition with zod schema, WebSocket command sending, screenshot capture
- **Layer**: TypeScript MCP server (the bridge between agent loop and browser)

### **3. Pygame Integration Plan**
[PYGAME_TRAJECTORY_RECORDING_INTEGRATION.md](PYGAME_TRAJECTORY_RECORDING_INTEGRATION.md)
- **Purpose**: Recording integration into existing `MinecraftController`
- **Scope**: F5/F6 hotkeys, trajectory capture using OpenAIAsyncMessageChain format
- **Layer**: Python pygame controller (where humans control and recording happens)





**Key Learning Questions:**
- Does OpenAIAsyncMessageChain handle our image volumes?
- Are file sizes manageable for 50 trajectories?
- Does the conversation format actually work for training?
- Do we need custom metadata that doesn't fit the conversation model?

**Potential Pivots Based on Findings:**
- If file sizes are too large → Implement image compression or separate storage
- If conversation format is awkward → Add custom metadata fields  
- If serialization is unreliable → Fallback to manual JSON approach
- If training pipeline doesn't accept this format → Build conversion utilities

**Golden Rule:** If it doesn't directly enable testing the OpenAIAsyncMessageChain approach for collecting the first few trajectories, it's scope creep!

---


### **Native Multimodal Support:**
- Conversation format should be directly consumable by training scripts
- Images already embedded and properly formatted  
- Tool calls in standard OpenAI format
- No custom serialization/deserialization needed

### **Potential Simplifications:**
- **Phase 4 (SFT):** May require minimal data preprocessing
- **Phase 5 (GRPO):** Trajectory comparison becomes conversation comparison
- **Phase 7 (Evaluation):** Can directly feed conversations to evaluation models


