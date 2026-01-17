import os
from elevenlabs import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ELEVENLABS_API_KEY")

class TTSManager:
    def __init__(self):
        print(f"DEBUG: Initializing TTSManager. API Key present: {bool(API_KEY)}")
        if API_KEY:
            self.client = ElevenLabs(api_key=API_KEY)
        else:
            self.client = None
            print("Warning: ELEVENLABS_API_KEY not found. TTS will not work.")

    def correct_pronunciation(self, text: str) -> str:
     corrections = {
        # Core Programming & CS
        "SQL": "Sequel",
        "NoSQL": "No Sequel",
        "Python": "Pie-thon",
        "Java": "Jah-vuh",
        "C++": "C plus plus",
        "C#": "C sharp",
        "JavaScript": "Java Script",
        "TypeScript": "Type Script",
        "Node.js": "Node J S",
        "Django": "Jang-go",
        "Flask": "Flask",
        "Kotlin": "Kot-lin",
        "Swift": "Swift",
        "Go": "Go Lang",
        "Rust": "Rust",

        # AI / ML / Data Science
        "AI": "A I",
        "ML": "M L",
        "DL": "Deep Learning",
        "LLM": "L L M",
        "NLP": "N L P",
        "CNN": "C N N",
        "RNN": "R N N",
        "GAN": "G A N",
        "Transformer": "Transform-er",
        "t-SNE": "Tee Snee",
        "XGBoost": "X G Boost",
        "LightGBM": "Light G B M",
        "CatBoost": "Cat Boost",
        "PCA": "P C A",
        "KNN": "K N N",

        # Math & Algorithms
        "O(n)": "Big O of N",
        "O(log n)": "Big O of log N",
        "O(n^2)": "Big O of N square",
        "DFS": "D F S",
        "BFS": "B F S",
        "Dijkstra": "Dike stra",
        "Fibonacci": "Fibo-nah-chee",
        "Naive Bayes": "Naive Bayes",
        "Bayesian": "Bay-zee-an",

        # Web & APIs
        "API": "A P I",
        "REST": "Rest",
        "RESTful": "Rest-full",
        "HTTP": "H T T P",
        "HTTPS": "H T T P S",
        "JSON": "J Son",
        "XML": "X M L",
        "GraphQL": "Graph Q L",
        "OAuth": "O Auth",
        "JWT": "J W T",

        # DevOps & Cloud
        "AWS": "A W S",
        "GCP": "G C P",
        "Azure": "A-zure",
        "Docker": "Dock-er",
        "Kubernetes": "Koo-ber-net-ees",
        "CI/CD": "C I C D",
        "Git": "Git",
        "GitHub": "Git Hub",
        "GitLab": "Git Lab",
        "Linux": "Lin-ux",
        "Ubuntu": "Oo-boon-too",

        # Databases
        "MySQL": "My Sequel",
        "PostgreSQL": "Post Gres Sequel",
        "MongoDB": "Mongo D B",
        "Redis": "Red-iss",
        "SQLite": "S Q Lite",

        # System & Architecture
        "CPU": "C P U",
        "GPU": "G P U",
        "RAM": "Ram",
        "SSD": "S S D",
        "HDD": "H D D",
        "Microservices": "Micro services",
        "Monolith": "Mono-lith",
        "Load Balancer": "Load Balancer",

        # Security
        "SSL": "S S L",
        "TLS": "T L S",
        "AES": "A E S",
        "RSA": "R S A",
        "SHA": "S H A",
        "Hashing": "Hash-ing",

        # Data & Analytics
        "ETL": "E T L",
        "OLAP": "O Lap",
        "OLTP": "O L T P",
        "BI": "B I",
        "KPI": "K P I",

        # File & Formats
        "CSV": "C S V",
        "YAML": "Yam-ul",
        "Parquet": "Par-kay",
        "Avro": "Av-ro"
    }

    for term, replacement in corrections.items():
        text = text.replace(term, replacement)

    return text
   

    def get_best_voice(self):
         # Try to find 'Adam', 'Josh' (US Male), 'Rachel' (US Female)
         try:
             all_voices = self.client.voices.get_all()
             
             for v in all_voices.voices:
                 if "Adam" in v.name or "Josh" in v.name: return v.voice_id
             
             for v in all_voices.voices:
                 if "Rachel" in v.name: return v.voice_id
                 
             return all_voices.voices[0].voice_id
         except:
             return "nPczCJZxpgCpKD07lhj7" # Fallback to hardcoded Brian

    def stream_audio(self, text: str):
        """
        Generates audio stream from text using ElevenLabs.
        Returns a generator yielding bytes.
        """
        if not self.client:
            raise ValueError("ElevenLabs API Key is missing.")

        try:
            voice_id = self.get_best_voice()
            # Updated for ElevenLabs v3+ SDK
            audio_stream = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_turbo_v2_5",
                output_format="mp3_44100_128",
            )
            
            for chunk in audio_stream:
                yield chunk
                
        except Exception as e:
            print(f"TTS Error: {e}")
            raise e
