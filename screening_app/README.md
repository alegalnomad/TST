# TST Screening App

A Flutter mobile application for automated Tuberculin Skin Test (TST) interpretation, developed as part of the dissertation *"Mobile Image Segmentation App for Mantoux Skin Test"* at the University of Nottingham.

## What It Does

The app allows clinicians to capture an image of a TST injection site and receive an automated reading. The image is sent to a backend server where YOLO detects the site and SAM segments the induration, returning the result to the app.

## Prerequisites

- [Flutter SDK](https://docs.flutter.dev/get-started/install) (3.0+)
- The backend server running — see [`/server`](../server)
- Device with a camera (iOS or Android)

## Setup

1. Navigate to this directory:
   ```bash
   cd screening_app
   ```

2. Install dependencies:
   ```bash
   flutter pub get
   ```

3. Copy the environment template in the root of the repo and set your server URL:
   ```bash
   cp ../.env.example ../.env
   ```

4. Run the app:
   ```bash
   flutter run
   ```

## Notes

- The backend server must be running and reachable from the device before using the app
- Ensure camera permissions are granted on the device
