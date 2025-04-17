# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import yt_dlp
import whisper
import re
import nltk
from nltk.tokenize import sent_tokenize
from transformers import pipeline
import uuid
from rouge_score import rouge_scorer
import threading
import time

os.environ["PATH"] += os.pathsep + r"D:\NLP\ffmpeg-7.0.2-essentials_build\bin"


# Download NLTK resources
nltk.download('punkt')
nltk.download('punkt_tab')


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Create necessary directories
os.makedirs("downloads", exist_ok=True)
os.makedirs("transcripts", exist_ok=True)
os.makedirs("summaries", exist_ok=True)

# Global variables
summarizer = None
whisper_model = None
job_status = {}  # Track status of async jobs

def load_models():
    global summarizer, whisper_model
    print("Loading summarization model...")
    summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    print("Loading Whisper model...")
    whisper_model = whisper.load_model("base")
    print("Models loaded successfully")

# Load models in a separate thread at startup
threading.Thread(target=load_models).start()

def clean_text(text):
    """Clean the text by removing extra spaces and filler words"""
    text = re.sub(r"\s+", " ", text)
    text = text.replace("uh", "").replace("um", "")
    return text.strip()

def download_video(video_url, job_id):
    """Download video using yt-dlp"""
    try:
        job_status[job_id]['status'] = 'downloading'
        
        video_path = f"downloads/{job_id}.mp4"
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
            'outtmpl': video_path,
            'ffmpeg_location': r'D:\NLP\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        return video_path
    except Exception as e:
        job_status[job_id]['error'] = f"Error downloading video: {str(e)}"
        raise

def transcribe_video(video_path, job_id):
    """Transcribe video using Whisper"""
    try:
        job_status[job_id]['status'] = 'transcribing'
        
        # Wait for model to load if needed
        while whisper_model is None:
            time.sleep(1)
            
        result = whisper_model.transcribe(video_path)
        transcript = result["text"]
        
        # Save transcript
        transcript_path = f"transcripts/{job_id}.txt"
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(transcript)
            
        return transcript
    except Exception as e:
        job_status[job_id]['error'] = f"Error transcribing video: {str(e)}"
        raise

def generate_summary(transcript, job_id):
    """Generate summary from transcript"""
    try:
        job_status[job_id]['status'] = 'summarizing'
        
        # Wait for model to load if needed
        while summarizer is None:
            time.sleep(1)
            
        cleaned_transcript = clean_text(transcript)
        
        # Break transcript into chunks
        sentences = sent_tokenize(cleaned_transcript)
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) < 1000:
                current_chunk += " " + sentence
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
                
        if current_chunk:
            chunks.append(current_chunk.strip())

        # Summarize each chunk
        summaries = []
        for i, chunk in enumerate(chunks):
            job_status[job_id]['progress'] = f"Summarizing chunk {i+1}/{len(chunks)}"
            result = summarizer(chunk, max_length=130, min_length=30, do_sample=False)
            summaries.append(result[0]['summary_text'])

        # Create final summary
        if len(summaries) > 1:
            combined_summaries = " ".join(summaries)
            final_summary = summarizer(combined_summaries, max_length=250, min_length=100, do_sample=False)[0]['summary_text']
        else:
            final_summary = summaries[0]
            
        # Save summary
        summary_path = f"summaries/{job_id}.txt"
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(final_summary.strip())
            
        return final_summary.strip()
    except Exception as e:
        job_status[job_id]['error'] = f"Error generating summary: {str(e)}"
        raise

def process_video(video_url, job_id):
    try:
        print(f"🔁 Starting processing for {job_id}")

        video_path = download_video(video_url, job_id)
        print(f"✅ Downloaded video to: {video_path}")

        transcript = transcribe_video(video_path, job_id)
        print(f"✅ Transcript created: {len(transcript)} chars")

        summary = generate_summary(transcript, job_id)
        print(f"✅ Summary created: {len(summary)} chars")

        job_status[job_id]['status'] = 'completed'
        job_status[job_id]['summary'] = summary

    except Exception as e:
        print(f"❌ Error in processing: {str(e)}")
        job_status[job_id]['status'] = 'failed'
        if 'error' not in job_status[job_id]:
            job_status[job_id]['error'] = str(e)


@app.route('/api/summarize', methods=['POST'])
def start_summarization():
    """Start the summarization process"""
    data = request.json
    video_url = data.get('videoUrl')
    
    if not video_url:
        return jsonify({'error': 'Video URL is required'}), 400
    
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    job_status[job_id] = {
        'status': 'queued',
        'videoUrl': video_url
    }
    
    # Start processing in a separate thread
    threading.Thread(target=process_video, args=(video_url, job_id)).start()
    
    return jsonify({
        'jobId': job_id,
        'status': 'queued'
    })

@app.route('/api/status/<job_id>', methods=['GET'])
def check_status(job_id):
    """Check the status of a summarization job"""
    if job_id not in job_status:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(job_status[job_id])

@app.route('/api/evaluate', methods=['POST'])
def evaluate_summary():
    """Evaluate a summary using ROUGE score"""
    data = request.json
    reference = data.get('reference')
    generated = data.get('generated')
    
    if not reference or not generated:
        return jsonify({'error': 'Both reference and generated summaries are required'}), 400
    
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    scores = scorer.score(reference, generated)
    
    result = {}
    for metric, score in scores.items():
        result[metric] = {
            'precision': score.precision,
            'recall': score.recall,
            'f1': score.fmeasure
        }
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5000, threaded=True)