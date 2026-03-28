from flask import Flask, request, jsonify, send_file, render_template
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from groq import Groq
from docx import Document
import time

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/tara", methods=["POST"])
def tara():
    data = request.json
    api_key = data["api_key"]
    sorgu = data["sorgu"]

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    driver.get("https://duckduckgo.com")
    time.sleep(3)

    arama_kutusu = driver.find_element(By.NAME, "q")
    arama_kutusu.send_keys(sorgu)
    arama_kutusu.send_keys(Keys.RETURN)
    time.sleep(4)

    linkler = driver.find_elements(By.CSS_SELECTOR, "a[data-testid='result-title-a']")
    urls = []
    for link in linkler[:3]:
        url = link.get_attribute("href")
        if url:
            urls.append(url)

    tum_icerik = ""
    for url in urls:
        driver.get(url)
        time.sleep(3)
        paragraflar = driver.find_elements(By.TAG_NAME, "p")
        for p in paragraflar[:10]:
            if p.text:
                tum_icerik += p.text + "\n"

    driver.quit()

    groq_client = Groq(api_key=api_key)
    cevap = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": f"Asagidaki metni Turkce olarak ozetle:\n\n{tum_icerik[:3000]}"
            }
        ]
    )
    ozet = cevap.choices[0].message.content

    doc = Document()
    doc.add_heading(f"Rapor: {sorgu}", 0)
    doc.add_heading("Ozet", 1)
    doc.add_paragraph(ozet)
    doc.add_heading("Kaynaklar", 1)
    for url in urls:
        doc.add_paragraph(url)

    doc.save("rapor.docx")
    return jsonify({"durum": "tamam"})

@app.route("/indir")
def indir():
    return send_file("rapor.docx", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
