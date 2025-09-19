from flask import Flask, request, jsonify
from flask_cors import CORS
import os, re, time, uuid, threading
import yt_dlp
import whisper
import nltk
from nltk.tokenize import sent_tokenize
from rouge_score import rouge_scorer

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

os.environ["PATH"] += os.pathsep + r"D:\NLP\ffmpeg-7.0.2-essentials_build\bin"


# Download NLTK resources
nltk.download('punkt')


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Create necessary directories
os.makedirs("downloads", exist_ok=True)
os.makedirs("transcripts", exist_ok=True)
os.makedirs("summaries", exist_ok=True)

MODEL_NAME = "sshleifer/distilbart-cnn-12-6"

tokenizer = None
summ_model = None
whisper_model = None
models_ready = threading.Event()  # set when loader finishes

# Token/window config (stay under 1024; keep headroom)
MAX_SOURCE_TOKENS = 960
CHUNK_OVERLAP_TOKENS = 96

GEN_ARGS = dict(
    max_length=180,          # per-chunk output length
    min_length=60,
    num_beams=4,
    no_repeat_ngram_size=3,
    length_penalty=1.05
)

job_status = {}

def load_models():
    """Load HF summarizer and Whisper once at startup."""
    global tokenizer, summ_model, whisper_model
    try:
        print("Loading summarization model...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)
        summ_model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
        print("Loading Whisper model...")
        whisper_model = whisper.load_model("base")  # or "small.en"/"medium"
        print("Models loaded successfully.")
    except Exception as e:
        print(f"❌ Model load failed: {e}")
    finally:
        models_ready.set()

# Load models in a separate thread at startup
threading.Thread(target=load_models, daemon=True).start()

def clean_text(text):
    """Clean the text by removing extra spaces and filler words"""
    text = re.sub(r"\s+", " ", text)
    text = text.replace("uh", "").replace("um", "")
    return text.strip()

def _encode(text: str):
    return tokenizer(text, add_special_tokens=False).input_ids

def _decode(ids):
    return tokenizer.decode(ids, skip_special_tokens=True)

def chunk_by_tokens(text: str,
                    max_tokens: int = MAX_SOURCE_TOKENS,
                    overlap: int = CHUNK_OVERLAP_TOKENS):
    """Token-aware sliding window chunking."""
    ids = _encode(text)
    if not ids:
        return []
    chunks, start = [], 0
    step = max(max_tokens - overlap, 1)
    while start < len(ids):
        end = min(start + max_tokens, len(ids))
        chunks.append(_decode(ids[start:end]))
        if end == len(ids):
            break
        start += step
    return chunks

def summarize_block(text: str) -> str:
    """Summarize a single block safely within token limits."""
    enc = tokenizer(text, return_tensors="pt", truncation=True, max_length=MAX_SOURCE_TOKENS)
    out = summ_model.generate(**enc, **GEN_ARGS)
    return tokenizer.decode(out[0], skip_special_tokens=True).strip()

def hierarchical_summarize(long_text: str) -> str:
    """Chunk → summarize each → merge → second-hop summarize."""
    chunks = chunk_by_tokens(long_text)
    if not chunks:
        return ""
    if len(chunks) == 1:
        return summarize_block(chunks[0])

    part_summaries = [summarize_block(c) for c in chunks]
    combined = " ".join(part_summaries)

    # If combined is still long, do a quick hop
    if len(_encode(combined)) > MAX_SOURCE_TOKENS:
        hop_chunks = chunk_by_tokens(combined)
        hop_sums = [summarize_block(c) for c in hop_chunks]
        combined2 = " ".join(hop_sums)
        if len(_encode(combined2)) > MAX_SOURCE_TOKENS:
            return summarize_block(combined2)
        return combined2
    else:
        # one more pass for coherence
        return summarize_block(combined)

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
    job_status[job_id]['status'] = 'summarizing'
        
    models_ready.wait()

    if tokenizer is None or summ_model is None:
        raise RuntimeError("Summarization model not available")
            
    cleaned_transcript = clean_text(transcript)
        
    if len(_encode(cleaned_transcript)) <= MAX_SOURCE_TOKENS:
        final_summary = summarize_block(cleaned_transcript)
    else:
        chunks = chunk_by_tokens(cleaned_transcript)
        summaries = []
        for i, ch in enumerate(chunks, 1):
            job_status[job_id]["progress"] = f"Summarizing chunk {i}/{len(chunks)}"
            summaries.append(summarize_block(ch))
        merged = " ".join(summaries)
        if len(_encode(merged)) > MAX_SOURCE_TOKENS:
            final_summary = hierarchical_summarize(merged)
        else:
            final_summary = summarize_block(merged)

    # Save
    with open(f"summaries/{job_id}.txt", "w", encoding="utf-8") as f:
        f.write(final_summary.strip())

    return final_summary.strip()

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
    data = request.json or {}
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
    threading.Thread(target=process_video, args=(video_url, job_id), daemon=True).start()
    
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