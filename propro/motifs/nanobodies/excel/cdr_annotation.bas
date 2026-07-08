Attribute VB_Name = "CdrAnnotation"
' =============================================================================
'  Nanobody (VHH) CDR annotation + property summary for Microsoft Excel (VBA).
'  Part of propro (propro.motifs.nanobodies). Excel equivalent of the Google
'  Sheets script cdr_annotation.gs in ../gscripts/. See README.md in this folder.
'
'  Works in Excel for Windows AND Excel for Mac: no VBScript.RegExp dependency
'  (the CDR anchor logic is implemented with plain string scans).
'
'  What it does on the "nanobodies" worksheet, in one run of
'  AnnotateNanobodyCDRs:
'    1. Reads each sequence from the "AA Sequences" column (tolerant to common
'       header spellings, e.g. "Sequence", "AA Seq").
'    2. Extracts IMGT CDR1/CDR2/CDR3 into the "CDR1"/"CDR2"/"CDR3" columns,
'       each colored (CDR1 red, CDR2 green, CDR3 blue). Below the residues of
'       each CDR cell it adds a compact grey stats line:
'           q<±charge>  phi<n> . pol<n> . chg<n>
'       = net charge at pH 7.4 and counts of hydrophobic / polar / charged
'       side chains for that loop.
'    3. Recolors the AA-sequence cell so each CDR shows in its CDR color.
'    4. Writes whole-sequence bulk properties to their own columns (auto-created
'       if missing): pI, MW (kDa), extinction coefficient (M-1 cm-1) and A280 at
'       1 mg/mL, each given for the reduced ("red:") and oxidized ("ox:",
'       disulfides formed) state.
'
'  Property math mirrors ExPASy ProtParam / BioPython (verified numerically):
'    MW   = sum of average residue masses + one water.
'    pI   = Bjellqvist pKa set, terminus-aware, solved by bisection.
'    ext  = Tyr*1490 + Trp*5500 (reduced); + (Cys\2)*125 for cystines (oxidized).
'    A280 = ext / MW (absorbance of a 1 mg/mL = 0.1% solution).
'  Per-CDR net charge uses the same side-chain pKa at pH 7.4 with NO terminal
'  groups (a CDR is an internal fragment, so its ends are not real termini).
'
'  HOW TO RUN:
'    Windows: Alt+F11 to open the VBA editor.
'    Mac:     Tools > Macro > Visual Basic Editor.
'    Then: Insert > Module, paste this file, and run AnnotateNanobodyCDRs
'    (F5, or Developer > Macros). Save the workbook as .xlsm to keep the macro.
' =============================================================================
Option Explicit

' ---- settings ----
Private Const SHEET_NAME As String = "nanobodies"
Private Const BOLD_CDRS As Boolean = True
Private Const STATS_SIZE As Long = 8
Private Const CDR_NET_CHARGE_PH As Double = 7.4

' colors (hex, no leading #)
Private Const HEX_CDR1 As String = "C0392B"   ' red
Private Const HEX_CDR2 As String = "1E8449"   ' green
Private Const HEX_CDR3 As String = "1F4E9C"   ' blue
Private Const HEX_STATS As String = "7F7F7F"  ' grey (per-CDR stats line)
Private Const HEX_TWOLINE As String = "3C3C3C" ' dark grey (ext / A280 cells)

' ---- side-chain classification for per-CDR counts ----
Private Const HYDROPHOBIC As String = "AVLIMFWYC"
Private Const POLAR As String = "STNQHG"
Private Const CHARGED As String = "DEKR"

' ---- result containers ----
Private Type TCdr
    CDR1 As String: CDR2 As String: CDR3 As String
    r1s As Long: r1e As Long: has1 As Boolean
    r2s As Long: r2e As Long: has2 As Boolean
    r3s As Long: r3e As Long: has3 As Boolean
End Type

Private Type TStats
    netCharge As Double
    hyd As Long: pol As Long: chg As Long
End Type


' =============================================================================
'  Main entry point
' =============================================================================
Public Sub AnnotateNanobodyCDRs()
    Dim ws As Worksheet
    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets(SHEET_NAME)
    On Error GoTo 0
    If ws Is Nothing Then
        MsgBox "Worksheet """ & SHEET_NAME & """ not found.", vbExclamation
        Exit Sub
    End If

    Dim lastRow As Long, lastCol As Long
    With ws.UsedRange
        lastRow = .Row + .Rows.Count - 1
        lastCol = .Column + .Columns.Count - 1
    End With
    If lastRow < 2 Then
        MsgBox "No data rows found.", vbExclamation
        Exit Sub
    End If

    ' --- locate header row + sequence column ---
    Dim headerRow As Long, seqCol As Long
    Dim headers() As String
    headerRow = FindHeaderRow(ws, lastRow, lastCol, seqCol, headers)
    If headerRow = 0 Then
        MsgBox "Could not find a sequence header (e.g. 'AA Sequences') in the first 15 rows.", vbExclamation
        Exit Sub
    End If

    ' --- CDR columns (must exist) ---
    Dim cdrCols(1 To 3) As Long
    Dim cdrNames As Variant: cdrNames = Array("CDR1", "CDR2", "CDR3")
    Dim i As Long
    For i = 1 To 3
        cdrCols(i) = ColOf(headers, CStr(cdrNames(i - 1)))
        If cdrCols(i) = 0 Then
            MsgBox "Column """ & cdrNames(i - 1) & """ not found in the header row.", vbExclamation
            Exit Sub
        End If
    Next i

    ' --- property columns (auto-create any that are missing) ---
    Dim propNames As Variant
    propNames = Array("pI", "MW (kDa)", "Ext coeff (M-1 cm-1)", "A280 (1 mg/mL)")
    Dim propCols(0 To 3) As Long, nextCol As Long
    nextCol = lastCol
    For i = 0 To 3
        propCols(i) = ColOf(headers, CStr(propNames(i)))
        If propCols(i) = 0 Then
            nextCol = nextCol + 1
            ws.Cells(headerRow, nextCol).Value = propNames(i)
            ws.Cells(headerRow, nextCol).Font.Bold = True
            propCols(i) = nextCol
            ReDim Preserve headers(1 To nextCol)
            headers(nextCol) = Norm(CStr(propNames(i)))
        End If
    Next i

    ' speed up
    Dim prevScreen As Boolean, prevCalc As XlCalculation
    prevScreen = Application.ScreenUpdating
    prevCalc = Application.Calculation
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual

    Dim firstData As Long, r As Long
    firstData = headerRow + 1

    For r = firstData To lastRow
        Dim raw As String, seq As String
        raw = CStr(ws.Cells(r, seqCol).Value)
        seq = CleanSeq(raw)
        If Len(seq) = 0 Then GoTo NextRow

        Dim f As TCdr
        f = FindCDRs(seq)

        ' --- per-CDR cells: residues (colored) + grey stats line below ---
        WriteCdrCell ws.Cells(r, cdrCols(1)), f.CDR1, HEX_CDR1
        WriteCdrCell ws.Cells(r, cdrCols(2)), f.CDR2, HEX_CDR2
        WriteCdrCell ws.Cells(r, cdrCols(3)), f.CDR3, HEX_CDR3

        ' --- recolor the full sequence in place ---
        Dim sc As Range
        Set sc = ws.Cells(r, seqCol)
        sc.Value = seq
        If f.has1 Then ColorRange sc, f.r1s, f.r1e, HEX_CDR1
        If f.has2 Then ColorRange sc, f.r2s, f.r2e, HEX_CDR2
        If f.has3 Then ColorRange sc, f.r3s, f.r3e, HEX_CDR3

        ' --- whole-sequence bulk properties (standard 20 residues only) ---
        Dim clean As String, mw As Double, extRed As Long, extOx As Long
        clean = CleanStd(seq)
        mw = MolWeight(clean)
        extRed = ExtinctionRed(clean)
        extOx = ExtinctionOx(clean)
        ws.Cells(r, propCols(0)).Value = Round2(IsoelectricPoint(clean), 2)
        ws.Cells(r, propCols(1)).Value = Round2(mw / 1000#, 2)
        WriteTwoLine ws.Cells(r, propCols(2)), "ox: " & extOx, "red: " & extRed
        Dim aOx As Double, aRed As Double
        If mw > 0 Then aOx = extOx / mw: aRed = extRed / mw
        WriteTwoLine ws.Cells(r, propCols(3)), _
            "ox: " & NumStr(Round2(aOx, 3)), "red: " & NumStr(Round2(aRed, 3))
NextRow:
    Next r

    ' left-align + wrap the used range
    With ws.UsedRange
        .HorizontalAlignment = xlLeft
        .WrapText = True
    End With

    Application.Calculation = prevCalc
    Application.ScreenUpdating = prevScreen
    MsgBox "Annotated " & (lastRow - headerRow) & " rows.", vbInformation, "CDR + properties done"
End Sub


' =============================================================================
'  Cell writers (rich formatting)
' =============================================================================

' One CDR cell: loop residues (CDR color, bold, Courier) + grey stats line below.
Private Sub WriteCdrCell(cell As Range, loop_ As String, hexColor As String)
    If Len(loop_) = 0 Then Exit Sub
    Dim st As TStats
    st = CdrStats(loop_)
    Dim line2 As String
    line2 = "q" & Signed(Round2(st.netCharge, 1)) & "  " & _
            ChrW(966) & st.hyd & " " & ChrW(183) & " pol" & st.pol & _
            " " & ChrW(183) & " chg" & st.chg   ' ChrW(966)=phi, ChrW(183)=middot

    cell.Value = loop_ & vbLf & line2
    cell.Font.Name = "Courier New"
    cell.WrapText = True

    ' residues
    cell.Characters(1, Len(loop_)).Font.Color = HexColor(hexColor)
    If BOLD_CDRS Then cell.Characters(1, Len(loop_)).Font.Bold = True

    ' grey stats (starts after residues + the newline char)
    Dim sPos As Long
    sPos = Len(loop_) + 2
    With cell.Characters(sPos, Len(line2)).Font
        .Color = HexColor(HEX_STATS)
        .Bold = False
        .Size = STATS_SIZE
    End With
End Sub

' Two grey lines stacked in one cell (ext / A280 cells).
Private Sub WriteTwoLine(cell As Range, line1 As String, line2 As String)
    cell.Value = line1 & vbLf & line2
    cell.WrapText = True
    cell.Font.Color = HexColor(HEX_TWOLINE)
End Sub

' Color a [start,end) 0-based residue range in a cell that already holds text.
Private Sub ColorRange(cell As Range, startPos As Long, endPos As Long, hexColor As String)
    If endPos <= startPos Then Exit Sub
    cell.Characters(startPos + 1, endPos - startPos).Font.Color = HexColor(hexColor)
    If BOLD_CDRS Then cell.Characters(startPos + 1, endPos - startPos).Font.Bold = True
End Sub


' =============================================================================
'  Per-CDR stats
' =============================================================================
Private Function CdrStats(loop_ As String) As TStats
    Dim i As Long, a As String, h As Long, p As Long, c As Long
    For i = 1 To Len(loop_)
        a = Mid$(loop_, i, 1)
        If InStr(HYDROPHOBIC, a) > 0 Then
            h = h + 1
        ElseIf InStr(CHARGED, a) > 0 Then
            c = c + 1
        ElseIf InStr(POLAR, a) > 0 Then
            p = p + 1
        End If
    Next i
    CdrStats.hyd = h: CdrStats.pol = p: CdrStats.chg = c
    CdrStats.netCharge = ChargeAtPH(loop_, CDR_NET_CHARGE_PH, False)
End Function


' =============================================================================
'  Property math (mirrors ExPASy ProtParam / BioPython)
' =============================================================================
Private Function MolWeight(s As String) As Double
    If Len(s) = 0 Then Exit Function
    Dim i As Long, m As Double
    m = 18.01524                     ' one water
    For i = 1 To Len(s)
        m = m + AaMass(Mid$(s, i, 1))
    Next i
    MolWeight = m
End Function

Private Function ExtinctionRed(s As String) As Long
    ExtinctionRed = CountChar(s, "Y") * 1490 + CountChar(s, "W") * 5500
End Function

Private Function ExtinctionOx(s As String) As Long
    ExtinctionOx = ExtinctionRed(s) + (CountChar(s, "C") \ 2) * 125
End Function

' Net charge at a given pH (Henderson-Hasselbalch).
' useTermini=True adds terminus-aware alpha-amino / alpha-carboxyl groups.
Private Function ChargeAtPH(s As String, pH As Double, useTermini As Boolean) As Double
    If Len(s) = 0 Then Exit Function
    Dim q As Double
    q = CountChar(s, "K") * NPos(pH, 10#) _
      + CountChar(s, "R") * NPos(pH, 12#) _
      + CountChar(s, "H") * NPos(pH, 5.98) _
      - CountChar(s, "D") * NNeg(pH, 4.05) _
      - CountChar(s, "E") * NNeg(pH, 4.45) _
      - CountChar(s, "C") * NNeg(pH, 9#) _
      - CountChar(s, "Y") * NNeg(pH, 10#)
    If useTermini Then
        q = q + NPos(pH, PkNterm(Left$(s, 1)))
        q = q - NNeg(pH, PkCterm(Right$(s, 1)))
    End If
    ChargeAtPH = q
End Function

Private Function IsoelectricPoint(s As String) As Double
    If Len(s) = 0 Then Exit Function
    Dim lo As Double, hi As Double, pH As Double, i As Long
    lo = 0#: hi = 14#
    For i = 1 To 60
        pH = (lo + hi) / 2#
        If ChargeAtPH(s, pH, True) > 0 Then lo = pH Else hi = pH
    Next i
    IsoelectricPoint = (lo + hi) / 2#
End Function

Private Function NPos(pH As Double, pK As Double) As Double
    NPos = 1# / (10# ^ (pH - pK) + 1#)
End Function
Private Function NNeg(pH As Double, pK As Double) As Double
    NNeg = 1# / (10# ^ (pK - pH) + 1#)
End Function

' Bjellqvist terminus pKa (default N-term 7.5, default C-term 3.55).
Private Function PkNterm(a As String) As Double
    Select Case a
        Case "A": PkNterm = 7.59
        Case "M": PkNterm = 7#
        Case "S": PkNterm = 6.93
        Case "P": PkNterm = 8.36
        Case "T": PkNterm = 6.82
        Case "V": PkNterm = 7.44
        Case "E": PkNterm = 7.7
        Case Else: PkNterm = 7.5
    End Select
End Function
Private Function PkCterm(a As String) As Double
    Select Case a
        Case "D": PkCterm = 4.55
        Case "E": PkCterm = 4.75
        Case Else: PkCterm = 3.55
    End Select
End Function

' Average residue masses (Da); 0 for anything non-standard.
Private Function AaMass(a As String) As Double
    Select Case a
        Case "G": AaMass = 57.0513
        Case "A": AaMass = 71.0788
        Case "S": AaMass = 87.0782
        Case "P": AaMass = 97.1167
        Case "V": AaMass = 99.1326
        Case "T": AaMass = 101.1051
        Case "C": AaMass = 103.1388
        Case "L": AaMass = 113.1594
        Case "I": AaMass = 113.1594
        Case "N": AaMass = 114.1038
        Case "D": AaMass = 115.0886
        Case "Q": AaMass = 128.1307
        Case "K": AaMass = 128.1741
        Case "E": AaMass = 129.1155
        Case "M": AaMass = 131.1926
        Case "H": AaMass = 137.1411
        Case "F": AaMass = 147.1766
        Case "R": AaMass = 156.1875
        Case "Y": AaMass = 163.176
        Case "W": AaMass = 186.2132
        Case Else: AaMass = 0#
    End Select
End Function


' =============================================================================
'  CDR boundary finder (regex-free; matches cdr_annotation.gs output)
' =============================================================================
Private Function FindCDRs(s As String) As TCdr
    Dim R As TCdr
    Dim c1 As Long
    c1 = InStr(s, "C") - 1                 ' 0-based Cys23; -1 if absent
    If c1 < 0 Then FindCDRs = R: Exit Function

    ' FR2 Trp41: W then 0-2 residues then [RQK]; else first W
    Dim trp As Long
    trp = FindTrp41(s, c1 + 8)
    If trp < 0 Then trp = FindChar(s, "W", c1 + 8)

    ' FR4 WGxG (last WG?[GQ]); fallback W[GA]?[GQ]
    Dim wg As Long
    wg = FindWGxGLast(s)
    If wg < 0 Then wg = FindWGxGFallback(s)

    ' Cys104: earliest Cys 3..45 upstream of WGxG, preferring aromatic context
    Dim c2 As Long, i As Long
    c2 = -1
    Dim bestArom As Long, bestAny As Long
    bestArom = -1: bestAny = -1
    For i = c1 + 1 To Len(s) - 1
        If Mid$(s, i + 1, 1) = "C" Then
            If (wg - i) >= 3 And (wg - i) <= 45 Then
                If bestAny = -1 Then bestAny = i
                Dim aromCtx As Boolean
                aromCtx = (i >= 2 And InStr("YFWH", CharAt(s, i - 2)) > 0) _
                       Or (i >= 1 And InStr("YF", CharAt(s, i - 1)) > 0)
                If aromCtx And bestArom = -1 Then bestArom = i
            End If
        End If
    Next i
    If bestArom >= 0 Then c2 = bestArom ElseIf bestAny >= 0 Then c2 = bestAny

    ' CDR1: Cys23+4 .. Trp41-2
    If trp <> -1 And (trp - 2) > (c1 + 4) Then
        R.r1s = c1 + 4: R.r1e = trp - 2: R.has1 = True
        R.CDR1 = Mid$(s, R.r1s + 1, R.r1e - R.r1s)
    End If

    ' CDR3: Cys104+1 .. WGxG
    If c2 <> -1 And wg <> -1 And wg > (c2 + 1) Then
        R.r3s = c2 + 1: R.r3e = wg: R.has3 = True
        R.CDR3 = Mid$(s, R.r3s + 1, R.r3e - R.r3s)
    End If

    ' CDR2: Trp41+15 .. (conserved FR3 motif - 8)
    If trp <> -1 Then
        Dim st As Long, subEnd As Long, sub_ As String, ci As Long, endPos As Long
        st = trp + 15
        subEnd = IIf(c2 > 0, c2, Len(s))
        If st < subEnd Then
            sub_ = Mid$(s, st + 1, subEnd - st)
        Else
            sub_ = ""
        End If
        ci = FindCdr2Core(sub_)
        If ci >= 0 And (ci - 8) > 0 Then endPos = st + ci - 8 Else endPos = st + 8
        If endPos > st Then
            R.r2s = st: R.r2e = endPos: R.has2 = True
            R.CDR2 = Mid$(s, R.r2s + 1, R.r2e - R.r2s)
        End If
    End If

    FindCDRs = R
End Function

' W then 0-2 residues then [RQK]; returns 0-based index of W, or -1.
Private Function FindTrp41(s As String, fromIdx As Long) As Long
    Dim i As Long, g As Long
    For i = IIf(fromIdx < 0, 0, fromIdx) To Len(s) - 1
        If Mid$(s, i + 1, 1) = "W" Then
            For g = 1 To 3
                If (i + g) <= (Len(s) - 1) Then
                    If InStr("RQK", Mid$(s, i + g + 1, 1)) > 0 Then FindTrp41 = i: Exit Function
                End If
            Next g
        End If
    Next i
    FindTrp41 = -1
End Function

' Last occurrence of W G ? [GQ]; 0-based index of W, or -1.
Private Function FindWGxGLast(s As String) As Long
    Dim i As Long, last As Long
    last = -1
    For i = 0 To Len(s) - 4
        If Mid$(s, i + 1, 1) = "W" And Mid$(s, i + 2, 1) = "G" _
           And InStr("GQ", Mid$(s, i + 4, 1)) > 0 Then last = i
    Next i
    FindWGxGLast = last
End Function

' First occurrence of W [GA] ? [GQ]; 0-based index of W, or -1.
Private Function FindWGxGFallback(s As String) As Long
    Dim i As Long
    For i = 0 To Len(s) - 4
        If Mid$(s, i + 1, 1) = "W" And InStr("GA", Mid$(s, i + 2, 1)) > 0 _
           And InStr("GQ", Mid$(s, i + 4, 1)) > 0 Then FindWGxGFallback = i: Exit Function
    Next i
    FindWGxGFallback = -1
End Function

' Earliest [KR][FLY][ST][ILV][ST] in sub; 0-based index, or -1.
Private Function FindCdr2Core(sub_ As String) As Long
    Dim i As Long
    For i = 0 To Len(sub_) - 5
        If InStr("KR", Mid$(sub_, i + 1, 1)) > 0 _
           And InStr("FLY", Mid$(sub_, i + 2, 1)) > 0 _
           And InStr("ST", Mid$(sub_, i + 3, 1)) > 0 _
           And InStr("ILV", Mid$(sub_, i + 4, 1)) > 0 _
           And InStr("ST", Mid$(sub_, i + 5, 1)) > 0 Then FindCdr2Core = i: Exit Function
    Next i
    FindCdr2Core = -1
End Function


' =============================================================================
'  Header handling
' =============================================================================
Private Function FindHeaderRow(ws As Worksheet, lastRow As Long, lastCol As Long, _
                               ByRef seqCol As Long, ByRef headers() As String) As Long
    Dim seqKeys As Variant
    seqKeys = Array("aasequences", "aasequence", "aaseq", "aminoacidsequence", "sequence", "seq")
    Dim scanN As Long
    scanN = IIf(lastRow < 15, lastRow, 15)

    Dim hr As Long, c As Long, sc As Long, k As Long
    For hr = 1 To scanN
        sc = 0
        Dim rowNorm() As String
        ReDim rowNorm(1 To lastCol)
        For c = 1 To lastCol
            rowNorm(c) = Norm(CStr(ws.Cells(hr, c).Value))
        Next c
        ' exact key match
        For c = 1 To lastCol
            For k = LBound(seqKeys) To UBound(seqKeys)
                If rowNorm(c) = seqKeys(k) Then sc = c: Exit For
            Next k
            If sc > 0 Then Exit For
        Next c
        ' fallback: contains "sequence" / "aaseq"
        If sc = 0 Then
            For c = 1 To lastCol
                If InStr(rowNorm(c), "sequence") > 0 Or InStr(rowNorm(c), "aaseq") > 0 Then sc = c: Exit For
            Next c
        End If
        If sc > 0 Then
            seqCol = sc
            headers = rowNorm
            FindHeaderRow = hr
            Exit Function
        End If
    Next hr
    FindHeaderRow = 0
End Function

' Column index (1-based) whose normalized header equals Norm(key); 0 if absent.
Private Function ColOf(headers() As String, key As String) As Long
    Dim c As Long, nk As String
    nk = Norm(key)
    For c = LBound(headers) To UBound(headers)
        If headers(c) = nk Then ColOf = c: Exit Function
    Next c
    ColOf = 0
End Function


' =============================================================================
'  Small helpers
' =============================================================================

' Lowercase + strip everything except a-z0-9.
Private Function Norm(h As String) As String
    Dim i As Long, ch As String, out As String, low As String
    low = LCase$(h)
    For i = 1 To Len(low)
        ch = Mid$(low, i, 1)
        If (ch >= "a" And ch <= "z") Or (ch >= "0" And ch <= "9") Then out = out & ch
    Next i
    Norm = out
End Function

' Keep only A-Z (uppercased) - used for CDR finding + sequence coloring.
Private Function CleanSeq(raw As String) As String
    Dim i As Long, ch As String, up As String, out As String
    up = UCase$(raw)
    For i = 1 To Len(up)
        ch = Mid$(up, i, 1)
        If ch >= "A" And ch <= "Z" Then out = out & ch
    Next i
    CleanSeq = out
End Function

' Keep only the standard 20 amino acids - used for numeric properties.
Private Function CleanStd(s As String) As String
    Dim i As Long, ch As String, out As String
    For i = 1 To Len(s)
        ch = Mid$(s, i, 1)
        If InStr("ACDEFGHIKLMNPQRSTVWY", ch) > 0 Then out = out & ch
    Next i
    CleanStd = out
End Function

Private Function CountChar(s As String, ch As String) As Long
    Dim i As Long, n As Long
    For i = 1 To Len(s)
        If Mid$(s, i, 1) = ch Then n = n + 1
    Next i
    CountChar = n
End Function

' 0-based char access; "" if out of range.
Private Function CharAt(s As String, i As Long) As String
    If i < 0 Or i > Len(s) - 1 Then CharAt = "" Else CharAt = Mid$(s, i + 1, 1)
End Function

' Find 0-based index of single char ch from 0-based fromIdx; -1 if absent.
Private Function FindChar(s As String, ch As String, fromIdx As Long) As Long
    Dim p As Long
    p = InStr(IIf(fromIdx < 0, 1, fromIdx + 1), s, ch)
    FindChar = IIf(p = 0, -1, p - 1)
End Function

' Round half-away-from-zero to d decimals (avoids VBA banker's rounding surprises).
Private Function Round2(x As Double, d As Long) As Double
    Dim f As Double
    f = 10# ^ d
    Round2 = Int(Abs(x) * f + 0.5) / f * Sgn2(x)
End Function
Private Function Sgn2(x As Double) As Double
    Sgn2 = IIf(x < 0, -1#, 1#)
End Function

' Number -> string with "." decimal separator regardless of locale.
Private Function NumStr(x As Double) As String
    NumStr = Replace(CStr(x), ",", ".")
End Function

' Signed number string: "+3", "-1", "+0.8".
Private Function Signed(x As Double) As String
    Signed = IIf(x >= 0, "+", "") & NumStr(x)
End Function

' Hex "RRGGBB" -> VBA color Long (RGB).
Private Function HexColor(h As String) As Long
    Dim rr As Long, gg As Long, bb As Long
    rr = CLng("&H" & Mid$(h, 1, 2))
    gg = CLng("&H" & Mid$(h, 3, 2))
    bb = CLng("&H" & Mid$(h, 5, 2))
    HexColor = RGB(rr, gg, bb)
End Function
