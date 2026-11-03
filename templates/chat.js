// DOM refs
const side = document.getElementById('side');
const msgs = document.getElementById('messages');
const input = document.getElementById('input');
const send = document.getElementById('send');
const pdf = document.getElementById('pdf');
const fileBar = document.getElementById('file');
const fname = document.getElementById('fname');
const uploadButton = document.createElement('button');
uploadButton.className = 'quiz-next';
uploadButton.type = 'button';
uploadButton.textContent = 'Upload PDF';
fileBar.insertBefore(uploadButton, document.getElementById('remove'));
const composerArea = document.querySelector('.composer-area');
const quizControls = document.createElement('div');
quizControls.className = 'quiz-controls';
const quizLabel = document.createElement('label');
quizLabel.textContent = 'Quiz length';
const quizCount = document.createElement('select');
quizCount.setAttribute('aria-label', 'Quiz length');
for (const count of [5, 10, 15]) {
  const option = document.createElement('option');
  option.value = count;
  option.textContent = `${count} questions`;
  option.selected = count === 10;
  quizCount.appendChild(option);
}
const quizStart = document.createElement('button');
quizStart.className = 'quiz-start';
quizStart.type = 'button';
quizStart.textContent = 'Create quiz';
quizControls.append(quizLabel, quizCount, quizStart);
composerArea.prepend(quizControls);
const flashcardControls = document.createElement('div');
flashcardControls.className = 'quiz-controls';
const flashcardLabel = document.createElement('label');
flashcardLabel.textContent = 'Flashcard count';
const flashcardCount = document.createElement('select');
flashcardCount.setAttribute('aria-label', 'Flashcard count');
for (const count of [10, 20, 30]) {
  const option = document.createElement('option');
  option.value = count;
  option.textContent = `${count} cards`;
  option.selected = count === 10;
  flashcardCount.appendChild(option);
}
const flashcardStart = document.createElement('button');
flashcardStart.className = 'quiz-start';
flashcardStart.type = 'button';
flashcardStart.textContent = 'Create flashcards';
flashcardControls.append(flashcardLabel, flashcardCount, flashcardStart);
composerArea.prepend(flashcardControls);

// Sidebar open/close
document.getElementById('open').onclick = () => side.classList.add('open');
document.getElementById('close').onclick = () => side.classList.remove('open');

// Logout
document.getElementById('logout').onclick = () => { location.href = '/'; };

// Add a message bubble to the chat
function add(text, user = false, isHtml = false) {
  const x = document.createElement('div');
  x.className = 'msg ' + (user ? 'user' : '');
  const avatar = '<div class="avatar">' + (user ? 'U' : '✦') + '</div>';
  const body = '<div class="msg-body">' + (isHtml ? text : escapeHtml(text).replace(/\n/g, '<br>')) + '</div>';
  x.innerHTML = avatar + body;
  msgs.appendChild(x);
  msgs.scrollTop = msgs.scrollHeight;
  return x;
}

async function startQuiz(count = Number(quizCount.value)) {
  if (send.disabled || quizStart.disabled) return;
  send.disabled = true;
  quizStart.disabled = true;
  const loader = addLoading('Building a quiz from your latest PDF…');
  try {
    const response = await fetch('/quiz', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question_count: count })
    });
    const quiz = await readApiResponse(response);
    if (!Array.isArray(quiz.questions) || !quiz.questions.length) {
      throw new Error('The server returned an empty quiz. Try again.');
    }
    loader.remove();
    renderQuiz(quiz);
  } catch (error) {
    loader.remove();
    add(`⚠ ${error.message || 'Could not create the quiz. Try again.'}`);
  } finally {
    send.disabled = false;
    quizStart.disabled = false;
  }
}

async function startFlashcards(count = Number(flashcardCount.value)) {
  if (send.disabled || flashcardStart.disabled) return;
  send.disabled = true;
  flashcardStart.disabled = true;
  const loader = addLoading('Building flashcards from your latest PDF…');
  try {
    const response = await fetch('/flashcards', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ card_count: count })
    });
    const deck = await readApiResponse(response);
    if (!Array.isArray(deck.cards) || !deck.cards.length) {
      throw new Error('The server returned no flashcards. Try again.');
    }
    loader.remove();
    renderFlashcards(deck);
  } catch (error) {
    loader.remove();
    add(`⚠ ${error.message || 'Could not create flashcards. Try again.'}`);
  } finally {
    send.disabled = false;
    flashcardStart.disabled = false;
  }
}

function renderFlashcards(deck) {
  const section = document.createElement('section');
  section.className = 'flashcard-deck';
  const title = document.createElement('h2');
  title.textContent = deck.title || 'PDF Flashcards';
  const progress = document.createElement('p');
  progress.className = 'quiz-progress';
  const card = document.createElement('div');
  card.className = 'flashcard';
  card.setAttribute('aria-live', 'polite');
  const faceLabel = document.createElement('small');
  const faceText = document.createElement('p');
  const actions = document.createElement('div');
  actions.className = 'flashcard-actions';
  const reveal = document.createElement('button');
  reveal.className = 'quiz-next';
  reveal.type = 'button';
  const next = document.createElement('button');
  next.className = 'quiz-next';
  next.type = 'button';

  let index = 0;
  let isRevealed = false;

  function showCard() {
    isRevealed = false;
    const current = deck.cards[index];
    progress.textContent = `Card ${index + 1} of ${deck.cards.length}`;
    faceLabel.textContent = 'FRONT';
    faceText.textContent = current.front;
    reveal.textContent = 'Reveal answer';
    next.textContent = index === deck.cards.length - 1 ? 'Finish deck' : 'Next card';
    next.disabled = false;
  }

  reveal.addEventListener('click', () => {
    const current = deck.cards[index];
    isRevealed = !isRevealed;
    faceLabel.textContent = isRevealed ? 'ANSWER' : 'FRONT';
    faceText.textContent = isRevealed ? current.back : current.front;
    reveal.textContent = isRevealed ? 'Show front' : 'Reveal answer';
  });

  next.addEventListener('click', () => {
    if (index >= deck.cards.length - 1) {
      section.replaceChildren(title);
      const completed = document.createElement('p');
      completed.className = 'quiz-progress';
      completed.textContent = `You reviewed all ${deck.cards.length} flashcards.`;
      const restart = document.createElement('button');
      restart.className = 'quiz-next';
      restart.type = 'button';
      restart.textContent = 'Study these cards again';
      restart.addEventListener('click', () => {
        index = 0;
        section.replaceChildren(title, progress, card, actions);
        showCard();
      });
      section.replaceChildren(title, completed, restart);
      msgs.scrollTop = msgs.scrollHeight;
      return;
    }
    index += 1;
    showCard();
    msgs.scrollTop = msgs.scrollHeight;
  });

  actions.append(reveal, next);
  card.append(faceLabel, faceText);
  section.append(title, progress, card, actions);
  msgs.appendChild(section);
  showCard();
}

function renderQuiz(quiz) {
  const card = document.createElement('section');
  card.className = 'quiz-card';
  const title = document.createElement('h2');
  title.textContent = quiz.title || 'PDF Practice Quiz';
  const progress = document.createElement('p');
  progress.className = 'quiz-progress';
  const questionText = document.createElement('h3');
  const options = document.createElement('div');
  options.className = 'quiz-options';
  const feedback = document.createElement('p');
  feedback.className = 'quiz-feedback';
  const next = document.createElement('button');
  next.className = 'quiz-next';
  next.type = 'button';
  next.hidden = true;

  let questionIndex = 0;
  let score = 0;
  let answered = false;

  function showResults() {
    card.replaceChildren(title);
    const result = document.createElement('h3');
    result.textContent = `You scored ${score} out of ${quiz.questions.length}`;
    const summary = document.createElement('p');
    summary.className = 'quiz-progress';
    summary.textContent = 'Your answers were checked against the active PDF.';
    const restart = document.createElement('button');
    restart.className = 'quiz-next';
    restart.type = 'button';
    restart.textContent = 'Try another quiz';
    restart.addEventListener('click', () => startQuiz(Number(quizCount.value)));
    card.append(result, summary, restart);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function showQuestion() {
    answered = false;
    const question = quiz.questions[questionIndex];
    progress.textContent = `Question ${questionIndex + 1} of ${quiz.questions.length} · Score ${score}`;
    questionText.textContent = question.question;
    options.replaceChildren();
    feedback.textContent = '';
    next.hidden = true;
    question.options.forEach((option, optionIndex) => {
      const button = document.createElement('button');
      button.className = 'quiz-option';
      button.type = 'button';
      button.textContent = option;
      button.addEventListener('click', () => {
        if (answered) return;
        answered = true;
        const isCorrect = optionIndex === question.answer_index;
        if (isCorrect) score += 1;
        for (const [index, optionButton] of [...options.children].entries()) {
          optionButton.disabled = true;
          if (index === question.answer_index) optionButton.classList.add('correct');
          else if (index === optionIndex) optionButton.classList.add('incorrect');
        }
        feedback.textContent = `${isCorrect ? 'Correct.' : 'Not quite.'} ${question.explanation}`;
        progress.textContent = `Question ${questionIndex + 1} of ${quiz.questions.length} · Score ${score}`;
        next.textContent = questionIndex === quiz.questions.length - 1 ? 'See results' : 'Next question';
        next.hidden = false;
      });
      options.appendChild(button);
    });
    msgs.scrollTop = msgs.scrollHeight;
  }

  next.addEventListener('click', () => {
    if (!answered) return;
    questionIndex += 1;
    if (questionIndex >= quiz.questions.length) showResults();
    else showQuestion();
  });

  card.append(title, progress, questionText, options, feedback, next);
  msgs.appendChild(card);
  showQuestion();
}
function escapeHtml(t) {
  return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

async function readApiResponse(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || data.message || `Request failed (${response.status})`);
  }
  return data;
}

// Show a loading spinner bubble, returns the element so it can be replaced
function addLoading() {
  const x = document.createElement('div');
  x.className = 'msg';
  x.innerHTML = '<div class="avatar">✦</div><div class="msg-body" style="color:#6b637a;font-style:italic">Thinking…</div>';
  msgs.appendChild(x);
  msgs.scrollTop = msgs.scrollHeight;
  return x;
}

// ── SEND MESSAGE ──────────────────────────────────────────────────────────────
async function ask() {
  const q = input.value.trim();
  if (!q || send.disabled) return;

  send.disabled = true;
  let loader;
  try {
    const pendingFile = pdf.files[0];
    if (pendingFile) {
      const uploaded = await uploadPdf(pendingFile);
      if (!uploaded) return;
      add('PDF uploaded. Send your question when ready.', false);
      return;
    }

    add(q, true);
    input.value = '';
    input.style.height = 'auto';

    loader = addLoading();
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: q })
    });
    const data = await readApiResponse(res);
    if (typeof data.reply !== 'string' || !data.reply.trim()) {
      throw new Error('The server returned an empty reply. Try again.');
    }
    loader.remove();
    add(data.reply.trim(), false);
  } catch (err) {
    if (loader) loader.remove();
    add(`⚠ ${err.message || 'Could not reach the server. Try again.'}`, false);
  } finally {
    send.disabled = false;
  }
}

send.onclick = ask;
input.onkeydown = e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ask(); }
};

// Auto-resize textarea
input.oninput = () => {
  input.style.height = 'auto';
  input.style.height = input.scrollHeight + 'px';
};

// Quick-prompt buttons
document.querySelectorAll('[data-q]').forEach(b => b.onclick = () => {
  if (b.dataset.q.toLowerCase().includes('quiz')) {
    startQuiz(Number(quizCount.value));
    return;
  }
  if (b.dataset.q.toLowerCase().includes('flashcard')) {
    startFlashcards(Number(flashcardCount.value));
    return;
  }
  input.value = b.dataset.q;
  input.focus();
});
quizStart.addEventListener('click', () => startQuiz(Number(quizCount.value)));
flashcardStart.addEventListener('click', () => startFlashcards(Number(flashcardCount.value)));

// ── PDF UPLOAD ────────────────────────────────────────────────────────────────
pdf.onchange = e => {
  const f = e.target.files[0];
  if (f) { fname.textContent = f.name; fileBar.classList.add('show'); }
};

document.getElementById('remove').onclick = () => {
  pdf.value = '';
  fileBar.classList.remove('show');
};

async function uploadPdf(file) {
  const statusBubble = add(`📄 Uploading "${file.name}"…`, false);
  const formData = new FormData();
  formData.append('file', file);
  uploadButton.disabled = true;
  try {
    const res = await fetch('/upload', { method: 'POST', body: formData });
    const data = await readApiResponse(res);
    statusBubble.querySelector('.msg-body').textContent = '✓ ' + (data.message || 'PDF uploaded.');
    pdf.value = '';
    fileBar.classList.remove('show');
    return true;
  } catch (err) {
    statusBubble.querySelector('.msg-body').textContent = `⚠ ${err.message || 'Upload failed. Try again.'}`;
    return false;
  } finally {
    uploadButton.disabled = false;
  }
}

uploadButton.addEventListener('click', () => {
  const file = pdf.files[0];
  if (file) uploadPdf(file);
});

// ── CLEAR CHAT ────────────────────────────────────────────────────────────────
document.getElementById('clear').onclick = async () => {
  if (!confirm('Clear all chat history and uploaded documents?')) return;
  try {
    const res = await fetch('/clear', { method: 'POST' });
    await readApiResponse(res);
    const allMsgs = msgs.querySelectorAll('.msg');
    allMsgs.forEach(m => m.remove());
  } catch (err) {
    add(`⚠ ${err.message || 'Could not clear chat. Try again.'}`, false);
  }
};

// ── NEW CHAT ──────────────────────────────────────────────────────────────────
document.getElementById('new').onclick = () => location.reload();
