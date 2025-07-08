from flask import Flask, render_template, request, redirect, url_for
from pathlib import Path
import shutil, json
from your_llm_code import extract_one
from langchain_groq import ChatGroq

app = Flask(__name__)

UPLOAD_ROOT = Path("static/images")
JSON_ROOT = Path("json_outputs")
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
JSON_ROOT.mkdir(parents=True, exist_ok=True)

# Initialize LLM
llm = ChatGroq(
    model="meta-llama/Llama-4-Maverick-17B-128E-Instruct",
    groq_api_key=""  # Replace with your real key
)

# 1. Home Page – Input main folder and show subfolders
@app.route("/", methods=["GET", "POST"])
def index():
    subfolders = []
    if request.method == "POST":
        main_dir = request.form.get("main_folder_path").strip()
        main_path = Path(main_dir)

        if not main_path.exists() or not main_path.is_dir():
            return f"❌ Folder not found: {main_path}", 400

        app.config['MAIN_FOLDER'] = str(main_path)
        subfolders = [f.name for f in main_path.iterdir() if f.is_dir()]

    return render_template("index.html", subfolders=subfolders)

# 2. Show all images inside selected subfolder
@app.route("/folder/<subfolder>")
def folder_view(subfolder):
    main_path = Path(app.config.get("MAIN_FOLDER", ""))
    folder_path = main_path / subfolder

    if not folder_path.exists():
        return f"❌ Folder not found: {folder_path}", 404

    images = [f.name for f in folder_path.iterdir() if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"]]

    return render_template("folder.html", subfolder=subfolder, images=images)

# 3. View individual image + extracted JSON
@app.route("/view/<subfolder>/<filename>")
def view_image(subfolder, filename):
    main_path = Path(app.config.get("MAIN_FOLDER", ""))
    src_img_path = main_path / subfolder / filename

    # Copy to static/images/subfolder/
    static_folder = UPLOAD_ROOT / subfolder
    static_folder.mkdir(parents=True, exist_ok=True)
    static_img_path = static_folder / filename
    if not static_img_path.exists():
        shutil.copy(src_img_path, static_img_path)

    # Extract JSON and save
    json_folder = JSON_ROOT / subfolder
    json_folder.mkdir(parents=True, exist_ok=True)
    json_path = json_folder / f"{Path(filename).stem}.json"

    if not json_path.exists():
        try:
            json_data = extract_one(static_img_path, llm)
            json_data["source_file"] = filename
            with open(json_path, "w") as f:
                json.dump(json_data, f, indent=2)
        except Exception as e:
            return f"❌ Error extracting JSON: {e}", 500
    else:
        with open(json_path, "r") as f:
            json_data = json.load(f)

    return render_template("view.html", image_file=f"images/{subfolder}/{filename}", json_data=json_data)

if __name__ == "__main__":
    app.run(debug=True)

