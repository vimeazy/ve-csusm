let currentDate = new Date();

function renderCalendar() {
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();
  
  const monthDisplay = document.getElementById('monthDisplay');
  monthDisplay.textContent = currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const daysInMonth = lastDay.getDate();
  const startingDayOfWeek = firstDay.getDay();
  
  const calendarBody = document.getElementById('calendarBody');
  calendarBody.innerHTML = '';
  
  let date = 1;
  let nextDate = 1;
  
  for (let i = 0; i < 6; i++) {
    const row = document.createElement('tr');
    
    for (let j = 0; j < 7; j++) {
      const cell = document.createElement('td');
      cell.className = 'calendar-day';
      
      if (i === 0 && j < startingDayOfWeek) {
        // Previous month days
        const prevMonthLastDay = new Date(year, month, 0).getDate();
        cell.className += ' other-month';
        cell.innerHTML = (prevMonthLastDay - startingDayOfWeek + j + 1);
      } else if (date > daysInMonth) {
        // Next month days
        cell.className += ' other-month';
        cell.innerHTML = nextDate;
        nextDate++;
      } else {
        // Current month days
        const dateStr = year + '-' + String(month + 1).padStart(2, '0') + '-' + String(date).padStart(2, '0');
        const today = new Date();
        if (year === today.getFullYear() && month === today.getMonth() && date === today.getDate()) {
          cell.className += ' today';
        }
        
        cell.innerHTML = '<div class="day-number">' + date + '</div>';
        
        // Add event preview
        if (eventsByDate[dateStr]) {
          const events = eventsByDate[dateStr];
          let eventPreviewHtml = '<div class="day-events">';
          
          events.forEach((event, idx) => {
            if (idx < 2) { // Show max 2 event previews
              eventPreviewHtml += '<div class="event-preview ' + event.type + '" title="' + event.title + ' at ' + event.time + '">';
              eventPreviewHtml += '<span class="event-dot ' + event.type + '"></span>';
              eventPreviewHtml += '<span class="event-title-short">' + event.title.substring(0, 20) + (event.title.length > 20 ? '...' : '') + '</span>';
              eventPreviewHtml += '</div>';
            }
          });
          
          if (events.length > 2) {
            eventPreviewHtml += '<div class="event-more">+' + (events.length - 2) + ' more</div>';
          }
          
          eventPreviewHtml += '</div>';
          cell.innerHTML += eventPreviewHtml;
        }
        
        date++;
      }
      
      row.appendChild(cell);
    }
    
    if (date > daysInMonth) {
      calendarBody.appendChild(row);
      break;
    }
    
    calendarBody.appendChild(row);
  }
}

function previousMonth() {
  currentDate.setMonth(currentDate.getMonth() - 1);
  renderCalendar();
}

function nextMonth() {
  currentDate.setMonth(currentDate.getMonth() + 1);
  renderCalendar();
}

// Initialize calendar when page loads
document.addEventListener('DOMContentLoaded', renderCalendar);
