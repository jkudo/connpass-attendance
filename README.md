# Event Registration System

This project is an event registration system that uses OCR (Optical Character Recognition) to scan registration numbers from camera input, verify them against a CSV file of registered participants, and update their attendance status. The system uses `Picamera2` for capturing camera input and `Tesseract` for text recognition.

## Features

- Real-time scanning of registration numbers using a camera.
- Verification of scanned numbers against a CSV file of participants.
- Automatic update of attendance status in the CSV file.
- Display of registration details and status on the screen using Tkinter.

## Requirements

- Python 3.x
- OpenCV
- NumPy
- Pytesseract
- Picamera2
- Pandas
- Tkinter
- PIL (Pillow)
