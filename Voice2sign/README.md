# 🎙️ Voice2Sign: Speak to 3D Sign Language Conversion System

A complete end-to-end system that converts **speech → text → 3D Indian Sign Language animations** using real-time speech recognition, Python preprocessing, and Blender-generated ISL animations. This project aims to support accessibility and bridge communication gaps for the Deaf and Hard-of-Hearing community.

---

## 🚀 Overview

Voice2Sign is an interactive web application that:

* Captures **live speech**.
* Converts audio to **text**.
* Preprocesses text using Python + NLTK.
* Maps processed text to **ISL animations**.
* Displays 3D animations generated using Blender.

Supports both **voice input** and **manual text entry**.

---

## ✨ Features

* 🎤 Real-time Speech Recognition (Web Speech API)
* ✍️ Text preprocessing (NLTK)
* 🧍‍♀️ 3D ISL animations (Blender)
* 🔐 User authentication system
* 🎛️ Clean and responsive UI
* ⚙️ Django backend logic and asset handling

---

## 🛠️ Tech Stack

### **Frontend**

* HTML, CSS, JavaScript
* Web Speech API

### **Backend**

* Python 3.7+
* Django Framework
* NLTK for text tokenization and preprocessing

### **3D Animation**

* Blender

---

## 📦 Prerequisites

* Python >= 3.7
* Browser supporting Web Speech API (Chrome recommended)
* Install Python dependencies before running

---

## ⚙️ Installation Guide

### **1. Clone the Repository**

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

### **2. (Optional) Create a Virtual Environment**

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv/Scripts/activate     # Windows
```

### **3. Install Requirements**

```bash
pip install -r requirements.txt
```

### **4. Run the Development Server**

```bash
python manage.py runserver
```

### **5. Open in Browser**

```
http://127.0.0.1:8000/
```

---

## 🧭 How to Use

1. Sign up or log in.
2. Go to the **Home** page.
3. Click the 🎤 **Mic button** to begin speech capture.
4. Speak
