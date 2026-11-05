/* ============================================================================
   vidal.js — the interactive ClaimFlow demo on the Health Claims case study.

   WHAT THIS IS, AND IS NOT
   The source artefact for this project is a static mockup. It renders stage
   one and leaves stages two, three and four as empty labelled rows. This file
   is the four-stage workflow designed out in full for the case study: the
   three missing stages are design work, not a recovered artefact, and the
   page says so beside the frame.

   Everything here is deterministic. The Claim Companion answers from the same
   CLAIM object the stages render from — there is no model, no network call and
   no generation anywhere in this file. That is a design position rather than a
   shortcut: an assistant that composes a settlement figure out of a language
   model is an assistant nobody can audit, and the case study argues for the
   opposite.

   The sample claim is sample data. The claim number is the mockup's own
   (#CLM-88219); the member is invented and named as a sample in the UI.

   Progressive enhancement: stage one is in the markup and works without this
   file, because stage one is the part that genuinely exists. This script adds
   the other three and the companion.
   ========================================================================= */

(function () {
  'use strict';

  var root = document.querySelector('[data-claimflow]');
  if (!root) return;

  /* ── the claim ──────────────────────────────────────────────────────────
     One object. Every stage and every companion answer reads from it, so the
     interface cannot contradict itself — which is the whole argument of the
     coverage and settlement stages.                                        */

  var INR = function (n) {
    return '₹' + n.toLocaleString('en-IN');
  };

  var CLAIM = {
    id: '#CLM-88219',
    member: 'R. Sharma (sample)',
    hospital: 'Ruby Hall Clinic, Pune',
    network: 'In network',
    admitted: '31 Oct 2026',
    discharged: '03 Nov 2026',
    sumInsured: 400000,
    sumUsed: 0,
    roomEligible: 5000,
    roomActual: 8000,
    coPayPct: 10,

    docs: [
      { id: 'discharge', name: 'Discharge Summary',   kind: 'Medical',   state: 'ok',
        note: 'Read and matched to the admission dates on the claim.' },
      { id: 'bills',     name: 'Hospital Bills',      kind: 'Financial', state: 'ok',
        note: 'Itemised bill read. Twenty-three line items extracted.' },
      { id: 'idproof',   name: 'Member ID Proof',     kind: 'Identity',  state: 'ok',
        note: 'Matches the member on the policy.' },
      { id: 'prescrip',  name: 'Prescriptions',       kind: 'Medical',   state: 'ok',
        note: 'Three prescriptions, all within the admission window.' },
      { id: 'invest',    name: 'Investigation Reports', kind: 'Medical', state: 'ok',
        note: 'Pathology and imaging reports present.' },
      { id: 'receipt',   name: 'Payment Receipts',    kind: 'Financial', state: 'warn',
        note: 'Receipt total is ' + INR(248600) + '. The bill total is ' +
              INR(252300) + '. A ' + INR(3700) + ' difference needs a receipt or a note.' },
      { id: 'implant',   name: 'Implant Sticker',     kind: 'Medical',   state: 'stop',
        note: 'Required because the bill carries an implant line. Not supplied, ' +
              'and the implant cannot be assessed without it.' },
      { id: 'bank',      name: 'Bank Details',        kind: 'Settlement', state: 'idle',
        note: 'Needed before a settlement can be paid. Not needed to decide the claim.' }
    ],

    mapping: [
      { doc: 'Discharge Summary', clause: 'Clause 3.1 — Hospitalisation, minimum 24 hours',
        state: 'ok',   note: 'Three nights recorded. The minimum stay condition is met.' },
      { doc: 'Hospital Bills',    clause: 'Clause 4.2 — Room rent, capped at 1% of sum insured per day',
        state: 'warn', note: 'Room billed at ' + INR(8000) + ' a night against an eligible ' +
                             INR(5000) + '. Clause 4.2 prorates the associated charges.' },
      { doc: 'Investigation Reports', clause: 'Clause 3.4 — Diagnostics during admission',
        state: 'ok',   note: 'All reports fall inside the admission window.' },
      { doc: 'Hospital Bills',    clause: 'Clause 5.6 — Non-medical consumables are not payable',
        state: 'stop', note: 'Nine bill lines fall under the non-payable list in Annexure II.' },
      { doc: 'Implant Sticker',   clause: 'Clause 4.9 — Implants, invoice and sticker required',
        state: 'stop', note: 'No document to map. The implant line cannot be assessed.' },
      { doc: 'Member ID Proof',   clause: 'Clause 1.2 — Member is on the policy on the date of admission',
        state: 'ok',   note: 'Policy active from 01 Apr 2026. Admission 31 Oct 2026.' }
    ],

    coverage: [
      { line: 'Room and nursing, 3 nights', billed: 24000, state: 'warn',
        note: 'Eligible at ' + INR(5000) + ' a night under clause 4.2. ' + INR(9000) + ' above the cap.' },
      { line: 'Surgeon and anaesthetist fees', billed: 86000, state: 'warn',
        note: 'Payable, but prorated with the room category under clause 4.2.' },
      { line: 'Operation theatre', billed: 42000, state: 'warn',
        note: 'Prorated on the same basis as the surgeon fee.' },
      { line: 'Investigations and pathology', billed: 31500, state: 'ok',
        note: 'Covered in full under clause 3.4.' },
      { line: 'Pharmacy, in-patient', billed: 28400, state: 'ok',
        note: 'Covered under clause 3.1.' },
      { line: 'Implant', billed: 32000, state: 'stop',
        note: 'Cannot be assessed. Clause 4.9 needs the implant sticker and invoice, and ' +
              'neither is on the claim.' },
      { line: 'Consumables and non-medical items', billed: 8400, state: 'stop',
        note: 'Not payable. Annexure II lists all nine items.' }
    ],

    settlement: [
      { line: 'Total billed',                      amt:  252300, kind: 'base' },
      { line: 'Non-payable consumables, clause 5.6', amt:  -8400,  kind: 'minus' },
      { line: 'Implant, held pending documents',   amt: -32000,  kind: 'minus' },
      { line: 'Room rent above eligibility, clause 4.2', amt: -9000, kind: 'minus' },
      { line: 'Proration of associated charges, clause 4.2', amt: -32000, kind: 'minus' },
      { line: 'Co-payment at 10%, clause 6.1',      amt: -17090,  kind: 'minus' }
    ]
  };

  CLAIM.estimate = CLAIM.settlement.reduce(function (t, r) { return t + r.amt; }, 0);

  /* ── small helpers ──────────────────────────────────────────────────── */

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  var TAG = { ok: 'Verified', warn: 'Needs a look', stop: 'Blocked', idle: 'Not yet needed' };
  var GLYPH = { ok: '✓', warn: '!', stop: '×', idle: '·' };

  function tag(state, label) {
    return el('span', 'cf__tag cf__tag--' + state, label || TAG[state]);
  }

  /* ── the four stages ────────────────────────────────────────────────── */

  var STAGES = [
    {
      n: 1, id: 'docs', name: 'Add Documents',
      sub: function () {
        var ok = CLAIM.docs.filter(function (d) { return d.state === 'ok'; }).length;
        return ok + ' of ' + CLAIM.docs.length + ' verified';
      },
      build: function (host) {
        var grid = el('div', 'cf__docs');
        CLAIM.docs.forEach(function (d) {
          var b = el('button', 'cf__doc');
          b.type = 'button';
          b.dataset.state = d.state;
          b.setAttribute('aria-describedby', 'cf-docnote');
          var i = el('span', 'cf__doci', GLYPH[d.state]);
          i.setAttribute('aria-hidden', 'true');
          var txt = el('span');
          txt.appendChild(el('b', null, d.name));
          txt.appendChild(el('span', null, TAG[d.state] + ' · ' + d.kind));
          b.appendChild(i); b.appendChild(txt);
          b.addEventListener('click', function () { say(d.name + ': ' + d.note, 'Document detail'); });
          grid.appendChild(b);
        });
        host.appendChild(grid);

        var note = el('p', 'cf__caveat');
        note.id = 'cf-docnote';
        note.textContent = 'Select any document to see what the system read from it and what is ' +
          'still outstanding. Two documents are holding this claim up: a receipt that does not ' +
          'reconcile, and a missing implant sticker.';
        host.appendChild(note);
      }
    },
    {
      n: 2, id: 'mapping', name: 'Policy Mapping',
      sub: function () {
        var bad = CLAIM.mapping.filter(function (m) { return m.state !== 'ok'; }).length;
        return CLAIM.mapping.length + ' clauses, ' + bad + ' unresolved';
      },
      build: function (host) {
        var rows = el('div', 'cf__rows');
        CLAIM.mapping.forEach(function (m) {
          var r = el('div', 'cf__row');
          var left = el('div');
          left.appendChild(el('b', null, m.clause));
          r.appendChild(left);
          r.appendChild(tag(m.state, m.state === 'ok' ? 'Matched' :
                                     m.state === 'warn' ? 'Partly matched' : 'No evidence'));
          r.appendChild(el('small', null, m.doc + ' — ' + m.note));
          rows.appendChild(r);
        });
        host.appendChild(rows);
        var note = el('p', 'cf__caveat');
        note.textContent = 'Each row ties one document to one clause. A clause with no document ' +
          'behind it is the reason a claim stalls, so it is stated here rather than discovered ' +
          'two stages later.';
        host.appendChild(note);
      }
    },
    {
      n: 3, id: 'coverage', name: 'Coverage Decision',
      sub: function () {
        var held = CLAIM.coverage.filter(function (c) { return c.state === 'stop'; }).length;
        return CLAIM.coverage.length + ' lines, ' + held + ' held';
      },
      build: function (host) {
        var rows = el('div', 'cf__rows');
        CLAIM.coverage.forEach(function (c) {
          var r = el('div', 'cf__row');
          var left = el('div');
          left.appendChild(el('b', null, c.line));
          r.appendChild(left);
          var right = el('div');
          right.style.display = 'flex';
          right.style.gap = '.6rem';
          right.style.alignItems = 'center';
          right.appendChild(el('span', 'cf__amt', INR(c.billed)));
          right.appendChild(tag(c.state, c.state === 'ok' ? 'Covered' :
                                         c.state === 'warn' ? 'Capped' : 'Held'));
          r.appendChild(right);
          r.appendChild(el('small', null, c.note));
          rows.appendChild(r);
        });
        host.appendChild(rows);
        var note = el('p', 'cf__caveat');
        note.textContent = 'Every line carries the clause it was decided under. An adjuster has ' +
          'to defend this decision later, and a figure without its reason is not defensible.';
        host.appendChild(note);
      }
    },
    {
      n: 4, id: 'settlement', name: 'Estimated Settlement',
      sub: function () { return 'Estimate only'; },
      build: function (host) {
        var rows = el('div', 'cf__rows');
        CLAIM.settlement.forEach(function (s) {
          var r = el('div', 'cf__row' + (s.kind === 'minus' ? ' cf__row--sub' : ''));
          var left = el('div');
          left.appendChild(el('b', null, s.line));
          r.appendChild(left);
          r.appendChild(el('span', 'cf__amt' + (s.kind === 'minus' ? ' cf__amt--minus' : ''),
                           (s.amt < 0 ? '−' : '') + INR(Math.abs(s.amt))));
          rows.appendChild(r);
        });
        host.appendChild(rows);

        var total = el('div', 'cf__total');
        var tl = el('div');
        tl.appendChild(el('p', null, 'Estimated settlement'));
        tl.appendChild(el('b', null, INR(CLAIM.estimate)));
        total.appendChild(tl);
        var tr = el('div');
        tr.appendChild(el('p', null, 'Sum insured remaining'));
        tr.appendChild(el('b', null, INR(CLAIM.sumInsured - CLAIM.sumUsed)));
        total.appendChild(tr);
        host.appendChild(total);

        var note = el('p', 'cf__caveat');
        note.innerHTML = '<b>This is an estimate, not an approval.</b> It assumes the implant ' +
          'line stays held. Supplying the implant sticker would reopen ' + INR(32000) +
          ' for assessment and change this figure. No payment is authorised from this screen.';
        host.appendChild(note);
      }
    }
  ];

  /* ── render ─────────────────────────────────────────────────────────── */

  var railHost = root.querySelector('[data-cf-steps]');
  var workHost = root.querySelector('[data-cf-work]');
  var current = 0;

  var buttons = STAGES.map(function (s, i) {
    var b = el('button', 'cf__step');
    b.type = 'button';
    b.id = 'cf-tab-' + s.id;
    b.setAttribute('role', 'tab');
    b.setAttribute('aria-controls', 'cf-panel-' + s.id);
    b.dataset.done = i === 0 ? 'yes' : 'no';
    var n = el('span', 'cf__stepn', String(s.n));
    n.setAttribute('aria-hidden', 'true');
    b.appendChild(n);
    b.appendChild(el('span', null, s.name));
    b.addEventListener('click', function () { show(i); });
    b.addEventListener('keydown', function (e) {
      var d = e.key === 'ArrowDown' || e.key === 'ArrowRight' ? 1
            : e.key === 'ArrowUp'   || e.key === 'ArrowLeft'  ? -1
            : e.key === 'Home' ? -99 : e.key === 'End' ? 99 : 0;
      if (!d) return;
      e.preventDefault();
      // Move relative to the tab that has focus, not to the selected stage.
      // Those are usually the same, but a reader can tab into the rail while a
      // later stage is open, and an arrow key there should step from where the
      // focus is rather than jumping somewhere else entirely.
      var from = buttons.indexOf(e.currentTarget);
      if (from < 0) from = current;
      var next = d === -99 ? 0 : d === 99 ? STAGES.length - 1
               : (from + d + STAGES.length) % STAGES.length;
      show(next);
      buttons[next].focus();
    });
    return b;
  });

  railHost.innerHTML = '';
  railHost.setAttribute('role', 'tablist');
  railHost.setAttribute('aria-label', 'Claim stages');
  buttons.forEach(function (b) { railHost.appendChild(b); });

  function show(i) {
    current = i;
    var s = STAGES[i];

    buttons.forEach(function (b, j) {
      b.setAttribute('aria-selected', j === i ? 'true' : 'false');
      b.tabIndex = j === i ? 0 : -1;
    });

    var panel = el('div', 'cf__panel');
    panel.id = 'cf-panel-' + s.id;
    panel.setAttribute('role', 'tabpanel');
    panel.setAttribute('aria-labelledby', 'cf-tab-' + s.id);
    panel.tabIndex = 0;

    var head = el('div', 'cf__stagehead');
    var hl = el('div');
    var hn = el('span', 'cf__stagen', String(s.n));
    hn.setAttribute('aria-hidden', 'true');
    hl.appendChild(hn);
    var ht = el('div');
    ht.appendChild(el('h4', null, s.name));
    ht.appendChild(el('p', null, s.sub()));
    hl.appendChild(ht);
    head.appendChild(hl);
    panel.appendChild(head);

    s.build(panel);

    var actions = el('div', 'cf__actions');
    actions.style.marginTop = 'var(--step-4)';
    if (i > 0) {
      var prev = el('button', 'cf__btn cf__btn--ghost', 'Back');
      prev.type = 'button';
      prev.addEventListener('click', function () { show(i - 1); buttons[i - 1].focus(); });
      actions.appendChild(prev);
    }
    if (i < STAGES.length - 1) {
      var next = el('button', 'cf__btn', 'Continue to ' + STAGES[i + 1].name);
      next.type = 'button';
      next.addEventListener('click', function () {
        buttons[i].dataset.done = 'yes';
        show(i + 1);
        buttons[i + 1].focus();
      });
      actions.appendChild(next);
    }
    panel.appendChild(actions);

    workHost.innerHTML = '';
    workHost.appendChild(panel);
  }

  /* ── the companion ──────────────────────────────────────────────────────
     Answers are composed from CLAIM by ordinary code and each one names the
     clause or the document it came from. Nothing is generated.            */

  var compDoc = root.querySelector('[data-cf-messages]');
  var askHost = root.querySelector('[data-cf-asks]');

  var ANSWERS = [
    { q: 'What is holding this claim up?',
      a: function () {
        return 'Two things. The implant sticker is missing, which holds ' + INR(32000) +
               ' under clause 4.9. And the payment receipts total ' + INR(248600) +
               ' against a bill of ' + INR(252300) + ', a ' + INR(3700) + ' gap.';
      },
      src: 'Documents · clause 4.9' },
    { q: 'Why is the room rent reduced?',
      a: function () {
        return 'The room was billed at ' + INR(CLAIM.roomActual) + ' a night. Clause 4.2 caps ' +
               'the room at 1% of the sum insured, which is ' + INR(CLAIM.roomEligible) +
               ' a night here. The excess is deducted, and the clause also prorates the ' +
               'surgeon, theatre and anaesthetist charges that were billed at the higher room category.';
      },
      src: 'Clause 4.2' },
    { q: 'How was the estimate calculated?',
      a: function () {
        return 'From the billed total of ' + INR(252300) + ', less non-payable consumables, ' +
               'the held implant, the room excess, the proration, and a 10% co-payment. ' +
               'That leaves ' + INR(CLAIM.estimate) + '. Stage four shows each line.';
      },
      src: 'Stage 4 · clauses 4.2, 5.6, 6.1' },
    { q: 'Can I approve this now?',
      a: function () {
        return 'Not from here. This is an estimate rather than a decision, and one line is ' +
               'still held pending a document. Nothing on this screen authorises a payment.';
      },
      src: 'Scope of this screen' },
    { q: 'What happens if the implant sticker arrives?',
      a: function () {
        return 'The implant line reopens for assessment and ' + INR(32000) +
               ' comes back into scope, so the estimate changes. The claim returns to stage two ' +
               'so the document can be mapped to clause 4.9 before coverage is decided again.';
      },
      src: 'Clause 4.9 · stage 2' }
  ];

  function say(text, src) {
    var m = el('div', 'cf__msg cf__msg--bot');
    m.appendChild(document.createTextNode(text));
    if (src) m.appendChild(el('span', 'cf__src', 'Source: ' + src));
    compDoc.appendChild(m);
    compDoc.scrollTop = compDoc.scrollHeight;
  }

  if (askHost) {
    ANSWERS.forEach(function (item) {
      var b = el('button', 'cf__ask', item.q);
      b.type = 'button';
      b.addEventListener('click', function () {
        var you = el('div', 'cf__msg cf__msg--you', item.q);
        compDoc.appendChild(you);
        say(item.a(), item.src);
      });
      askHost.appendChild(b);
    });
  }

  /* ── reset ──────────────────────────────────────────────────────────── */

  var reset = document.querySelector('[data-cf-reset]');
  if (reset) {
    reset.addEventListener('click', function () {
      compDoc.innerHTML = '';
      say('Reviewing the documents on claim ' + CLAIM.id + ' for ' + CLAIM.member +
          '. Ask about coverage, the deductions, or what is outstanding.', 'Sample claim');
      buttons.forEach(function (b, j) { b.dataset.done = j === 0 ? 'yes' : 'no'; });
      show(0);
      buttons[0].focus();
    });
  }

  say('Reviewing the documents on claim ' + CLAIM.id + ' for ' + CLAIM.member +
      '. Ask about coverage, the deductions, or what is outstanding.', 'Sample claim');
  show(0);
})();
