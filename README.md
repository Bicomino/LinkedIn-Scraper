# LinkedIn Profile Scraper

A lightweight Python tool that uses Selenium and EdgeDriver to scrape public LinkedIn profiles and export all data in structured JSON.

---

## 🚀 Features

- Full-profile extraction:  
  - General info (name, location, “About”)
  - Contact info (LinkedIn URL, email, phone, birthday)
  - Work experience (title, company, dates, location, description)
  - Education (institution, degree/title, dates)
  - Certifications & licenses (name, issuer, issue/expiry dates, credential URL)
  - Skills
  - Languages (name & proficiency)
- Persistent session: keeps you logged in via an Edge user data directory.
- Automatic scrolling: loads dynamic content before extraction.
- Intelligent file naming: generates JSON filename from the profile URL.
- Configurable timeouts & driver path via `config.ini`.

---

## 📋 Requirements

- Python 3.7 or higher  
- Microsoft Edge browser  
- msedgedriver matching your Edge version  
- A LinkedIn account (optional if you have a valid session in `edge_profile`)

---

## 🛠️ Installation

1. Clone the repository  
   ```bash
   git clone https://github.com/Bicomino/LinkedIn-Scraper.git
   cd LinkedIn-Scraper
   ```

2. Install dependencies  
   ```bash
   pip install -r requirements.txt
   ```
   _`requirements.txt` should contain at least:_  
   ```
   selenium>=4.0.0
   ```

3. Download EdgeDriver  
   - Download from  
     https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/  
   - Unzip and place `msedgedriver.exe` somewhere on your system.

4. Create or directly edit `config.ini` file (see below).

---

## ⚙️ Configuration

Modify the file named `config.ini` that should be **next to** `linkedin_scraper.py` with your desired configuration:

```ini
[credentials]
# Your LinkedIn login (optional if you already have an Edge profile)
email             = youremail@example.com
password          = yourpassword

[timeouts]
# Seconds to wait after loading each page
page_load_sleep   = 6.0
# Seconds to wait between scroll actions
scroll_wait       = 1.5
# Max consecutive scrolls with no new content before stopping
max_scroll_attempts = 10

[driver]
# Full path to your msedgedriver executable
msedgedriver_path = C:/path/to/msedgedriver.exe
```

- If you omit `email`/`password`, the scraper will rely on an existing session in the `edge_profile` folder.
- The script will create an `edge_profile` directory in the working folder to store your browser profile and cookies.

---

## 💻 Usage

```bash
python linkedin_scraper.py https://www.linkedin.com/in/username-ABC123XYZ/
```

- Replace the URL with the target profile’s public URL.
- The scraper will:
  1. Launch Edge with your profile.
  2. Log in (if credentials are provided).
  3. Scroll and extract every section.
  4. Save the results as `username.json` (underscores replace dashes).

---

## 📁 Output

The JSON file contains:

```json
{
  "datos generales": [
    {
      "nombreContacto": "...",
      "ubicacionContacto": "...",
      "acerca_deContacto": "..."
    }
  ],
  "información de contacto": {
    "linkedinContacto": "...",
    "teléfonoContacto": "...",
    "emailContacto": "...",
    "cumpleañosContacto": "..."
  },
  "experiencias": [
    {
      "cargoExperiencia": "...",
      "empresaExperiencia": "...",
      "duracionExperiencia": "...",
      "ubicacionExperiencia": "...",
      "descripcionExperiencia": "..."
    }
  ],
  "educacion": [ /* … */ ],
  "licencias y certificaciones": [ /* … */ ],
  "aptitudes": [ /* … */ ],
  "idiomas": [ /* … */ ]
}
```

---

## 🐛 Troubleshooting

- **`configparser.NoSectionError`**  
  Make sure `config.ini` lives next to `linkedin_scraper.py` and has the `[credentials]`, `[timeouts]` and `[driver]` sections.
- **EdgeDriver not found**  
  Verify `msedgedriver_path` in `config.ini` points to the correct `msedgedriver.exe`.
- **Elements not found / stale selectors**  
  LinkedIn’s HTML changes often. Update the CSS/XPath selectors in the script accordingly.
- **Session expired / login loop**  
  Delete the `edge_profile` folder to force a fresh login.

---

## 🤝 Contributing

1. Fork the repo  
2. Create a branch:  
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. Commit your changes  
4. Push to your branch  
5. Open a Pull Request

---

## 📝 License

This project is published under the general GitHub license.

---

## 📞 Contact

Angel Truque Contreras  
- LinkedIn: https://www.linkedin.com/in/angel-truque-contreras-37bb44342/  
- Email: angel.trcn@gmail.com / angel.truquecontreras@gmail.com  
- GitHub: https://github.com/Bicomino/LinkedIn-Scraper

---
