# Human Perception & Performance Tester

A Python-based GUI application designed to evaluate human visual perception and motor performance under varying interface conditions[span_0](start_span)[span_0](end_span). Built with Tkinter / CustomTkinter, this tool allows experimenters to adjust visual parameters, run interaction tests based on visual ergonomics and Fitts' Law, log metrics to a CSV file, and analyze the impact of design choices on user performance[span_1](start_span)[span_1](end_span)[span_2](start_span)[span_2](end_span).

---

## 📌 Features

### 1. Visual Variable Controls
Modify interface parameters in real-time to test performance under different visual constraints[span_3](start_span)[span_3](end_span):
* **Contrast Levels**: Select between `High`, `Medium`, and `Low` contrast modes[span_4](start_span)[span_4](end_span).
* **Size Scaling**: Adjust text and target elements to `Small`, `Medium`, or `Large`[span_5](start_span)[span_5](end_span).
* **Brightness Adjustment**: Control background luminance and widget contrast via a brightness slider[span_6](start_span)[span_6](end_span).

### 2. Interaction Tasks
* **Identification Task**: Evaluates perception and visual clarity by presenting an ambiguous shape under different visual conditions[span_7](start_span)[span_7](end_span).
* **Target Hitting Task (Fitts' Law)**: Measures movement time (in seconds) to click a target button across variable distances and target sizes[span_8](start_span)[span_8](end_span)[span_9](start_span)[span_9](end_span).

### 3. Automatic Data Logging
Results are automatically logged to a CSV file (`performance_log.csv`) capturing key trial variables[span_10](start_span)[span_10](end_span):
* Visual Condition (Contrast, Size, Brightness)[span_11](start_span)[span_11](end_span)
* Task Type (`Identification` or `Target Hitting`)[span_12](start_span)[span_12](end_span)
* Time Taken to Click Target (in seconds)[span_13](start_span)[span_13](end_span)
* User-Reported Ease of Use (Likert Scale: 1 = Very Difficult to 5 = Very Easy)[span_14](start_span)[span_14](end_span)

---

## 🛠️ Requirements & Dependencies

* **Python**: `3.x`[span_15](start_span)[span_15](end_span)
* **GUI Toolkit**: `Tkinter` (standard library) or `CustomTkinter`[span_16](start_span)[span_16](end_span)

To install `customtkinter` (if used):
```bash
pip install customtkinter
