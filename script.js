/* ==========================================================================
   AI-POWERED RESUME ANALYZER - INTERACTIVE PREMIUM LOGIC
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {

  // Auto-dismiss Flash Alerts
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });

  // --- JOB DESCRIPTION SAMPLE AUTO-FILL LOGIC ---
  const sampleJdBtns = document.querySelectorAll('.sample-jd-btn');
  const jobTitleInput = document.getElementById('job_title');
  const jobDescInput = document.getElementById('job_description');

  const SAMPLE_JDS = {
    python: {
      title: "Senior Full-Stack Python Developer",
      desc: "We are seeking an experienced Full-Stack Python Developer to design and scale microservices. Requirements:\n• Strong proficiency in Python, Flask, or Django.\n• Frontend experience with React, JavaScript, HTML5, and CSS3.\n• Database expertise in PostgreSQL, MySQL, and Redis.\n• Containerization & DevOps using Docker, Kubernetes, and AWS.\n• CI/CD pipeline building, Git version control, REST API design, Agile methodology."
    },
    data: {
      title: "Data Engineer & Analytics Specialist",
      desc: "Looking for a Data Engineer to build data processing pipelines. Required Skills:\n• Python, R, SQL, PostgreSQL, MongoDB, Redis.\n• Knowledge of AWS, GCP, Docker, Linux shell scripting.\n• Familiarity with RESTful APIs, Git, GitHub, and Data Structures.\n• Experience with OOP principles and Agile Scrum development."
    },
    devops: {
      title: "DevOps & Cloud Systems Engineer",
      desc: "Hiring a DevOps Engineer to automate deployment and infrastructure. Tech Stack Required:\n• AWS, Azure, GCP, Linux, Docker, Kubernetes.\n• Version control using Git and GitHub.\n• Scripting in Python, Bash, or Go.\n• CI/CD automated deployment, Microservices architecture, REST API security."
    }
  };

  sampleJdBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const type = btn.getAttribute('data-sample');
      if (SAMPLE_JDS[type] && jobTitleInput && jobDescInput) {
        jobTitleInput.value = SAMPLE_JDS[type].title;
        jobDescInput.value = SAMPLE_JDS[type].desc;
        updateTextCounters();
      }
    });
  });

  // --- TEXTAREA WORD & CHARACTER COUNTER ---
  if (jobDescInput) {
    const wordCountSpan = document.getElementById('wordCountDisplay');
    const charCountSpan = document.getElementById('charCountDisplay');

    function updateTextCounters() {
      const text = jobDescInput.value.trim();
      const words = text ? text.split(/\s+/).length : 0;
      const chars = text.length;

      if (wordCountSpan) wordCountSpan.textContent = `${words} words`;
      if (charCountSpan) charCountSpan.textContent = `${chars} chars`;
    }

    jobDescInput.addEventListener('input', updateTextCounters);
    updateTextCounters();
  }

  // --- FILE UPLOAD DROPZONE LOGIC ---
  const dropzone = document.getElementById('uploadDropzone');
  const fileInput = document.getElementById('resume');
  const fileInfo = document.getElementById('fileInfo');
  const fileNameDisplay = document.getElementById('fileNameDisplay');
  const fileSizeDisplay = document.getElementById('fileSizeDisplay');
  const removeFileBtn = document.getElementById('removeFileBtn');

  if (dropzone && fileInput) {
    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('dragover');
      }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('dragover');
      }, false);
    });

    dropzone.addEventListener('drop', (e) => {
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        fileInput.files = files;
        handleFileSelection(files[0]);
      }
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        handleFileSelection(e.target.files[0]);
      }
    });

    if (removeFileBtn) {
      removeFileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.value = '';
        if (fileInfo) fileInfo.classList.add('d-none');
        const content = dropzone.querySelector('.dropzone-content');
        if (content) content.classList.remove('d-none');
      });
    }
  }

  function handleFileSelection(file) {
    if (!file) return;

    if (file.type !== 'application/pdf' && !file.name.endsWith('.pdf')) {
      alert('Please upload a valid PDF document (.pdf).');
      fileInput.value = '';
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      alert('File size exceeds the maximum limit of 5 MB.');
      fileInput.value = '';
      return;
    }

    if (fileNameDisplay && fileSizeDisplay && fileInfo) {
      fileNameDisplay.textContent = file.name;
      fileSizeDisplay.textContent = (file.size / (1024 * 1024)).toFixed(2) + ' MB';
      fileInfo.classList.remove('d-none');
      const content = dropzone.querySelector('.dropzone-content');
      if (content) content.classList.add('d-none');
    }
  }

  // --- MULTI-STEP LOADING SPINNER ANIMATION ---
  const uploadForm = document.getElementById('resumeUploadForm');
  const loadingOverlay = document.getElementById('loadingOverlay');

  if (uploadForm && loadingOverlay) {
    uploadForm.addEventListener('submit', () => {
      if (uploadForm.checkValidity()) {
        loadingOverlay.classList.add('active');

        // Animate loading steps
        const step1 = document.getElementById('step1');
        const step2 = document.getElementById('step2');
        const step3 = document.getElementById('step3');

        setTimeout(() => {
          if (step1) { step1.classList.remove('active'); step1.classList.add('text-success'); }
          if (step2) { step2.classList.add('active'); }
        }, 1200);

        setTimeout(() => {
          if (step2) { step2.classList.remove('active'); step2.classList.add('text-success'); }
          if (step3) { step3.classList.add('active'); }
        }, 2400);
      }
    });
  }

  // --- HISTORY SEARCH & FILTER LOGIC ---
  const historySearchInput = document.getElementById('historySearchInput');
  const historyRows = document.querySelectorAll('.history-table-row');
  const filterBtns = document.querySelectorAll('.filter-btn');

  if (historyRows.length > 0) {
    let currentFilter = 'all';

    function filterTable() {
      const searchTerm = historySearchInput ? historySearchInput.value.toLowerCase().trim() : '';

      historyRows.forEach(row => {
        const title = row.getAttribute('data-title') || '';
        const score = parseFloat(row.getAttribute('data-score') || '0');
        const matched = row.getAttribute('data-skills') || '';

        const matchesSearch = title.includes(searchTerm) || matched.includes(searchTerm);

        let matchesFilter = true;
        if (currentFilter === 'high') matchesFilter = score >= 80;
        else if (currentFilter === 'medium') matchesFilter = score >= 50 && score < 80;
        else if (currentFilter === 'low') matchesFilter = score < 50;

        if (matchesSearch && matchesFilter) {
          row.style.display = '';
        } else {
          row.style.display = 'none';
        }
      });
    }

    if (historySearchInput) {
      historySearchInput.addEventListener('input', filterTable);
    }

    filterBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        filterBtns.forEach(b => {
          b.classList.remove('active', 'btn-primary-custom');
          b.classList.add('btn-outline-secondary');
        });

        btn.classList.remove('btn-outline-secondary');
        btn.classList.add('active', 'btn-primary-custom');

        currentFilter = btn.getAttribute('data-filter');
        filterTable();
      });
    });
  }

});

// --- CHART INITIALIZATION HELPERS ---
function initAnalysisCharts(matchScore, matchedCount, missingCount) {
  const gaugeCtx = document.getElementById('scoreGaugeChart');
  const comparisonCtx = document.getElementById('comparisonBarChart');

  if (gaugeCtx) {
    const remainingScore = Math.max(0, 100 - matchScore);

    let primaryColor = '#10b981'; // Green
    if (matchScore < 50) primaryColor = '#f43f5e'; // Red
    else if (matchScore < 80) primaryColor = '#f59e0b'; // Yellow

    new Chart(gaugeCtx, {
      type: 'doughnut',
      data: {
        labels: ['Match Score', 'Skill Gap'],
        datasets: [{
          data: [matchScore, remainingScore],
          backgroundColor: [primaryColor, 'rgba(255, 255, 255, 0.05)'],
          borderWidth: 0,
          hoverOffset: 6
        }]
      },
      options: {
        cutout: '82%',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function(context) {
                return ` ${context.label}: ${context.raw}%`;
              }
            }
          }
        }
      }
    });
  }

  if (comparisonCtx) {
    new Chart(comparisonCtx, {
      type: 'bar',
      data: {
        labels: ['Matched Skills', 'Missing Skills'],
        datasets: [{
          label: 'Skills Count',
          data: [matchedCount, missingCount],
          backgroundColor: [
            'rgba(16, 185, 129, 0.8)',
            'rgba(244, 63, 94, 0.8)'
          ],
          borderColor: [
            '#10b981',
            '#f43f5e'
          ],
          borderWidth: 2,
          borderRadius: 10
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: '#94a3b8', font: { family: 'Plus Jakarta Sans', weight: '600' } }
          },
          y: {
            beginAtZero: true,
            ticks: { stepSize: 1, color: '#94a3b8', font: { family: 'Plus Jakarta Sans' } },
            grid: { color: 'rgba(255, 255, 255, 0.05)' }
          }
        }
      }
    });
  }
}
