import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import os
import csv
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# Global variables
datasetFilePath = None
imageFilePath = None
useLsb = True
resizeEnabled = True

# Function to perform XOR encryption
def xorEncrypt(data, key):
    encryptedData = bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])
    return encryptedData

# Function to perform AES encryption
def aesEncrypt(data, key, iv):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(data.encode(), AES.block_size))

# Function to perform AES decryption
def aesDecrypt(data, key, iv):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(data), AES.block_size).decode()

# Function to toggle between LSB and MSB bit modes
def toggleBitMode():
    global useLsb
    useLsb = not useLsb
    bitModeButton.config(text=f"Mode: {'LSB' if useLsb else 'MSB'}")
    displayMessage(f"Bit mode switched to: {'LSB' if useLsb else 'MSB'}", "green")

# Function to toggle image resizing
def toggleResize():
    global resizeEnabled
    resizeEnabled = not resizeEnabled
    displayMessage(f"Image resizing {'enabled' if resizeEnabled else 'disabled'}.", "green")

# Function to display messages in the GUI
def displayMessage(message, color):
    errorLabel.config(text=message, fg=color)
    errorLabel.update_idletasks()

# Function to select a dataset file
def selectDataset():
    global datasetFilePath
    datasetFilePath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    if datasetFilePath:
        displayMessage(f"Dataset selected: {os.path.basename(datasetFilePath)}", "green")
        pickImageButton.config(state="normal")
    else:
        displayMessage("No dataset selected.", "red")

# Function to select an image file
def selectImage():
    global imageFilePath
    imageFilePath = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif")])
    if imageFilePath:
        try:
            img = Image.open(imageFilePath)
            img = resizeImage(img, (380, 300))
            tkImg = ImageTk.PhotoImage(img)
            canvas.delete("all")
            canvas.create_image(200, 150, image=tkImg, anchor="center")
            canvas.image = tkImg
            encryptButton.config(state="normal")
            displayMessage("Image selected successfully.", "green")
        except Exception as e:
            displayMessage(f"Error loading image: {e}", "red")
    else:
        displayMessage("No image selected.", "red")

# Function to resize an image
def resizeImage(image, targetSize):
    targetWidth, targetHeight = targetSize
    originalWidth, originalHeight = image.size
    scale = min(targetWidth / originalWidth, targetHeight / originalHeight)
    newWidth = int(originalWidth * scale)
    newHeight = int(originalHeight * scale)
    return image.resize((newWidth, newHeight), Image.LANCZOS)

# Function to modify image pixels to embed binary text
def modifyImagePixels(image, binTxt):
    pixels = list(image.getdata())
    pixelsModified = []
    for pixel in pixels:
        r, g, b = pixel[:3]
        if binTxt:
            if useLsb:
                r = (r & ~1) | int(binTxt.pop(0))
            else:
                r = (r & ~(1 << 7)) | (int(binTxt.pop(0)) << 7)
        pixelsModified.append((r, g, b))
    return pixelsModified

# Function to calculate new dimensions for the image
def calculateNewDimensions(sizeOfImage, ratio):
    newHeight = int((sizeOfImage / ratio) ** 0.5)
    newWidth = int(newHeight * ratio)
    while (newWidth * newHeight < sizeOfImage) or ((newWidth * newHeight) % 8 != 0):
        newHeight += 1
        newWidth = int(newHeight * ratio)
    return newWidth, newHeight

# Function to extract key and IV from a file
def extractKeyAndIv():
    keyIvPath = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")], title="Select the key and IV file")
    with open(keyIvPath, "r") as f:
        key = bytes.fromhex(f.readline().strip())
        iv = bytes.fromhex(f.readline().strip())
    return key, iv

# Function to run the encryption process
def runEncryption():
    if not datasetFilePath:
        displayMessage("No dataset selected. Please select a dataset first.", "red")
        return

    savePath = filedialog.asksaveasfilename(defaultextension=".bmp", filetypes=[("BMP Files", "*.bmp")], title="Save the image")
    if not savePath:
        displayMessage("No save location selected.", "red")
        return

    encryptionType = encryptionTypeVar.get()
    imageName = os.path.basename(savePath)
    with open(datasetFilePath, 'r') as csvfile:
        csvData = csvfile.read()

    try:
        image = Image.open(imageFilePath)
        if encryptionType == "No Encryption":
            binTxt = [bit for byte in csvData.encode() for bit in bin(byte)[2:].zfill(8)]
        elif encryptionType == "AES Encryption":
            key = os.urandom(16)
            iv = os.urandom(16)
            encryptedData = aesEncrypt(csvData, key, iv)
            binTxt = [bit for byte in encryptedData for bit in bin(byte)[2:].zfill(8)]
            saveDir = os.path.dirname(savePath)
            keyIvPath = os.path.join(saveDir, "AES_key_iv_" + imageName + ".txt")
            with open(keyIvPath, "w") as f:
                f.write(key.hex() + "\n")
                f.write(iv.hex() + "\n")
        elif encryptionType == "XOR Encryption":
            key = os.urandom(8)
            encryptedData = xorEncrypt(csvData.encode(), key)
            binTxt = [bit for byte in encryptedData for bit in bin(byte)[2:].zfill(8)]
            saveDir = os.path.dirname(savePath)
            keyIvPath = os.path.join(saveDir, "XOR_key_" + imageName + ".txt")
            with open(keyIvPath, "w") as f:
                f.write(key.hex() + "\n")
            displayMessage(f"XOR key saved to {keyIvPath}", "green")

        lengthBin = bin(len(binTxt))[2:].zfill(64)
        binTxt = list(lengthBin) + binTxt
        sizeOfImage = len(binTxt)
        ratio = image.width / image.height
        newWidth, newHeight = calculateNewDimensions(sizeOfImage, ratio)
        newImage = image.resize((newWidth, newHeight)) if resizeEnabled else image
        pixelsModified = modifyImagePixels(newImage, binTxt)
        newImage.putdata(pixelsModified)
        newImage.save(savePath, 'BMP')
        displayMessage(f"Image saved with hidden data to {savePath}", "green")
    except Exception as e:
        displayMessage(f"Error during embedding data into image: {e}", "red")

# Function to extract text from an image
def extractTextFromImage(imagePath):
    image = Image.open(imagePath)
    txtList = [bin(pixel[0])[2:].zfill(8)[-1 if useLsb else 0] for pixel in list(image.getdata())]
    lengthBin = txtList[:64]
    txtList = txtList[64:]
    numBits = int(''.join(lengthBin), 2)
    txtList = txtList[:numBits]
    encryptedData = bytes([int(''.join(txtList[i:i+8]), 2) for i in range(0, len(txtList), 8)])
    return encryptedData

# Function to run the decryption process
def decrypt():
    decryptionType = encryptionTypeVar.get()
    imagePath = filedialog.askopenfilename(filetypes=[("BMP Files", "*.bmp")], title="Select the encrypted image")
    if not imagePath:
        displayMessage("No image selected for decryption.", "red")
        return

    savePath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")], title="Save the decrypted data as")
    if not savePath:
        displayMessage("No save location selected for decrypted data.", "red")
        return

    try:
        encryptedData = extractTextFromImage(imagePath)
        if decryptionType == "AES Encryption":
            key, iv = extractKeyAndIv()
            decryptedData = aesDecrypt(encryptedData, key, iv)
        elif decryptionType == "XOR Encryption":
            key = extractXorKey()
            decryptedData = xorEncrypt(encryptedData, key)
            decryptedData = decryptedData.decode('utf-8')
        else:
            decryptedData = encryptedData.decode()

        with open(savePath, 'w', newline='', encoding='utf-8') as csvfile:
            csvwriter = csv.writer(csvfile)
            for row in decryptedData.split('\n'):
                csvwriter.writerow(row.split(','))

        displayMessage(f"Decrypted data saved to {savePath}", "green")
    except Exception as e:
        displayMessage(f"Error during decryption: {e}", "red")

# Function to extract XOR key from a file
def extractXorKey():
    keyIvPath = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")], title="Select the key file")
    with open(keyIvPath, "r") as f:
        key = bytes.fromhex(f.readline().strip())
    return key

# Create the main tkinter window
root = tk.Tk()
root.title("CryptoGraph")
root.geometry("500x670")
root.resizable(False, False)
icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
root.iconbitmap(icon_path)

# Canvas to display the image
canvas = tk.Canvas(root, width=400, height=300, bg="gray")
canvas.pack(pady=20)

# Frame for bit mode toggle and encryption method dropdown
bitModeFrame = tk.Frame(root)
bitModeFrame.pack(pady=10)

# Bit mode toggle
bitModeButton = tk.Button(bitModeFrame, text="Mode: LSB", command=toggleBitMode)
bitModeButton.pack(side=tk.LEFT, padx=5)

# Encryption Method Dropdown
encryptionOptions = ["No Encryption", "AES Encryption", "XOR Encryption"]
encryptionTypeVar = tk.StringVar()
encryptionTypeVar.set(encryptionOptions[1])
encryptionTypeMenu = tk.OptionMenu(bitModeFrame, encryptionTypeVar, *encryptionOptions)
encryptionTypeMenu.pack(side=tk.LEFT, padx=5)

# Create a canvas line above Pick Dataset, Pick Image, Mode: LSB, etc.
line1 = tk.Canvas(root, height=2, bg="black")
line1.pack(fill='x', pady=10)

# Frame for buttons (to place Encrypt and Decrypt buttons next to each other)
buttonFrame = tk.Frame(root)
buttonFrame.pack(pady=10)

# Dataset selection
pickDatasetButton = tk.Button(buttonFrame, text="Pick a Dataset", command=selectDataset)
pickDatasetButton.pack(side=tk.LEFT, padx=5)

# Image selection
pickImageButton = tk.Button(buttonFrame, text="Pick an Image", command=selectImage, state="disabled")
pickImageButton.pack(side=tk.LEFT, padx=5)

# Resizing checkbox
resizeCheckbox = tk.Checkbutton(root, text="Enable Image Resizing", command=toggleResize)
resizeCheckbox.select()
resizeCheckbox.pack(pady=5)

# Frame for Encryption Method Dropdown   and Encryption Button next to each other
encryptionFrame = tk.Frame(root)
encryptionFrame.pack(pady=10)

# Encryption button (inside the same frame)
encryptButton = tk.Button(encryptionFrame, text="Run Encryption", command=runEncryption, state="disabled")
encryptButton.pack(side=tk.LEFT, padx=5)

# Create a line above Decrypt button
line2 = tk.Canvas(root, height=2, bg="black")
line2.pack(fill='x', pady=10)

# Frame for Decryption Dropdown and Decrypt Button (side by side)
decryptionFrame = tk.Frame(root)
decryptionFrame.pack(pady=10)

# Decryption button
decryptButton = tk.Button(decryptionFrame, text="Decrypt", command=decrypt, state="normal")
decryptButton.pack(side=tk.LEFT, padx=5)

# Error display label
errorLabel = tk.Label(root, text="", fg="red", wraplength=400)
errorLabel.pack(pady=10)

# Run the tkinter main loop
root.mainloop()