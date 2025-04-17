# 🎬 VideoVerse: YouTube Video Summarization using NLP

**VideoVerse** is a full-stack NLP application that takes a YouTube video URL, transcribes its audio using Whisper, and generates a concise abstractive summary using transformer-based models. Built with a modern React + Flask architecture, this project showcases how natural language processing can be applied to real-world video content.

---

## 📌 Features

- 🔗 Accepts any YouTube video URL
- 🎙️ Transcribes speech to text using [Whisper](https://github.com/openai/whisper)
- ✂️ Preprocesses and chunks long transcripts
- 📝 Generates abstractive summaries using transformer models (`DistilBART`)
- 📊 Supports ROUGE-based evaluation against reference summaries
- ⚙️ Full asynchronous backend job queue
- 🖥️ Frontend built with modern UI and real-time updates

---

## 🧠 NLP Pipeline

YouTube Video → Audio Extraction → Whisper ASR → Text Cleaning → Sentence Splitting → Chunking → Abstractive Summarization → Summary


---

## 🛠️ Tech Stack

| Layer        | Tools & Frameworks |
|--------------|--------------------|
| **Frontend** | React, TypeScript, Tailwind CSS, shadcn-ui |
| **Backend**  | Flask (Python), Flask-CORS |
| **NLP**      | Whisper, Hugging Face Transformers (DistilBART), NLTK |
| **Utilities**| yt-dlp, ffmpeg, uuid, threading, ROUGE Score |

---

## 🚀 Setup Instructions

### ⚙️ Prerequisites

- Python 3.8+
- Node.js (v18+ recommended)
- `ffmpeg` installed and added to system PATH
- `pip`, `npm`, `git` installed

---

### 🔌 Backend Setup (Flask)

```bash
# Clone the repository
git clone https://github.com/99anjalipai/nlp-project.git
cd backend

# Create a virtual environment and activate it
python -m venv venv
venv\Scripts\activate  # On Windows
source venv/bin/activate  # On Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Download NLTK models
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"

# Run the server
flask run

The backend runs on http://localhost:5000

### 🔌 Frontend Setup (React)


# Install dependencies
npm install

# Start development server
npm run dev


📹 Using the UI
Open your browser and go to http://localhost:5173.

Paste a YouTube video URL.

Click "Generate Summary".

The app will:

Download the video

Transcribe it

Summarize the transcript

Final summary will be displayed on the screen. (Might take a few minutes)