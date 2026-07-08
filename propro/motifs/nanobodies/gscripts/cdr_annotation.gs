/**
 * Nanobody (VHH) CDR annotation + property summary for Google Sheets — IMGT scheme.
 * Part of propro (propro.motifs.nanobodies). See README.md in this folder
 * for sheet layout and install instructions.
 *
 * What it does on the "nanobodies" tab (one pass, one menu click):
 *   1. Reads each sequence in the "AA Sequences" column.
 *   2. Extracts IMGT CDR1 / CDR2 / CDR3 and writes them to the
 *      "CDR1", "CDR2", "CDR3" columns, each in its own font color
 *      (CDR1 = red, CDR2 = green, CDR3 = blue). Below the residues of each
 *      CDR cell it adds a compact grey stats line:
 *          q<±charge>  φ<n> · pol<n> · chg<n>
 *      = net charge at pH 7.4, and counts of hydrophobic / polar / charged
 *      side chains for that loop.
 *   3. Recolors the AA-sequence cell so each CDR is shown in its CDR color
 *      (frameworks stay default).
 *   4. Writes whole-sequence bulk properties to their own columns (auto-created
 *      if missing): isoelectric point, molecular weight (kDa), molar extinction
 *      coefficient (M^-1 cm^-1) and A280 at 1 mg/mL — each given for both the
 *      reduced and the oxidized (disulfides formed) state.
 *
 * Property math mirrors ExPASy ProtParam / BioPython (verified against
 * Bio.SeqUtils IsoelectricPoint and molecular_weight):
 *   - MW    = sum of average residue masses + one water.
 *   - pI    = Bjellqvist pKa set, terminus-aware, solved by bisection.
 *   - ext   = Tyr*1490 + Trp*5500 (reduced); + (Cys//2)*125 for cystines (oxidized).
 *   - A280  = ext / MW   (absorbance of a 1 mg/mL = 0.1% solution).
 * Per-CDR net charge uses the same side-chain pKa at pH 7.4 with NO terminal
 * groups (a CDR is an internal fragment, so its ends are not real termini).
 *
 * Method for CDR boundaries: conserved-residue anchoring (no external tools).
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
var STATS_COLOR  = '#7F7F7F';   // grey for the per-CDR stats line
var STATS_SIZE   = 8;           // pt, for the per-CDR stats line
var CDR_NET_CHARGE_PH = 7.4;

// Bulk-property columns (auto-created at the end of the header row if missing).
var PROP_HEADERS = ['pI', 'MW (kDa)', 'Ext coeff (M-1 cm-1)', 'A280 (1 mg/mL)'];

// ---- side-chain classification for per-CDR counts ----
// Hydrophobic + polar(uncharged) + charged. Charged residues (D,E,K,R) are
// reported as their own count and drive the net charge; His is treated as
// polar for the count but still contributes (partially) to net charge.
var HYDROPHOBIC = 'AVLIMFWYC';
var POLAR       = 'STNQHG';
var CHARGED     = 'DEKR';

// ---- property constants (average residue masses, Da) ----
var AA_MASS = {
  G: 57.0513,  A: 71.0788,  S: 87.0782,  P: 97.1167,  V: 99.1326,
  T: 101.1051, C: 103.1388, L: 113.1594, I: 113.1594, N: 114.1038,
  D: 115.0886, Q: 128.1307, K: 128.1741, E: 129.1155, M: 131.1926,
  H: 137.1411, F: 147.1766, R: 156.1875, Y: 163.1760, W: 186.2132
};
var WATER = 18.01524;

// Bjellqvist / ExPASy pKa (matches BioPython IsoelectricPoint).
var POS_PK    = { Nterm: 7.5, K: 10.0, R: 12.0, H: 5.98 };
var NEG_PK    = { Cterm: 3.55, D: 4.05, E: 4.45, C: 9.0, Y: 10.0 };
var PK_NTERM  = { A: 7.59, M: 7.0, S: 6.93, P: 8.36, T: 6.82, V: 7.44, E: 7.7 };
var PK_CTERM  = { D: 4.55, E: 4.75 };


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

  // Property columns: create any that are missing at the end of the header row.
  var propCols = PROP_HEADERS.map(colOf);
  var nextCol = lastCol;
  for (var pc = 0; pc < PROP_HEADERS.length; pc++) {
    if (!propCols[pc]) {
      nextCol += 1;
      sh.getRange(headerRow, nextCol).setValue(PROP_HEADERS[pc]).setFontWeight('bold');
      propCols[pc] = nextCol;
      headers.push(norm(PROP_HEADERS[pc])); // keep headers array in sync
    }
  }

  var firstData = headerRow + 1;
  var n = lastRow - headerRow;
  var seqs = sh.getRange(firstData, seqCol, n, 1).getValues();

  var cdrRich = [[], [], []];  // rich text for each CDR column (residues + grey stats)
  var richOut = [];            // recolored full sequence
  var piOut = [], mwOut = [], extOut = [], a280Out = [];

  for (var r = 0; r < n; r++) {
    var raw = String(seqs[r][0] || '');
    var seq = raw.replace(/[^A-Za-z]/g, '').toUpperCase();
    if (!seq) {
      for (var k = 0; k < 3; k++) cdrRich[k].push([null]);
      richOut.push([null]); piOut.push(['']); mwOut.push(['']); extOut.push([null]); a280Out.push([null]);
      continue;
    }

    var f = findCDRs(seq);

    // --- per-CDR cells: residues (colored/bold) + grey stats line below ---
    var loops = [f.CDR1, f.CDR2, f.CDR3];
    for (var i = 0; i < 3; i++) {
      cdrRich[i].push([buildCdrCell(loops[i], CDR_COLORS[i])]);
    }

    // --- recolor the full sequence in place ---
    var b = SpreadsheetApp.newRichTextValue().setText(seq);
    var ranges = [f.r1, f.r2, f.r3];
    for (var j = 0; j < 3; j++) {
      var rg = ranges[j];
      if (rg && rg[1] > rg[0]) {
        var st = SpreadsheetApp.newTextStyle().setForegroundColor(CDR_COLORS[j]);
        if (BOLD_CDRS) st.setBold(true);
        b.setTextStyle(rg[0], rg[1], st.build());
      }
    }
    richOut.push([b.build()]);

    // --- whole-sequence bulk properties (standard 20 residues only) ---
    var clean = seq.replace(/[^ACDEFGHIKLMNPQRSTVWY]/g, '');
    var mw = molWeight(clean);
    var ext = extinction(clean);
    piOut.push([round(isoelectricPoint(clean), 2)]);
    mwOut.push([round(mw / 1000, 2)]);
    extOut.push([buildTwoLineCell('ox: ' + ext.ox, 'red: ' + ext.red)]);
    var aOx = mw > 0 ? ext.ox / mw : 0, aRed = mw > 0 ? ext.red / mw : 0;
    a280Out.push([buildTwoLineCell('ox: ' + round(aOx, 3), 'red: ' + round(aRed, 3))]);
  }

  // write CDR columns (rich text per cell), set Courier + wrap on the column
  for (var ci = 0; ci < 3; ci++) {
    var col = cdrCols[ci];
    sh.getRange(firstData, col, n, 1).setFontFamily('Courier New');
    for (var rr = 0; rr < n; rr++) {
      if (cdrRich[ci][rr][0]) sh.getRange(firstData + rr, col).setRichTextValue(cdrRich[ci][rr][0]);
    }
  }

  // write colored sequences (skip nulls so blank rows are left untouched)
  for (var rs = 0; rs < n; rs++) {
    if (richOut[rs][0]) sh.getRange(firstData + rs, seqCol).setRichTextValue(richOut[rs][0]);
  }

  // write bulk property columns
  sh.getRange(firstData, propCols[0], n, 1).setValues(piOut);
  sh.getRange(firstData, propCols[1], n, 1).setValues(mwOut);
  for (var re = 0; re < n; re++) {
    if (extOut[re][0])  sh.getRange(firstData + re, propCols[2]).setRichTextValue(extOut[re][0]);
    if (a280Out[re][0]) sh.getRange(firstData + re, propCols[3]).setRichTextValue(a280Out[re][0]);
  }

  // left-align and wrap text across all used columns
  sh.getDataRange().setHorizontalAlignment('left').setWrap(true);

  SpreadsheetApp.getActiveSpreadsheet().toast('Annotated ' + n + ' rows.', 'CDR + properties done', 5);
}


// =============================================================================
//  CDR cell builder
// =============================================================================

/**
 * Build a rich-text cell for one CDR: the loop residues (CDR color, bold) on
 * the first line, and a compact grey stats line below (net charge + counts).
 * Returns null for an empty loop so the cell is left blank.
 */
function buildCdrCell(loop, color) {
  if (!loop) return null;
  var stats = cdrStats(loop);
  var line2 = 'q' + signed(round(stats.netCharge, 1)) +
              '  φ' + stats.hydrophobic +   // phi = hydrophobic
              ' · pol' + stats.polar +       // middot separators
              ' · chg' + stats.charged;
  var text = loop + '\n' + line2;
  var b = SpreadsheetApp.newRichTextValue().setText(text);

  var resStyle = SpreadsheetApp.newTextStyle().setForegroundColor(color);
  if (BOLD_CDRS) resStyle.setBold(true);
  b.setTextStyle(0, loop.length, resStyle.build());

  var statStyle = SpreadsheetApp.newTextStyle()
    .setForegroundColor(STATS_COLOR).setBold(false).setFontSize(STATS_SIZE).build();
  b.setTextStyle(loop.length + 1, text.length, statStyle);
  return b.build();
}

/** Two grey lines stacked in one cell (used for ox/red extinction & A280). */
function buildTwoLineCell(line1, line2) {
  var text = line1 + '\n' + line2;
  var b = SpreadsheetApp.newRichTextValue().setText(text);
  b.setTextStyle(0, text.length,
    SpreadsheetApp.newTextStyle().setForegroundColor('#3C3C3C').build());
  return b.build();
}

/** Net charge (pH 7.4, side chains only) + hydrophobic/polar/charged counts. */
function cdrStats(loop) {
  var h = 0, p = 0, ch = 0;
  for (var i = 0; i < loop.length; i++) {
    var a = loop.charAt(i);
    if (HYDROPHOBIC.indexOf(a) >= 0) h++;
    else if (CHARGED.indexOf(a) >= 0) ch++;
    else if (POLAR.indexOf(a) >= 0) p++;
  }
  return { netCharge: chargeAtPH(loop, CDR_NET_CHARGE_PH, false),
           hydrophobic: h, polar: p, charged: ch };
}


// =============================================================================
//  Property math (mirrors ExPASy ProtParam / BioPython)
// =============================================================================

function molWeight(s) {
  var m = WATER;
  for (var i = 0; i < s.length; i++) { var a = AA_MASS[s.charAt(i)]; if (a != null) m += a; }
  return s.length ? m : 0;
}

function extinction(s) {
  var y = 0, w = 0, c = 0;
  for (var i = 0; i < s.length; i++) {
    var a = s.charAt(i);
    if (a === 'Y') y++; else if (a === 'W') w++; else if (a === 'C') c++;
  }
  var red = y * 1490 + w * 5500;
  return { red: red, ox: red + Math.floor(c / 2) * 125 };
}

/**
 * Net charge at a given pH via Henderson-Hasselbalch.
 * useTermini=true adds the (terminus-aware) alpha-amino / alpha-carboxyl groups
 * — appropriate for a whole chain; false = side chains only (for CDR fragments).
 */
function chargeAtPH(s, pH, useTermini) {
  var cnt = {}, i, a;
  for (i = 0; i < s.length; i++) { a = s.charAt(i); cnt[a] = (cnt[a] || 0) + 1; }
  function nPos(pK) { return 1 / (Math.pow(10, pH - pK) + 1); }
  function nNeg(pK) { return 1 / (Math.pow(10, pK - pH) + 1); }

  var q = 0;
  q += (cnt.K || 0) * nPos(POS_PK.K);
  q += (cnt.R || 0) * nPos(POS_PK.R);
  q += (cnt.H || 0) * nPos(POS_PK.H);
  q -= (cnt.D || 0) * nNeg(NEG_PK.D);
  q -= (cnt.E || 0) * nNeg(NEG_PK.E);
  q -= (cnt.C || 0) * nNeg(NEG_PK.C);
  q -= (cnt.Y || 0) * nNeg(NEG_PK.Y);

  if (useTermini && s.length) {
    var nt = PK_NTERM[s.charAt(0)]; if (nt == null) nt = POS_PK.Nterm;
    var ct = PK_CTERM[s.charAt(s.length - 1)]; if (ct == null) ct = NEG_PK.Cterm;
    q += nPos(nt);
    q -= nNeg(ct);
  }
  return q;
}

/** Isoelectric point: bisection on chargeAtPH (terminus-aware), [0,14]. */
function isoelectricPoint(s) {
  if (!s.length) return 0;
  var lo = 0, hi = 14, pH = 7;
  for (var i = 0; i < 60; i++) {
    pH = (lo + hi) / 2;
    if (chargeAtPH(s, pH, true) > 0) lo = pH; else hi = pH;
  }
  return (lo + hi) / 2;
}


// =============================================================================
//  small helpers
// =============================================================================

function round(x, d) { var f = Math.pow(10, d); return Math.round(x * f) / f; }
function signed(x)   { return (x >= 0 ? '+' : '') + x; }


// =============================================================================
//  CDR boundary finder (unchanged conserved-residue anchoring)
// =============================================================================

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
