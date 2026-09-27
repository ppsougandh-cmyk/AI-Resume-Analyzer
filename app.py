import os
import re
import json
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from pypdf import PdfReader
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'

# Skill Taxonomy Dictionary
SKILL_TAXONOMY = {
    'Languages': ['Python', 'Java', 'C++', 'C#', 'C', 'PHP', 'JavaScript', 'TypeScript', 'Ruby', 'Go', 'Swift', 'Kotlin', 'SQL', 'HTML', 'CSS', 'R'],
    'Frameworks': ['Flask', 'Django', 'React', 'Angular', 'Vue', 'Laravel', 'Spring Boot', 'Spring', 'Express', 'Node.js', 'Bootstrap', 'Tailwind', 'FastAPI'],
    'Databases': ['MySQL', 'SQLite', 'PostgreSQL', 'MongoDB', 'Redis', 'Oracle', 'DynamoDB'],
    'Tools & Platforms': ['Git', 'GitHub', 'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'Postman', 'VS Code', 'Jira', 'Linux'],
    'Concepts': ['REST API', 'RESTful', 'CI/CD', 'Agile', 'Scrum', 'Microservices', 'OOP', 'Data Structures']
}


# --- DATABASE MODELS ---

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    analyses = db.relationship('Analysis', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_title = db.Column(db.String(150), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    resume_filename = db.Column(db.String(255), nullable=False)
    resume_text = db.Column(db.Text, nullable=True)
    match_score = db.Column(db.Float, nullable=False)
    matched_skills = db.Column(db.Text, nullable=False)   # JSON string
    missing_skills = db.Column(db.Text, nullable=False)   # JSON string
    jd_skills = db.Column(db.Text, nullable=False)        # JSON string
    suggestions = db.Column(db.Text, nullable=False)      # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def matched_skills_list(self):
        try:
            return json.loads(self.matched_skills)
        except Exception:
            return []

    @property
    def missing_skills_list(self):
        try:
            return json.loads(self.missing_skills)
        except Exception:
            return []

    @property
    def jd_skills_list(self):
        try:
            return json.loads(self.jd_skills)
        except Exception:
            return []

    @property
    def suggestions_list(self):
        try:
            return json.loads(self.suggestions)
        except Exception:
            return []


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- HELPER & PROCESSING FUNCTIONS ---

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def extract_text_from_pdf(filepath):
    """Extract raw text from PDF using PyPDF."""
    text = ""
    try:
        reader = PdfReader(filepath)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text.strip()
    except Exception as e:
        app.logger.error(f"Error reading PDF file {filepath}: {e}")
        return ""


def extract_skills_from_text(text: str) -> dict:
    """Extract skills from raw text using Taxonomy dictionary & Regex."""
    if not text:
        return {'skills': [], 'categorized': {}}

    found_skills = set()
    categorized = {}

    for category, skills_list in SKILL_TAXONOMY.items():
        cat_found = []
        for skill in skills_list:
            escaped = re.escape(skill)
            if skill in ['C++', 'C#', 'CI/CD', 'R']:
                pattern = r'(?:^|[\s,./\(\)\:;\-])' + escaped + r'(?:$|[\s,./\(\)\:;\-])'
            elif ' ' in skill:
                parts = [re.escape(p) for p in skill.split()]
                pattern = r'\b' + r'\s+'.join(parts) + r'\b'
            else:
                pattern = r'\b' + escaped + r'\b'

            if re.search(pattern, text, re.IGNORECASE):
                found_skills.add(skill)
                cat_found.append(skill)

        if cat_found:
            categorized[category] = cat_found

    return {
        'skills': sorted(list(found_skills)),
        'categorized': categorized
    }


def generate_recommendations(match_score, matched_skills, missing_skills, jd_text, resume_text):
    """Generate contextual, actionable recommendations for resume improvement."""
    suggestions = []

    # Overall match score assessment
    if match_score >= 80:
        suggestions.append("🚀 Excellent Fit! Your resume strongly matches the required technical stack. Focus on quantifying key achievements (e.g., 'Improved database latency by 40%') and polishing project impacts.")
    elif match_score >= 50:
        suggestions.append("⚡ Good Alignment. You meet several core requirements. Emphasize relevant projects or add specific key responsibilities matching missing required competencies.")
    else:
        suggestions.append("📌 Low Match Score. Your resume is missing a significant number of required technical skills for this role. Consider updating your skills section and highlighting related coursework or hands-on projects.")

    missing_set = set(missing_skills)

    # Contextual missing skill recommendations
    if 'Git' in missing_set or 'GitHub' in missing_set:
        suggestions.append("🐙 Version Control: 'Git' / 'GitHub' is specified in the job description. Highlight version control practices or link your GitHub profile.")

    if 'REST API' in missing_set or 'RESTful' in missing_set:
        suggestions.append("🌐 API Integration: Explicitly mention experience building or consuming RESTful APIs.")

    if 'Docker' in missing_set or 'Kubernetes' in missing_set:
        suggestions.append("🐳 DevOps & Containers: Containerization skills (Docker/Kubernetes) are required for this role. Add relevant deployment experience if applicable.")

    if any(db in missing_set for db in ['SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'SQLite']):
        suggestions.append("🗄️ Database Management: The position requires database knowledge. Add specific DBMS projects or SQL query writing experience.")

    if any(lang in missing_set for lang in ['Python', 'Java', 'JavaScript', 'TypeScript', 'C++']):
        req_langs = [l for l in missing_skills if l in ['Python', 'Java', 'JavaScript', 'TypeScript', 'C++']]
        suggestions.append(f"💻 Key Programming Languages: Consider explicitly adding competency in: {', '.join(req_langs)}.")

    if missing_skills:
        top_missing = missing_skills[:6]
        suggestions.append(f"🎯 Essential Keywords to Target: Add these keywords to your resume: {', '.join(top_missing)}.")

    return suggestions


# --- ROUTE HANDLERS ---

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not name or not email or not password:
            flash('Please fill in all required fields.', 'danger')
            return render_template('register.html')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email address is already registered. Please login.', 'warning')
            return render_template('register.html')

        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash(f'Account created successfully! Welcome, {name}.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash(f'Welcome back, {user.name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    user_analyses = Analysis.query.filter_by(user_id=current_user.id).order_by(Analysis.created_at.desc()).all()
    total_count = len(user_analyses)
    avg_score = round(sum(a.match_score for a in user_analyses) / total_count, 1) if total_count > 0 else 0
    recent_analyses = user_analyses[:5]

    return render_template('dashboard.html',
                           total_count=total_count,
                           avg_score=avg_score,
                           recent_analyses=recent_analyses)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        job_title = request.form.get('job_title', '').strip()
        job_description = request.form.get('job_description', '').strip()

        if not job_title or not job_description:
            flash('Job Title and Job Description are required fields.', 'danger')
            return render_template('upload.html')

        if 'resume' not in request.files:
            flash('No resume PDF file uploaded.', 'danger')
            return render_template('upload.html')

        file = request.files['resume']

        if file.filename == '':
            flash('No selected file.', 'danger')
            return render_template('upload.html')

        if not allowed_file(file.filename):
            flash('Invalid file format. Please upload a PDF document (.pdf).', 'danger')
            return render_template('upload.html')

        # Ensure upload folder exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        saved_filename = f"{current_user.id}_{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
        file.save(filepath)

        # Extract text from PDF
        resume_text = extract_text_from_pdf(filepath)

        if not resume_text:
            flash('Could not extract text from the uploaded PDF. It may be scanned, image-based, or encrypted.', 'warning')

        # Skills extraction logic
        jd_skills_data = extract_skills_from_text(job_description)
        resume_skills_data = extract_skills_from_text(resume_text)

        jd_skills = jd_skills_data['skills']
        resume_skills = set(resume_skills_data['skills'])

        matched_skills = [s for s in jd_skills if s in resume_skills]
        missing_skills = [s for s in jd_skills if s not in resume_skills]

        # Calculate match percentage
        if jd_skills:
            match_score = round((len(matched_skills) / len(jd_skills)) * 100, 1)
        else:
            # Fallback if no taxonomy skills are explicitly found in JD
            match_score = 0.0
            flash('Note: No standard technical skills from our taxonomy were identified in the Job Description.', 'info')

        suggestions = generate_recommendations(match_score, matched_skills, missing_skills, job_description, resume_text)

        # Create database record
        analysis = Analysis(
            user_id=current_user.id,
            job_title=job_title,
            job_description=job_description,
            resume_filename=filename,
            resume_text=resume_text,
            match_score=match_score,
            matched_skills=json.dumps(matched_skills),
            missing_skills=json.dumps(missing_skills),
            jd_skills=json.dumps(jd_skills),
            suggestions=json.dumps(suggestions)
        )

        db.session.add(analysis)
        db.session.commit()

        # Clean up stored temporary PDF file if desired
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            app.logger.warning(f"Failed to delete temporary PDF file {filepath}: {e}")

        flash('Resume analysis completed successfully!', 'success')
        return redirect(url_for('analysis_detail', id=analysis.id))

    return render_template('upload.html')


@app.route('/analysis/<int:id>')
@login_required
def analysis_detail(id):
    analysis = Analysis.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    return render_template('analysis.html', analysis=analysis)


@app.route('/history')
@login_required
def history():
    analyses = Analysis.query.filter_by(user_id=current_user.id).order_by(Analysis.created_at.desc()).all()
    return render_template('history.html', analyses=analyses)


@app.route('/analysis/delete/<int:id>', methods=['POST'])
@login_required
def delete_analysis(id):
    analysis = Analysis.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(analysis)
    db.session.commit()
    flash('Analysis record deleted successfully.', 'success')
    return redirect(url_for('history'))


# --- INITIALIZE DATABASE & RUN SERVER ---

if __name__ == '__main__':
    with app.app_context():
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        db.create_all()
    app.run(debug=True, port=5000)
