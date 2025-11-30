// static/js/main.js

document.addEventListener("DOMContentLoaded", function () {
  /* ==============================
     STAT COUNTER ANIMATION
     ============================== */
  function animateCounter(element, target, duration = 1000) {
    let current = 0;
    const increment = target / (duration / 8.33); // 120fps
    const timer = setInterval(() => {
      current += increment;
      if (current >= target) {
        element.textContent = target;
        clearInterval(timer);
      } else {
        element.textContent = Math.floor(current);
      }
    }, 8.33);
  }

  // Animate all stat values
  const statValues = document.querySelectorAll(".stat-value");
  statValues.forEach((element) => {
    const value = parseInt(element.textContent);
    if (!isNaN(value)) {
      animateCounter(element, value, 1500);
    }
  });

  /* ==============================
     ALL UPCOMING EVENTS SLIDER
     ============================== */
  const slider = document.getElementById("all-events-row");
  const prevBtn = document.getElementById("all-events-prev");
  const nextBtn = document.getElementById("all-events-next");

  if (slider && prevBtn && nextBtn) {
    const scrollAmount = 320; // roughly one card width

    prevBtn.addEventListener("click", function () {
      slider.scrollBy({ left: -scrollAmount, behavior: "smooth" });
    });

    nextBtn.addEventListener("click", function () {
      slider.scrollBy({ left: scrollAmount, behavior: "smooth" });
    });
  }

  /* ==============================
     EVENT FORM – QUILL DESCRIPTION
     ============================== */
  const quillContainer = document.getElementById("quill-editor");
  const descHidden = document.getElementById("description-hidden");
  const eventForm = document.getElementById("event-form");

  // Only run this on the event form page AND if Quill is loaded
  if (quillContainer && descHidden && eventForm && window.Quill) {
    const quill = new Quill("#quill-editor", {
      theme: "snow",
      placeholder: "Add event details, agenda, notes, etc...",
      modules: {
        toolbar: [
          ["bold", "italic", "underline"],
          [{ list: "ordered" }, { list: "bullet" }],
          [{ header: [2, 3, false] }],
          ["link"],
          ["clean"],
        ],
      },
    });

    // If the hidden field already has HTML (edit mode), load it into Quill
    if (descHidden.value) {
      quill.clipboard.dangerouslyPasteHTML(descHidden.value);
    }

    // On submit, copy Quill HTML into hidden textarea so WTForms/Flask receive it
    eventForm.addEventListener("submit", function () {
      descHidden.value = quill.root.innerHTML;
    });
  }

  /* ==============================
     DATE INPUT FORMAT HELPER
     ============================== */
  // Parse shorthand formats like "120125" (MMDDYY) and convert to proper format
  const startTimeInput = document.querySelector('input[name="start_time"]');
  const endTimeInput = document.querySelector('input[name="end_time"]');

  function formatTimeString(timeStr) {
    // Parse various time formats and return "HH:MM AM/PM"
    const timeRegex = /(\d{1,2})(?::(\d{2}))?\s*(am|pm)?/i;
    const match = timeStr.match(timeRegex);
    
    if (!match) return null;
    
    let hour = parseInt(match[1]);
    const minute = match[2] ? parseInt(match[2]) : 0;
    const meridiem = match[3] ? match[3].toUpperCase() : "PM";
    
    // Validate hour
    if (hour < 1 || hour > 12) return null;
    
    return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')} ${meridiem}`;
  }

  function formatDateInput(input) {
    if (!input) return;

    input.addEventListener("blur", function () {
      const value = this.value.trim();
      
      // Check if it looks like shorthand (6 digits for MMDDYY only)
      if (/^\d{6}$/.test(value)) {
        const mm = value.substring(0, 2);
        const dd = value.substring(2, 4);
        const yy = value.substring(4, 6);
        const fullYear = parseInt(yy) > 50 ? "19" + yy : "20" + yy;
        
        // Default time to 12:00 PM if not provided
        this.value = mm + "-" + dd + "-" + fullYear + " 12:00 PM";
      }
      // Check if input has date and time separated by space
      else if (value.includes(" ")) {
        const parts = value.split(" ");
        if (parts.length >= 2) {
          const dateStr = parts[0];
          const timeStr = parts.slice(1).join(" ");
          const formattedTime = formatTimeString(timeStr);
          
          if (formattedTime && /^\d{1,2}-\d{1,2}-\d{4}$/.test(dateStr)) {
            this.value = dateStr + " " + formattedTime;
          }
        }
      }
      // Check if just a time was entered (try to format it)
      else {
        const formattedTime = formatTimeString(value);
        if (formattedTime) {
          // If only time provided, use today's date
          const today = new Date();
          const mm = String(today.getMonth() + 1).padStart(2, '0');
          const dd = String(today.getDate()).padStart(2, '0');
          const yyyy = today.getFullYear();
          this.value = `${mm}-${dd}-${yyyy} ${formattedTime}`;
        }
      }
    });
  }

  formatDateInput(startTimeInput);
  formatDateInput(endTimeInput);

  /* ==============================
     NAVBAR UNDERLINE ANIMATION
     ============================== */
  document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
    link.addEventListener('click', function(e) {
      // Remove active class from all links
      document.querySelectorAll('.navbar-nav .nav-link').forEach(l => {
        l.classList.remove('active');
      });
      // Add active class to clicked link
      this.classList.add('active');
    });
  });

  /* ==============================
     EVENTS PAGE SEARCH & FUZZY MATCH
     ============================== */
  // Fuzzy matching function to allow imperfect spelling
  function fuzzyMatch(str, pattern) {
    let patternIdx = 0;
    let strIdx = 0;
    let score = 0;
    
    while (patternIdx < pattern.length && strIdx < str.length) {
      if (pattern[patternIdx] === str[strIdx]) {
        score++;
        patternIdx++;
      }
      strIdx++;
    }
    
    return patternIdx === pattern.length ? score : 0;
  }

  const eventSearch = document.getElementById('eventSearch');
  if (eventSearch) {
    const suggestionsDiv = document.getElementById('searchSuggestions');
    const suggestionsList = document.getElementById('suggestionsList');
    let selectedIndex = -1;

    // Extract all event titles with club names from the page
    const eventTitles = [];
    document.querySelectorAll('.list-group-item, .col').forEach(el => {
      const titleLink = el.querySelector('h6 a, .card-title a');
      
      if (titleLink) {
        const title = titleLink.textContent.trim();
        let club = '';
        
        if (el.querySelector('h6 a')) {
          const clubText = el.querySelector('p.text-muted');
          if (clubText) {
            const parts = clubText.textContent.split('•');
            club = parts.length > 2 ? parts[2].trim() : '';
          }
        } else if (el.querySelector('.card-title a')) {
          const clubSubtitle = el.querySelector('.card-subtitle');
          if (clubSubtitle) {
            club = clubSubtitle.textContent.trim();
          }
        }
        
        if (title) {
          eventTitles.push({ title, club });
        }
      }
    });

    function renderSuggestions(matches, visibleCount) {
      selectedIndex = -1;
      if (matches.length > 0) {
        suggestionsList.innerHTML = matches.map((item, index) => `
          <a href="#" class="list-group-item list-group-item-action px-3 py-3 suggestion-item" data-index="${index}" style="font-size: 0.95rem; border: none; border-bottom: 1px solid #f0f0f0;" onclick="event.preventDefault(); document.getElementById('eventSearch').value = '${item.title.replace(/'/g, "\\'")}'; document.getElementById('eventSearch').dispatchEvent(new Event('input'));">
            <strong>${item.title}</strong>
            ${item.club ? `<div style="font-size: 0.85rem; color: #6c757d; margin-top: 0.25rem;">${item.club}</div>` : ''}
          </a>
        `).join('');
        suggestionsDiv.style.display = 'block';
      } else if (visibleCount === 0) {
        suggestionsList.innerHTML = '<div class="px-3 py-3 text-muted" style="font-size: 0.9rem;">No matching events found</div>';
        suggestionsDiv.style.display = 'block';
      }
    }

    function updateSelectedItem() {
      const items = document.querySelectorAll('.suggestion-item');
      items.forEach((item, index) => {
        if (index === selectedIndex) {
          item.classList.add('active');
          item.scrollIntoView({ block: 'nearest' });
        } else {
          item.classList.remove('active');
        }
      });
    }

    eventSearch.addEventListener('input', function() {
      const query = this.value.trim().toLowerCase();
      const allEventElements = document.querySelectorAll('.list-group-item, .col');
      
      if (query.length === 0) {
        allEventElements.forEach(el => {
          el.style.display = '';
        });
        suggestionsDiv.style.display = 'none';
        suggestionsList.innerHTML = '';
        return;
      }

      let visibleCount = 0;
      allEventElements.forEach(el => {
        const titleLink = el.querySelector('h6 a, .card-title a');
        const descriptionText = el.textContent.toLowerCase();
        
        if (titleLink) {
          const titleText = titleLink.textContent.trim().toLowerCase();
          const titleMatch = fuzzyMatch(titleText, query) > 0;
          const descriptionMatch = descriptionText.includes(query);
          
          if (titleMatch || descriptionMatch) {
            el.style.display = '';
            visibleCount++;
          } else {
            el.style.display = 'none';
          }
        } else {
          el.style.display = 'none';
        }
      });

      const matches = eventTitles
        .map(item => ({ ...item, score: fuzzyMatch(item.title.toLowerCase(), query) }))
        .filter(item => item.score > 0)
        .sort((a, b) => b.score - a.score)
        .slice(0, 5);

      renderSuggestions(matches, visibleCount);
    });

    eventSearch.addEventListener('keydown', function(e) {
      const items = document.querySelectorAll('.suggestion-item');
      
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (selectedIndex < items.length - 1) {
          selectedIndex++;
          updateSelectedItem();
        }
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (selectedIndex > 0) {
          selectedIndex--;
          updateSelectedItem();
        }
      } else if (e.key === 'Enter' && selectedIndex >= 0) {
        e.preventDefault();
        items[selectedIndex].click();
      }
    });

    document.addEventListener('click', function(e) {
      if (!e.target.closest('.col-md-6')) {
        suggestionsDiv.style.display = 'none';
      }
    });
  }

  /* ==============================
     CLUBS PAGE SEARCH & FUZZY MATCH
     ============================== */
  const clubSearch = document.getElementById('clubSearch');
  if (clubSearch) {
    const suggestionsDiv = document.getElementById('searchSuggestions');
    const suggestionsList = document.getElementById('suggestionsList');
    let selectedIndex = -1;

    const clubNames = [];
    document.querySelectorAll('.card-title a').forEach(link => {
      const name = link.textContent.trim();
      if (name && !clubNames.find(c => c.name === name)) {
        clubNames.push({ name });
      }
    });

    function renderSuggestions(matches, visibleCount) {
      selectedIndex = -1;
      if (matches.length > 0) {
        suggestionsList.innerHTML = matches.map((item, index) => `
          <a href="#" class="list-group-item list-group-item-action px-3 py-3 suggestion-item" data-index="${index}" style="font-size: 0.95rem; border: none; border-bottom: 1px solid #f0f0f0;" onclick="event.preventDefault(); document.getElementById('clubSearch').value = '${item.name.replace(/'/g, "\\'")}'; document.getElementById('clubSearch').dispatchEvent(new Event('input'));">
            <strong>${item.name}</strong>
          </a>
        `).join('');
        suggestionsDiv.style.display = 'block';
      } else if (visibleCount === 0) {
        suggestionsList.innerHTML = '<div class="px-3 py-3 text-muted" style="font-size: 0.9rem;">No matching clubs found</div>';
        suggestionsDiv.style.display = 'block';
      }
    }

    function updateSelectedItem() {
      const items = document.querySelectorAll('.suggestion-item');
      items.forEach((item, index) => {
        if (index === selectedIndex) {
          item.classList.add('active');
          item.scrollIntoView({ block: 'nearest' });
        } else {
          item.classList.remove('active');
        }
      });
    }

    clubSearch.addEventListener('input', function() {
      const query = this.value.trim().toLowerCase();
      const allClubElements = document.querySelectorAll('.col');
      
      if (query.length === 0) {
        allClubElements.forEach(el => {
          el.style.display = '';
        });
        suggestionsDiv.style.display = 'none';
        suggestionsList.innerHTML = '';
        return;
      }

      let visibleCount = 0;
      allClubElements.forEach(el => {
        const titleLink = el.querySelector('.card-title a');
        const descriptionText = el.textContent.toLowerCase();
        
        if (titleLink) {
          const nameText = titleLink.textContent.trim().toLowerCase();
          const nameMatch = fuzzyMatch(nameText, query) > 0;
          const descriptionMatch = descriptionText.includes(query);
          
          if (nameMatch || descriptionMatch) {
            el.style.display = '';
            visibleCount++;
          } else {
            el.style.display = 'none';
          }
        } else {
          el.style.display = 'none';
        }
      });

      const matches = clubNames
        .map(item => ({ ...item, score: fuzzyMatch(item.name.toLowerCase(), query) }))
        .filter(item => item.score > 0)
        .sort((a, b) => b.score - a.score)
        .slice(0, 5);

      renderSuggestions(matches, visibleCount);
    });

    clubSearch.addEventListener('keydown', function(e) {
      const items = document.querySelectorAll('.suggestion-item');
      
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (selectedIndex < items.length - 1) {
          selectedIndex++;
          updateSelectedItem();
        }
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (selectedIndex > 0) {
          selectedIndex--;
          updateSelectedItem();
        }
      } else if (e.key === 'Enter' && selectedIndex >= 0) {
        e.preventDefault();
        items[selectedIndex].click();
      }
    });

    document.addEventListener('click', function(e) {
      if (!e.target.closest('.col-md-6')) {
        suggestionsDiv.style.display = 'none';
      }
    });
  }

  /* ==============================
     HERO CAROUSEL
     ============================== */
  function initHeroCarousel() {
    const carousel = document.getElementById('heroCarousel');
    if (!carousel) return;

    const slides = carousel.querySelectorAll('.hero-carousel-slide');
    const dots = carousel.querySelectorAll('.carousel-dot');

    if (slides.length === 0) return;

    let currentSlide = 0;
    let autoPlayInterval;

    function showSlide(index) {
      // Validate index
      if (index >= slides.length) {
        currentSlide = 0;
      } else if (index < 0) {
        currentSlide = slides.length - 1;
      } else {
        currentSlide = index;
      }

      // Update slides
      slides.forEach(slide => slide.classList.remove('active'));
      slides[currentSlide].classList.add('active');

      // Update dots
      dots.forEach(dot => dot.classList.remove('active'));
      dots[currentSlide].classList.add('active');
    }

    function nextSlide() {
      showSlide(currentSlide + 1);
    }

    function previousSlide() {
      showSlide(currentSlide - 1);
    }

    function startAutoPlay() {
      autoPlayInterval = setInterval(nextSlide, 5000); // Change slide every 5 seconds
    }

    function stopAutoPlay() {
      clearInterval(autoPlayInterval);
    }

    // Dot click handlers
    dots.forEach((dot, index) => {
      dot.addEventListener('click', () => {
        stopAutoPlay();
        showSlide(index);
        startAutoPlay();
      });
    });

    // Pause on hover, resume on leave
    carousel.addEventListener('mouseenter', stopAutoPlay);
    carousel.addEventListener('mouseleave', startAutoPlay);

    // Start the carousel
    showSlide(0);
    startAutoPlay();
  }

  // Initialize carousel when DOM is ready
  initHeroCarousel();
});

