from flask import Flask, request, jsonify, render_template
import umap_new_data

app = Flask(__name__)

@app.route('/')
def home():
   return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    
    new_json_data = umap_new_data.process_uploaded_data(file)
    
    print("Uploading...")
    print(new_json_data)

    return jsonify(new_json_data)

if __name__ == '__main__':
    app.run(debug=True)