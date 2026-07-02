/**
 * Nanobody (VHH) CDR annotation for Google Sheets — IMGT scheme.
 * Part of propro (propro.motifs.nanobodies). See README.md in this folder
 * for sheet layout and install instructions.
 *
 * What it does on the "nanobodies" tab:
 *   1. Reads each sequence in the "AA Sequences" column.
 *   2. Extracts IMGT CDR1 / CDR2 / CDR3 and writes them to the
 *      "CDR1", "CDR2", "CDR3" columns.
 *   3. Recolors the AA-sequence cell so each CDR is shown in its own font color:
 *         CDR1 = red, CDR2 = green, CDR3 = blue (frameworks stay default).
 *
 * Method: conserved-residue anchoring (no external tools needed).
 *   CDR1  = between the 1st conserved Cys (Cys23) and the FR2 Trp (Trp41)
 *   CDR3  = between the 2nd conserved Cys (Cys104) and the WGxG / FR4 motif
 *   CDR2  = fixed offset after Trp41, ending at the conserved FR3 motif
 * CDR1 and CDR3 are anchored on both sides by conserved residues, so they are
 * exact regardless of loop length. CDR2's downstream boundary is heuristic —
 * spot-check a few if your CDR2 loops are unusual.
 *
 * HOW TO RUN:
 *   Extensions > Apps Script  →  paste this file  →  Save  →
 *   choose "annotateNanobodyCDRs" in the function dropdown  →  Run.
 *   (First run asks for authorization — approve it.)
 */

// ---- settings ----
var SHEET_NAME   = 'nanobodies';
var SEQ_HEADER   = 'AA Sequences';
var CDR_HEADERS  = ['CDR1', 'CDR2', 'CDR3'];
var CDR_COLORS   = ['#C0392B', '#1E8449', '#1F4E9C']; // red, green, blue
var BOLD_CDRS    = true;

function annotateNanobodyCDRs() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) throw new Error('Tab "' + SHEET_NAME + '" not found.');

  var lastRow = sh.getLastRow(), lastCol = sh.getLastColumn();
  if (lastRow < 2) { SpreadsheetApp.getUi().alert('No data rows found.'); return; }

  // normalize a header for tolerant matching: lowercase, strip spaces/punctuation
  function norm(h) { return String(h).toLowerCase().replace(/[^a-z0-9]/g, ''); }
  // accepted spellings for the sequence column
  var SEQ_KEYS = ['aasequences', 'aasequence', 'aaseq', 'aminoacidsequence', 'sequence', 'seq'];

  // scan the first 15 rows to find the header row (the one holding the sequence header)
  var scanN = Math.min(15, lastRow);
  var grid = sh.getRange(1, 1, scanN, lastCol).getValues();
  var headerRow = -1, headers = null, seqCol = 0;
  for (var hr = 0; hr < scanN; hr++) {
    var row = grid[hr].map(norm);
    var sc = -1;
    for (var c = 0; c < row.length; c++) {
      if (SEQ_KEYS.indexOf(row[c]) >= 0) { sc = c; break; }
    }
    if (sc === -1) { // fallback: any header containing "sequence"
      for (var c2 = 0; c2 < row.length; c2++) {
        if (row[c2].indexOf('sequence') >= 0 || row[c2].indexOf('aaseq') >= 0) { sc = c2; break; }
      }
    }
    if (sc !== -1) { headerRow = hr + 1; headers = row; seqCol = sc + 1; break; }
  }
  if (headerRow === -1) {
    throw new Error('Could not find a sequence header. Headers seen in row 1: [' +
      grid[0].map(function (x) { return '"' + String(x) + '"'; }).join(', ') + ']');
  }

  function colOf(key) { return headers.indexOf(norm(key)) + 1; } // 1-based; 0 if missing
  var cdrCols = CDR_HEADERS.map(colOf);
  cdrCols.forEach(function (c, i) {
    if (!c) throw new Error('Column "' + CDR_HEADERS[i] + '" not found. Headers seen in row ' +
      headerRow + ': [' + grid[headerRow - 1].map(function (x) { return '"' + String(x) + '"'; }).join(', ') + ']');
  });

  var firstData = headerRow + 1;
  var n = lastRow - headerRow;
  var seqs = sh.getRange(firstData, seqCol, n, 1).getValues();

  var cdr1Out = [], cdr2Out = [], cdr3Out = [], richOut = [];

  for (var r = 0; r < n; r++) {
    var raw = String(seqs[r][0] || '');
    var seq = raw.replace(/[^A-Za-z]/g, '').toUpperCase();
    if (!seq) { cdr1Out.push(['']); cdr2Out.push(['']); cdr3Out.push(['']); richOut.push([null]); continue; }

    var f = findCDRs(seq);
    cdr1Out.push([f.CDR1]); cdr2Out.push([f.CDR2]); cdr3Out.push([f.CDR3]);

    // build rich text on the cleaned sequence (so positions line up)
    var b = SpreadsheetApp.newRichTextValue().setText(seq);
    var ranges = [f.r1, f.r2, f.r3];
    for (var i = 0; i < 3; i++) {
      var rg = ranges[i];
      if (rg && rg[1] > rg[0]) {
        var st = SpreadsheetApp.newTextStyle().setForegroundColor(CDR_COLORS[i]);
        if (BOLD_CDRS) st.setBold(true);
        b.setTextStyle(rg[0], rg[1], st.build());
      }
    }
    richOut.push([b.build()]);
  }

  // write CDR columns + style them: Courier New, font color matching each CDR's highlight
  var cdrData = [cdr1Out, cdr2Out, cdr3Out];
  for (var ci = 0; ci < 3; ci++) {
    var rng = sh.getRange(firstData, cdrCols[ci], n, 1);
    rng.setValues(cdrData[ci]);
    rng.setFontFamily('Courier New').setFontColor(CDR_COLORS[ci]);
    if (BOLD_CDRS) rng.setFontWeight('bold');
  }

  // write colored sequences (skip nulls so blank rows are left untouched)
  for (var rr = 0; rr < n; rr++) {
    if (richOut[rr][0]) sh.getRange(firstData + rr, seqCol).setRichTextValue(richOut[rr][0]);
  }

  // left-align and wrap text across all used columns
  sh.getDataRange().setHorizontalAlignment('left').setWrap(true);

  SpreadsheetApp.getActiveSpreadsheet().toast('Annotated ' + n + ' rows.', 'CDR done', 5);
}

/**
 * Extract IMGT CDR1/2/3 + their [start,end) char positions from a VHH sequence.
 */
function findCDRs(s) {
  var R = { CDR1: '', CDR2: '', CDR3: '', r1: null, r2: null, r3: null };

  var c1 = s.indexOf('C');                 // Cys23
  if (c1 < 0) return R;

  // FR2 Trp (Trp41): W-x-[RQK] after the CDR1 region
  var m = s.slice(c1 + 8).match(/W[A-Z]{0,2}[RQK]/);
  if (!m) m = s.slice(c1 + 8).match(/W/);
  var trp = m ? c1 + 8 + m.index : -1;

  // FR4 WGxG (take the last occurrence)
  var wg = -1, re = /WG[A-Z][GQ]/g, mm;
  while ((mm = re.exec(s)) !== null) wg = mm.index;
  if (wg < 0) { var m2 = s.match(/W[GA][A-Z][GQ]/); wg = m2 ? m2.index : -1; }

  // Cys104: a Cys with WGxG 3..45 downstream, preferring aromatic context, earliest such
  var cands = [];
  for (var i = c1 + 1; i < s.length; i++) {
    if (s.charAt(i) === 'C' && wg - i >= 3 && wg - i <= 45) cands.push(i);
  }
  var c2 = -1, arom = cands.filter(function (p) {
    return (p >= 2 && 'YFWH'.indexOf(s.charAt(p - 2)) >= 0) ||
           (p >= 1 && 'YF'.indexOf(s.charAt(p - 1)) >= 0);
  });
  if (arom.length) c2 = Math.min.apply(null, arom);
  else if (cands.length) c2 = Math.min.apply(null, cands);

  // CDR1: Cys23+4 .. Trp41-2
  if (trp !== -1 && trp - 2 > c1 + 4) { R.r1 = [c1 + 4, trp - 2]; R.CDR1 = s.slice(R.r1[0], R.r1[1]); }

  // CDR3: Cys104+1 .. WGxG
  if (c2 !== -1 && wg !== -1 && wg > c2 + 1) { R.r3 = [c2 + 1, wg]; R.CDR3 = s.slice(R.r3[0], R.r3[1]); }

  // CDR2: Trp41+15 .. (conserved FR3 motif - 8)
  if (trp !== -1) {
    var st = trp + 15;
    var sub = s.slice(st, c2 > 0 ? c2 : s.length);
    var core = sub.match(/[KR][FLY][ST][ILV][ST]/);
    var end = (core && core.index - 8 > 0) ? st + core.index - 8 : st + 8;
    if (end > st) { R.r2 = [st, end]; R.CDR2 = s.slice(st, end); }
  }
  return R;
}
