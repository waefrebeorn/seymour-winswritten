
"""
Seymour Clipart Vision Pipeline
Uses Gemma 4 12B (GGUF) via llama.cpp for clipart understanding
"""

import subprocess
import json
import base64
from pathlib import Path
from typing import Dict, List, Optional
import yaml

class ClipartVisionEngine:
    def __init__(self, model_path: str, llama_cli: str = "llama-cli"):
        self.model_path = model_path
        self.llama_cli = llama_cli
        self.system_prompt = """You are Seymour's clipart analyst. Analyze clipart images with the following framework:

1. DESCRIBE: What is literally depicted? Style, era, composition, colors.
2. CLASSIFY: Category from taxonomy (business_office, technology_computers, people_figures, animals_nature, symbols_icons, borders_frames, backgrounds_textures, transportation, household_objects, abstract_geometric, holiday_seasonal, 90s_aesthetic_markers)
3. MEME_POTENTIAL: How could this clipart function as a meme template? What concepts does it embody?
4. SEYMOUR_TAGS: 3-5 tags for Seymour's cross-reference system (e.g., bureaucracy, replication, irony, obsolescence, corporate_surrealism)
5. ALLEGORICAL_READING: If this clipart were a character in a memetic allegory, what would it represent?
6. PROVENANCE_CLUES: Visual indicators of source (Corel, ClickArt, WordPerfect, generic 90s CD-ROM style)

Output as structured JSON."""
    
    def analyze(self, image_path: str) -> Dict:
        """Analyze a single clipart image"""
        # Convert image to base64 for llama.cpp vision
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        
        prompt = f"{self.system_prompt}\n\nAnalyze this clipart image:"
        
        cmd = [
            self.llama_cli,
            "-m", self.model_path,
            "-p", prompt,
            "--image", image_path,
            "--temp", "0.3",
            "-n", "512",
            "-cnv", "-1"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        try:
            return json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            return {"raw_output": result.stdout, "error": "parse_failed"}
    
    def batch_analyze(self, image_dir: str, output_file: str) -> List[Dict]:
        """Process all images in a directory"""
        results = []
        for img_path in Path(image_dir).rglob("*"):
            if img_path.suffix.lower() in [".png", ".jpg", ".jpeg", ".bmp", ".gif", ".wmf"]:
                print(f"Analyzing {img_path.name}...")
                analysis = self.analyze(str(img_path))
                analysis["filename"] = img_path.name
                analysis["path"] = str(img_path)
                results.append(analysis)
        
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        return results

def extract_iso(iso_path: str, output_dir: str) -> List[str]:
    """Extract ISO and convert WMF/EMF to PNG"""
    import subprocess
    extracted = []
    
    # Mount/extract ISO (using 7z or mount)
    subprocess.run(["7z", "x", iso_path, f"-o{output_dir}"], check=False)
    
    # Find and convert WMF/EMF files
    for wmf in Path(output_dir).rglob("*.[wmf][emf]"):
        png_path = wmf.with_suffix(".png")
        subprocess.run(["convert", str(wmf), str(png_path)], check=False)
        if png_path.exists():
            extracted.append(str(png_path))
    
    # Also copy existing PNG/JPG/BMP
    for img in Path(output_dir).rglob("*"):
        if img.suffix.lower() in [".png", ".jpg", ".jpeg", ".bmp", ".gif"]:
            extracted.append(str(img))
    
    return extracted

if __name__ == "__main__":
    engine = ClipartVisionEngine("models/gemma-4-12B-it-qat-UD-Q4_K_XL.gguf")
    print("Seymour Vision Engine ready")
