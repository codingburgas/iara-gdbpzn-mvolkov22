(function(){
  var v1 = document.getElementById('heroVideo1');
  var v2 = document.getElementById('heroVideo2');
  if (!v1 || !v2) return;
  var videos = [v1, v2];
  var current = 0;

  v1.play();

  setInterval(function() {
    var next = (current + 1) % 2;
    videos[next].currentTime = 0;
    videos[next].play();
    videos[current].classList.remove('active');
    videos[next].classList.add('active');
    current = next;
  }, 10000);
})();

(function(){
  var el = document.getElementById('typed-sub');
  if (!el) return;
  var texts = [
    'Регистри, разрешителни, дневници и проследяване',
    'Управление на риболовни кораби и аквакултури',
    'Билети за любителски риболов онлайн',
    'Контрол и инспекции в реално време'
  ];
  var ti = 0, ci = 0, isDel = false;
  function type() {
    var txt = texts[ti];
    if (!isDel) {
      el.textContent = txt.slice(0, ci + 1);
      ci++;
      if (ci === txt.length) { setTimeout(function(){ isDel = true; type(); }, 2000); return; }
      setTimeout(type, 40 + Math.random() * 60);
    } else {
      el.textContent = txt.slice(0, ci - 1);
      ci--;
      if (ci === 0) { isDel = false; ti = (ti + 1) % texts.length; setTimeout(type, 400); return; }
      setTimeout(type, 20 + Math.random() * 30);
    }
  }
  setTimeout(type, 500);
})();

(function(){
  var slides = document.querySelectorAll('.about-carousel-slide');
  var dotsWrap = document.getElementById('acDots');
  var prevBtn = document.getElementById('acPrev');
  var nextBtn = document.getElementById('acNext');
  var current = 0;

  function buildDots() {
    dotsWrap.innerHTML = '';
    for (var i = 0; i < slides.length; i++) {
      var dot = document.createElement('button');
      dot.className = 'ac-dot' + (i === 0 ? ' active' : '');
      dot.onclick = (function(idx) { return function() { goTo(idx); }; })(i);
      dotsWrap.appendChild(dot);
    }
  }

  function goTo(idx) {
    slides[current].classList.remove('active');
    current = idx;
    slides[current].classList.add('active');
    var dots = dotsWrap.querySelectorAll('.ac-dot');
    dots.forEach(function(d, i) { d.classList.toggle('active', i === current); });
  }

  prevBtn.addEventListener('click', function() { goTo(current > 0 ? current - 1 : slides.length - 1); });
  nextBtn.addEventListener('click', function() { goTo(current < slides.length - 1 ? current + 1 : 0); });

  buildDots();
  setInterval(function() { goTo(current < slides.length - 1 ? current + 1 : 0); }, 4000);
})();

(function(){
  var tabs = document.querySelectorAll('.ticket-tab');
  var rows = document.querySelectorAll('.tickets-row');

  tabs.forEach(function(tab) {
    tab.addEventListener('click', function() {
      tabs.forEach(function(t) { t.classList.remove('active'); });
      rows.forEach(function(r) { r.classList.add('hidden'); });
      tab.classList.add('active');
      document.querySelector('.tickets-row[data-type="' + tab.dataset.tab + '"]').classList.remove('hidden');
    });
  });
})();

(function(){
  var nums = document.querySelectorAll('.stat-number');
  var observed = false;

  function animateCounters() {
    nums.forEach(function(el) {
      var target = parseInt(el.dataset.target);
      var current = 0;
      var step = Math.ceil(target / 60);
      var timer = setInterval(function() {
        current += step;
        if (current >= target) {
          current = target;
          clearInterval(timer);
        }
        el.textContent = current.toLocaleString('bg-BG') + '+';
      }, 30);
    });
  }

  var obs = new IntersectionObserver(function(entries) {
    if (entries[0].isIntersecting && !observed) {
      observed = true;
      animateCounters();
    }
  }, { threshold: 0.3 });

  var stats = document.querySelector('.stats-section');
  if (stats) obs.observe(stats);
})();

(function(){
  var els = document.querySelectorAll('.about-mini-card, .news-card, .stat-item, .ticket-card');
  if (!els.length) return;
  var obs = new IntersectionObserver(function(entries) {
    entries.forEach(function(e) {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        obs.unobserve(e.target);
      }
    });
  }, { threshold: 0.1 });
  els.forEach(function(el) { obs.observe(el); });
})();

(function(){
  var modal = document.getElementById('ticketModal');
  if (!modal) return;

  var isLoggedIn = modal.dataset.user === 'true';
  var loginUrl = modal.dataset.loginUrl;

  var prices = {
    'standard-1 седмица': {label: '6,14', val: '6.14'}, 'standard-1 месец': {label: '8,18', val: '8.18'}, 'standard-6 месеца': {label: '15,34', val: '15.34'}, 'standard-1 година': {label: '25,56', val: '25.56'},
    'reduced-1 седмица': {label: '3,07', val: '3.07'}, 'reduced-1 месец': {label: '4,09', val: '4.09'}, 'reduced-6 месеца': {label: '7,67', val: '7.67'}, 'reduced-1 година': {label: '12,78', val: '12.78'},
  };
  var typeLabels = {standard: 'Стандартен', reduced: 'Намален', disabled: 'Инвалид'};
  var periodLabels = {'1 седмица': '7 дни', '1 месец': '30 дни', '6 месеца': '180 дни', '1 година': '365 дни'};

  document.querySelectorAll('.ticket-card').forEach(function(card) {
    card.addEventListener('click', function() {
      var type = this.dataset.type;
      var period = this.dataset.period;
      if (!type || !period) return;
      if (type === 'disabled') {
        openModalDisabled(period);
      } else {
        openModal(type, period);
      }
    });
  });

  function openModal(type, period) {
    if (!isLoggedIn) { window.location.href = loginUrl; return; }
    document.getElementById('modalTitle').textContent = 'Потвърдете покупката';
    document.getElementById('modalDesc').textContent = typeLabels[type] + ' билет \u2014 ' + period + ' (' + periodLabels[period] + ')';
    document.getElementById('modalPriceBox').style.display = 'flex';
    document.getElementById('modalPriceAmount').textContent = prices[type + '-' + period].label + ' EUR';
    document.getElementById('modalTicketType').value = type;
    document.getElementById('modalPeriod').value = period;
    document.getElementById('telkField').style.display = 'none';
    document.getElementById('confirmBuyBtn').innerHTML = '<span class="modal-btn-text">Потвърди и плати</span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="16" height="16"><path d="M5 12h14M12 5l7 7-7 7"/></svg>';
    document.getElementById('ticketModal').style.display = 'flex';
  }

  function openModalDisabled(period) {
    if (!isLoggedIn) { window.location.href = loginUrl; return; }
    document.getElementById('modalTitle').textContent = 'Заявление за безплатен билет';
    document.getElementById('modalDesc').textContent = 'Безплатен билет за инвалиди \u2014 ' + period + ' (' + periodLabels[period] + ')';
    document.getElementById('modalPriceBox').style.display = 'flex';
    document.getElementById('modalPriceAmount').textContent = '0,00 EUR';
    document.getElementById('modalTicketType').value = 'disabled';
    document.getElementById('modalPeriod').value = period;
    document.getElementById('telkField').style.display = 'block';
    document.getElementById('confirmBuyBtn').innerHTML = '<span class="modal-btn-text">Подай заявление</span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="16" height="16"><path d="M5 12h14M12 5l7 7-7 7"/></svg>';
    document.getElementById('ticketModal').style.display = 'flex';
  }

  function closeModal() {
    document.getElementById('ticketModal').style.display = 'none';
  }

  document.getElementById('modalCloseBtn').addEventListener('click', closeModal);
  document.getElementById('modalCancelBtn').addEventListener('click', closeModal);
})();