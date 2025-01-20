# CryptoGraph

CryptoGraph is a Python-based graphical user interface (GUI) application designed to embed and extract encrypted data from images using steganography. The program allows users to securely hide datasets (CSV files) inside images using various encryption methods, such as AES or XOR. The encrypted image can then be saved and later decrypted to retrieve the original dataset.

## Key Features

- **Image Steganography**: Embed encrypted data into an image file using either Least Significant Bit (LSB) or Most Significant Bit (MSB) methods.
- **Encryption Methods**:
  - **AES Encryption**: Securely encrypt data before embedding it into the image.
  - **XOR Encryption**: A simpler encryption method using a randomly generated key.
  - **No Encryption**: Embed the data directly without any encryption.
- **Image Resizing**: Optionally resize the image to fit the data being embedded.
- **Decryption**: Extract and decrypt the hidden data from the image file.

## Installation

Before running CryptoGraph, ensure that you have the required libraries installed. You can install them using `pip`:

- **tkinter**: For creating the graphical user interface.
- **Pillow**: For image processing (opening, resizing, etc.).
- **pycryptodome**: For cryptographic operations (AES and XOR encryption).
- **csv**: For reading and writing CSV files.

## How to Use

### Run the Application

Start the application by running the `CryptoGraph.py` script

## Requierment Diagram

![Requierment Diagram](https://i.ibb.co/p1fMvLj/Requierment.png)


