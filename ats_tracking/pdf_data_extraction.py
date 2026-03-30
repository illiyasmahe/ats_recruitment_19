# full_resume_parser_function.py
import os
import re
import spacy
from pydparser import ResumeParser  # pip install pydparser, spacy
from pdfminer.high_level import extract_text
from dateutil.parser import parse
from datetime import datetime

# -------------------------
# Load spaCy model globally
# -------------------------
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
    nlp = spacy.load("en_core_web_sm")


def parse_resume(file_path: str, manual_input: str):
    """
    Parses a PDF resume and returns a dictionary with cleaned info.
    :param file_path: Path to the resume PDF
    :param manual_input: Manual input string containing candidate name or email
    :return: dict with keys: name, email, mobile, skills, education, experience, total_experience_years
    """
    if file_path.startswith("file://"):
        file_path = file_path[7:]

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Resume file not found: {file_path}")

    # -------------------------
    # 1️⃣ Parse resume with pydparser
    # -------------------------
    try:
        parser = ResumeParser(file_path)
        data = parser.get_extracted_data()
    except Exception as e:
        print("Error parsing resume:", e)
        data = {}

    def remove_emails_from_text(text):

        # remove normal emails
        text = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', ' ', text)

        # remove gmailcom style
        text = re.sub(
            r'\b[a-zA-Z]+(?:gmail|yahoo|hotmail|outlook|icloud)com\b',
            ' ',
            text,
            flags=re.I
        )

        return text

    # -------------------------
    # Clean email name
    # -------------------------
    def clean_email_name(email):

        if not email:
            return ""

        email = email.lower()

        # remove domain
        if "@" in email:
            email = email.split("@")[0]

        # remove numbers
        email = re.sub(r'\d+', '', email)

        # remove separators
        email = re.sub(r'[._\-]', '', email)

        # remove domains if stuck
        domains = [
            "gmailcom", "gmail",
            "yahoocom", "yahoo",
            "outlookcom", "outlook",
            "hotmailcom", "hotmail",
            "icloudcom", "icloud"
        ]

        for d in domains:
            email = email.replace(d, "")

        return email.strip()

    # -------------------------
    # Extract name from email
    # -------------------------
    def extract_name_from_email_match(pdf_text, email):

        name_part = clean_email_name(email)

        if len(name_part) < 3:
            return None

        words = pdf_text.split()

        # domains to exclude
        email_domains = ["gmail", "yahoo", "hotmail", "outlook", "icloud", "http", "www", "com", "net", "org", "linkedin"]

        clean_words = []
        for w in words:
            w_clean = re.sub(r'[^a-zA-Z]', '', w).lower()

            if len(w_clean) < 3:
                continue

            # skip email-like words
            if any(domain in w_clean for domain in email_domains):
                continue

            clean_words.append(w_clean)

        best_match = None
        best_score = 0

        # generate all substrings
        for i in range(len(name_part)):
            for j in range(i + 3, len(name_part) + 1):

                sub = name_part[i:j]

                for word in clean_words:

                    if sub in word:

                        score = len(sub)

                        if score > best_score:
                            best_score = score
                            best_match = word

        # -------------------------
        # 🔥 FULL NAME EXPANSION
        # -------------------------
        if best_match:

            stop_words = {
                "kerala", "kottayam", "india", "address","uae","country","state",
                "phone", "email", "resume", "cv", "profile", "summary"
            }

            original_words = pdf_text.split()

            for i, w in enumerate(original_words):

                w_clean = re.sub(r'[^a-zA-Z]', '', w).lower()

                if w_clean == best_match:

                    full_name = []

                    # 👈 previous word
                    if i > 0:
                        prev = re.sub(r'[^a-zA-Z]', '', original_words[i - 1])
                        prev_clean = prev.lower()

                        if prev_clean not in stop_words and prev.isalpha() and len(prev) > 2:
                            full_name.append(prev)

                    # current word
                    curr = re.sub(r'[^a-zA-Z]', '', original_words[i])
                    full_name.append(curr)

                    # 👉 next word
                    if i < len(original_words) - 1:
                        nxt = re.sub(r'[^a-zA-Z]', '', original_words[i + 1])
                        nxt_clean = nxt.lower()

                        if nxt_clean not in stop_words and nxt.isalpha() and len(nxt) > 2:
                            full_name.append(nxt)

                    return " ".join(full_name).title()

            return best_match.title()

        return None
    # -------------------------
    # 2️⃣ Extract name from PDF using seed
    # -------------------------
    def extract_name_from_pdf_line(file_path, seed_name):
        try:
            pdf_text = extract_text(file_path)
        except Exception:
            return None

        lines = pdf_text.splitlines()
        seed_lower = seed_name.lower()
        full_names = []

        for line in lines:
            if seed_lower not in line.lower():
                continue

            # Remove emails and URLs
            line_clean = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", " ", line)
            line_clean = re.sub(r"https?://\S+", " ", line_clean)
            # Remove numbers and special chars
            line_clean = re.sub(r"[\d<>\-\.]", " ", line_clean)
            line_clean = re.sub(r"\s+", " ", line_clean)

            words = line_clean.split()
            indices = [i for i, w in enumerate(words) if seed_lower in w.lower()]

            for idx in indices:
                # Left consecutive capitalized words
                left = idx
                while left > 0 and words[left - 1][0].isupper():
                    left -= 1
                # Right consecutive capitalized words
                right = idx + 1
                while right < len(words) and words[right][0].isupper():
                    right += 1
                full_name = " ".join(words[left:right])
                if full_name:  # skip empty
                    full_names.append(full_name)

        if full_names:
            return max(full_names, key=lambda x: len(x.split()))
        else:
            return None

    # -------------------------
    # 3️⃣ Extract education
    # -------------------------
    def get_education_section(pdf_text):

        text = re.sub(r'\s+', ' ', pdf_text)

        match = re.search(
            r'(education|academics|qualification)(.*?)(experience|project|skills|summary|$)',
            text,
            re.IGNORECASE
        )

        if match:
            return match.group(2)

        return text  # fallback

    def extract_education(pdf_text):

        text = get_education_section(pdf_text)  # ✅ important

        lines = text.split("  ")  # split better than lines

        education_list = []

        for line in lines:

            line_clean = re.sub(r'\s+', ' ', line)

            # 🎓 STRICT DEGREE MATCH (no generic "master")
            degree_match = re.search(
                r'(MSc|M\.Sc|BSc|B\.Sc|BCA|MCA|MBA|BTech|MTech)',
                line_clean,
                re.IGNORECASE
            )

            if not degree_match:
                continue

            degree = degree_match.group(0).replace('.', '').title()

            # 📅 Year (strict)
            year_match = re.search(r'(\d{4}\s*[-–]\s*\d{4})', line_clean)
            year = year_match.group(0) if year_match else None

            # 🏫 College
            college_match = re.search(
                r'([A-Z][A-Za-z\s]+College|University|Institute)[^,]*',
                line_clean
            )
            college = college_match.group(0).strip() if college_match else None

            education_list.append({
                "degree": degree,
                "year": year,
                "college": college
            })

        return education_list

    def clean_education_list(education_list):

        if not education_list:
            return []

        # 🎯 valid degrees only
        valid_degrees = {
            "msc", "mtech", "mca", "mba", "master",
            "bsc", "btech", "bca", "bachelor",
            "phd", "doctorate", "diploma"
        }

        # 🎯 normalization map
        degree_map = {
            "m.sc": "msc",
            "msc": "msc",
            "mtech": "mtech",
            "mca": "mca",
            "mba": "mba",
            "master": "master",

            "b.sc": "bsc",
            "bsc": "bsc",
            "btech": "btech",
            "bca": "bca",
            "bachelor": "bachelor",

            "phd": "phd",
            "doctorate": "doctorate",
            "diploma": "diploma"
        }

        cleaned = []
        seen = set()

        for edu in education_list:

            degree = (edu.get("degree") or "").lower().strip()
            year = (edu.get("year") or "").strip()
            college = (edu.get("college") or "").strip()

            # 🔥 normalize degree
            degree = degree.replace(".", "")
            degree = degree_map.get(degree, degree)

            # ❌ skip invalid degree
            if degree not in valid_degrees:
                continue

            # ❌ skip fake words like mbasd (extra safety)
            if not re.match(r'^[a-zA-Z]+$', degree):
                continue

            # ❌ remove useless entries (no year AND no college)
            if not year and not college:
                continue

            # 🎯 normalize year (extract proper range or single year)
            year_match = re.search(r'(\d{4}\s*[-–to]{1,3}\s*\d{4}|\d{4})', year)
            year = year_match.group(0) if year_match else None

            # 🎯 clean college text
            if college:
                college = re.sub(r'\s+', ' ', college)
                college = college.strip()

            # 🎯 final object
            clean_edu = {
                "degree": degree.upper() if len(degree) <= 4 else degree.title(),
                "year": year,
                "college": college or None
            }

            # 🔁 remove duplicates
            key = (clean_edu["degree"], clean_edu["year"], clean_edu["college"])

            if key not in seen:
                seen.add(key)
                cleaned.append(clean_edu)

        return cleaned

    def get_highest_education(education_list):

        # 🔥 CLEAN FIRST (your existing function)
        education_list = clean_education_list(education_list)

        if not education_list:
            return None

        # 🎯 UPDATED PRIORITY (added MBA + Master safely)
        priority = {
            "phd": 5,
            "doctorate": 5,

            "master": 4,
            "msc": 4,
            "mtech": 4,
            "mca": 4,
            "mba": 4,

            "bachelor": 3,
            "btech": 3,
            "bsc": 3,
            "bca": 3,

            "diploma": 2
        }

        best = None
        best_score = -1  # 🔥 important fix

        for edu in education_list:

            degree = (edu.get("degree") or "").lower()
            score = priority.get(degree, 0)

            # 🔥 safe year extraction
            def get_end_year(val):
                if not val:
                    return 0
                match = re.search(r'(\d{4})\s*$', val)
                return int(match.group(1)) if match else 0

            curr_year = get_end_year(edu.get("year"))
            best_year = get_end_year(best.get("year")) if best else 0

            # 🎯 selection logic
            if score > best_score:
                best_score = score
                best = edu

            elif score == best_score:
                # prefer latest year
                if curr_year > best_year:
                    best = edu

        return best

    # -------------------------
    # 4️⃣ Extract experience and total years
    # -------------------------
    import re
    from datetime import datetime

    import re
    from datetime import datetime

    def extract_experience(pdf_text):

        # -----------------------------
        # ✅ 1. DIRECT EXPERIENCE (BEST SOURCE)
        # -----------------------------
        exp_match = re.search(r'(\d+(\.\d+)?)\s*\+?\s*years', pdf_text, re.I)
        if exp_match:
            return [], float(exp_match.group(1))

        # -----------------------------
        # ❌ 2. STRICT EXPERIENCE SECTION ONLY
        # -----------------------------
        exp_section_match = re.search(
            r'(experience|work experience)(.*?)(education|skills|projects|certificates|$)',
            pdf_text,
            re.IGNORECASE | re.DOTALL
        )

        # 🚨 IMPORTANT: if no section → STOP
        if not exp_section_match:
            return [], 0.0  # 🔥 NO FALLBACK

        text = exp_section_match.group(2)
        lines = text.splitlines()

        date_ranges = []

        for line in lines:

            match = re.search(
                r'(\d{4}).{0,15}[-–to]{1,3}.{0,15}(\d{4}|present|currently)',
                line,
                re.I
            )

            if match:
                start_year = int(match.group(1))
                end_raw = match.group(2)

                if end_raw.lower() in ["present", "currently"]:
                    end_year = datetime.now().year
                else:
                    end_year = int(end_raw)

                if start_year <= end_year:
                    date_ranges.append((start_year, end_year))

        if not date_ranges:
            return [], 0.0

        min_year = min(start for start, end in date_ranges)
        max_year = max(end for start, end in date_ranges)

        total_years = max_year - min_year

        return [], round(total_years, 1)

    # -------------------------
    # 5️⃣ Prepare PDF text once
    # -------------------------
    pdf_text = extract_text(file_path)

    # -------------------------
    # 6️⃣ Extract seed name from manual input
    # -------------------------
    seed_match = re.match(r'"?([^"]+)"?', manual_input)
    seed_name = seed_match.group(1).strip() if seed_match else ""

    # Name
    name = extract_name_from_pdf_line(file_path, seed_name)
    if not name:
        name = extract_name_from_email_match(pdf_text, data.get("email"))
    if not name:
        parser_name = str(data.get("name", "")).strip()
        if parser_name and all(x.isalpha() or x.isspace() for x in parser_name):
            name = parser_name
        else:
            name = None

    # Email
    raw_text_email = " ".join([str(v) for v in data.values() if v])
    email_match = re.search(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", raw_text_email)
    email = email_match.group(0) if email_match else None

    mobile = extract_mobile_number(pdf_text)

    # fallback (if nothing found)
    if not mobile:
        mobile = data.get("mobile_number") or None

    linkedin = extract_linkedin_url(pdf_text)
    github_url = extract_github_url(pdf_text)

    # Skills
    skills = data.get("skills") or []

    # Education
    education = extract_education(pdf_text)
    highest_education = get_highest_education(education)

    # Experience
    experience, total_exp_years = extract_experience(pdf_text)

    # -------------------------
    # 7️⃣ Return as dictionary
    # -------------------------
    return {
        "name": name,
        "email": email,
        "mobile": mobile,
        "skills": skills,
        "education": education,
        "highest_education": highest_education,
        "experience": experience,
        "linkedin": linkedin,
        "github_url": github_url,
        "total_experience_years": total_exp_years,
        "pdf_text": pdf_text,
    }

def extract_mobile_number(pdf_text):

    # remove emails to avoid conflicts
    text = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', ' ', pdf_text)

    # normalize
    text = re.sub(r'\s+', ' ', text)

    # 🌍 global phone pattern
    pattern = r'(\+?\d[\d\-\s\(\)]{7,}\d)'

    matches = re.findall(pattern, text)

    cleaned_numbers = []

    for num in matches:
        # remove non-digits except +
        clean = re.sub(r'[^\d+]', '', num)

        # basic validation (length 10–15 digits)
        digits = re.sub(r'\D', '', clean)

        if 10 <= len(digits) <= 15:
            cleaned_numbers.append(clean)

    if not cleaned_numbers:
        return None

    # remove duplicates
    unique_numbers = list(set(cleaned_numbers))

    # ✅ prefer international format (+)
    for num in unique_numbers:
        if num.startswith('+'):
            return num

    # else return longest
    return max(unique_numbers, key=len)

def extract_linkedin_url(pdf_text):

    # ✅ keep spaces, just normalize
    text = re.sub(r'\s+', ' ', pdf_text)

    pattern = r'(https?://(?:www\.)?linkedin\.com/[^\s|]+|www\.linkedin\.com/[^\s|]+|linkedin\.com/[^\s|]+)'

    matches = re.findall(pattern, text, re.IGNORECASE)

    if not matches:
        return None

    cleaned = []

    for url in matches:
        url = url.strip()

        # ✂️ cut unwanted trailing junk (IMPORTANT)
        url = re.split(r'[A-Z]{2,}', url)[0]   # stops at SUMMARY, EDUCATION etc
        url = url.split('|')[0]                # remove pipe garbage

        # ensure proper format
        if not url.startswith("http"):
            url = "https://" + url

        cleaned.append(url)

    # remove duplicates
    unique_urls = list(set(cleaned))

    # prefer profile लिंक
    for url in unique_urls:
        if "/in/" in url:
            return url

    return unique_urls[0]

def extract_github_url(pdf_text):

    text = re.sub(r'\s+', ' ', pdf_text)

    pattern = r'(https?://(?:www\.)?github\.com/[^\s|]+|github\.com/[^\s|]+)'

    matches = re.findall(pattern, text, re.IGNORECASE)

    if not matches:
        return None

    url = matches[0].split('|')[0]

    if not url.startswith("http"):
        url = "https://" + url

    return url