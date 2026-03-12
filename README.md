# Mobile Image Segmentation App for Mantoux Skin Test (TST)

> **Master's Dissertation** — University of Nottingham  
> **Author:** Raghav Anand  
> **Supervisor:** Tan Chye Cheah

---

## Overview

This repository contains the full codebase developed for the dissertation *"Mobile Image Segmentation App for Mantoux Skin Test"*. The project proposes an automated pipeline for interpreting Tuberculin Skin Test (TST) results — commonly known as the Mantoux test — using computer vision and zero-shot learning techniques.

Manual TST interpretation is error-prone and requires trained clinicians, creating a bottleneck in tuberculosis screening programmes, particularly in resource-limited settings. This system addresses that challenge by combining **YOLOv8** for injection site detection with the **Segment Anything Model (SAM)** for precise skin induration segmentation, deployed via a cross-platform mobile application.

---

## System Architecture

The system consists of three core components:

1. **Detection (YOLO)** — Localises the TST injection site within the captured image
2. **Segmentation (SAM)** — Segments the raised induration area using the YOLO bounding box as a prompt
3. **Mobile App** — Captures images and communicates with a backend server to return the result to the clinician

---

## Repository Structure

```
TST/
├── BlenderDataset/              # Synthetic dataset rendered in Blender
├── PhysicalClayModeledDataset/  # Dataset built from physical clay models
├── SAM_training/                # Fine-tuning scripts and configs for SAM
├── YOLO_training/               # YOLO training notebooks and configs
├── screening_app/               # Flutter mobile application source code
├── server/                      # Backend inference server
├── DataSplit.py                 # Dataset splitting utility
└── .env.example                 # Environment variable template
```

---

## Model Weights

The fine-tuned SAM model weights (`model.pth`, ~370MB) are hosted on Hugging Face due to GitHub's file size limitations:

**🤗 [Download model weights — ALegalNomad/SAM_TB](https://huggingface.co/ALegalNomad/SAM_TB/tree/main)**

After downloading, place the file in the `SAM_training/` directory before running inference or evaluation.

---

## Datasets

Two datasets were constructed for this project:

- **Blender Dataset** — Synthetically rendered forearm images simulating TST induration at various sizes and skin tones, created in Blender
- **Physical Clay Model Dataset** — Photographs of hand-crafted clay forearm models replicating real-world TST presentations

Both datasets are included in this repository and were used to train and validate the YOLO detection and SAM segmentation models.

---

## Getting Started

### Prerequisites

- Python 3.9+
- PyTorch
- Flutter SDK (for the mobile app)
- See individual component folders for dependency details

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/alegalnomad/TST.git
   cd TST
   ```

2. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

3. Download the model weights from [Hugging Face](https://huggingface.co/ALegalNomad/SAM_TB/tree/main) and place in `SAM_training/`

4. Refer to the README within each sub-folder for component-specific setup instructions

---

## Technologies Used

| Component | Technology |
|-----------|-----------|
| Object Detection | YOLOv8 |
| Image Segmentation | Segment Anything Model (SAM) |
| Mobile App | Flutter (Dart) |
| Backend Server | Python |
| Synthetic Data | Blender |

---

## Academic Context

This project was submitted in partial fulfilment of the requirements for the degree of **MSc** at the **University of Nottingham**, under the supervision of **Tan Chye Cheah**.

The work explores the applicability of zero-shot and fine-tuned segmentation models in a clinical imaging context, with a focus on accessibility and deployment in low-resource environments.

---

## License

This repository is provided for academic and research reference purposes. Please contact the author for any other intended use.
