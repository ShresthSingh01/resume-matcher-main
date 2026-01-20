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
         # Hardcoded "Rachel" Voice ID for consistent, professional female interviewer tone.
         # ID: 21m00Tcm4TlvDq8ikWAM
         return "21m00Tcm4TlvDq8ikWAM"

    def generate_audio(self, text: str) -> bytes:
        """
        Generates full audio from text using ElevenLabs.
        Returns bytes (buffered). Raises exception if empty.
        """
        if not self.client:
            raise ValueError("ElevenLabs API Key is missing.")

        voice_id = self.get_best_voice()
        # Updated for ElevenLabs v3+ SDK
        audio_stream = self.client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id="eleven_monolingual_v1",
            output_format="mp3_44100_128",
        )
        
        # Buffer into memory to catch errors immediately
        audio_data = b"".join(chunk for chunk in audio_stream)
        
        if len(audio_data) == 0:
            raise ValueError("ElevenLabs returned empty audio (Quota Exceeded?).")
            
        return audio_data
