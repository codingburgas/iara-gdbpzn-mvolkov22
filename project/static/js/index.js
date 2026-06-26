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
