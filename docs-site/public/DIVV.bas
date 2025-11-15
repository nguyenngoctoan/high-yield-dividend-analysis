Attribute VB_Name = "DivvAPI"
'
' DIVV() - Custom Excel function for dividend data
'
' A drop-in replacement for stock data functions with superior dividend data.
'
' Installation:
'   1. Open Excel
'   2. Press Alt+F11 to open VBA Editor
'   3. Go to Insert > Module
'   4. Paste this entire code
'   5. Update API_BASE_URL constant below
'   6. Save and close VBA Editor
'   7. Start using =DIVV() in your spreadsheet!
'
' Examples:
'   =DIVV("AAPL", "price")              → Current price
'   =DIVV("AAPL", "dividendYield")      → Dividend yield
'   =DIVV("AAPL", "yearHigh")           → 52-week high
'
' Version: 1.0.0
' Last Updated: 2025-11-14
'

Option Explicit

' ============================================================================
' CONFIGURATION
' ============================================================================

' Base URL for Divv API
' Update this to your production API endpoint
Const API_BASE_URL As String = "http://localhost:8000"

' API Key (optional for now, required for production)
Const API_KEY As String = ""

' Cache duration in minutes
Const CACHE_DURATION_MINUTES As Integer = 5

' Tier restrictions
' Free tier: only price and dividendYield
' Paid tiers: all attributes
' Set to "free" or "paid" based on your subscription
Const ACCOUNT_TIER As String = "free"

' ============================================================================
' MAIN FUNCTION
' ============================================================================

'
' Main DIVV function - entry point for Excel
'
Public Function DIVV(symbol As String, Optional attribute As String = "") As Variant
    On Error GoTo ErrorHandler

    ' Input validation
    If Len(Trim(symbol)) = 0 Then
        DIVV = CVErr(xlErrValue)
        Exit Function
    End If

    symbol = UCase(Trim(symbol))

    ' Check cache first
    Dim cacheKey As String
    cacheKey = "DIVV_" & symbol

    Dim cachedData As String
    cachedData = GetFromCache(cacheKey)

    Dim jsonData As Object

    If Len(cachedData) > 0 Then
        ' Parse cached JSON
        Set jsonData = ParseJSON(cachedData)
    Else
        ' Fetch from API
        Dim apiResponse As String
        apiResponse = FetchStockData(symbol)

        If Len(apiResponse) = 0 Then
            DIVV = CVErr(xlErrNA)
            Exit Function
        End If

        ' Parse and cache
        Set jsonData = ParseJSON(apiResponse)
        SaveToCache cacheKey, apiResponse
    End If

    ' Extract attribute
    If Len(attribute) = 0 Then
        ' Return all data as 2D array
        DIVV = FormatDataForExcel(jsonData)
    Else
        ' Return specific attribute
        DIVV = ExtractAttribute(jsonData, attribute)
    End If

    Exit Function

ErrorHandler:
    DIVV = CVErr(xlErrValue)
End Function

' ============================================================================
' API FUNCTIONS
' ============================================================================

'
' Fetch stock data from Divv API
'
Private Function FetchStockData(symbol As String) As String
    On Error GoTo ErrorHandler

    Dim url As String
    url = API_BASE_URL & "/v1/stocks/" & symbol & "/quote"

    ' Create HTTP request
    Dim http As Object
    Set http = CreateObject("MSXML2.XMLHTTP")

    ' Send request
    http.Open "GET", url, False
    http.setRequestHeader "Accept", "application/json"

    If Len(API_KEY) > 0 Then
        http.setRequestHeader "X-API-Key", API_KEY
    End If

    http.Send

    ' Check response
    If http.Status = 200 Then
        FetchStockData = http.responseText
    Else
        FetchStockData = ""
    End If

    Exit Function

ErrorHandler:
    FetchStockData = ""
End Function

' ============================================================================
' DATA EXTRACTION
' ============================================================================

'
' Extract specific attribute from JSON data
'
Private Function ExtractAttribute(jsonData As Object, attribute As String) As Variant
    On Error GoTo ErrorHandler

    ' Normalize attribute name
    Dim normalizedAttr As String
    normalizedAttr = NormalizeAttributeName(attribute)

    ' Check tier restrictions (free tier only gets price and dividend data)
    If ACCOUNT_TIER = "free" Then
        Dim allowedAttrs As Variant
        allowedAttrs = Array("price", "open", "dayHigh", "dayLow", "previousClose", "dividendYield", "dividendAmount")

        Dim isAllowed As Boolean
        isAllowed = False

        Dim i As Integer
        For i = LBound(allowedAttrs) To UBound(allowedAttrs)
            If normalizedAttr = allowedAttrs(i) Then
                isAllowed = True
                Exit For
            End If
        Next i

        If Not isAllowed Then
            ExtractAttribute = "#UPGRADE: Requires paid plan. Visit divv.com/pricing"
            Exit Function
        End If
    End If

    ' Try to get value
    Dim value As Variant

    If jsonData.Exists(normalizedAttr) Then
        value = jsonData(normalizedAttr)
    ElseIf jsonData.Exists(attribute) Then
        value = jsonData(attribute)
    Else
        ExtractAttribute = CVErr(xlErrNA)
        Exit Function
    End If

    ' Return value
    If IsNull(value) Or IsEmpty(value) Then
        ExtractAttribute = CVErr(xlErrNA)
    Else
        ExtractAttribute = value
    End If

    Exit Function

ErrorHandler:
    ExtractAttribute = CVErr(xlErrNA)
End Function

'
' Normalize attribute names
'
Private Function NormalizeAttributeName(attr As String) As String
    Dim normalized As String
    normalized = LCase(Replace(Replace(attr, "_", ""), " ", ""))

    ' Map GOOGLEFINANCE-style names to Divv names
    Select Case normalized
        Case "price": NormalizeAttributeName = "price"
        Case "priceopen": NormalizeAttributeName = "open"
        Case "high": NormalizeAttributeName = "dayHigh"
        Case "low": NormalizeAttributeName = "dayLow"
        Case "volume": NormalizeAttributeName = "volume"
        Case "marketcap": NormalizeAttributeName = "marketCap"
        Case "pe": NormalizeAttributeName = "peRatio"
        Case "eps": NormalizeAttributeName = "eps"
        Case "high52": NormalizeAttributeName = "yearHigh"
        Case "low52": NormalizeAttributeName = "yearLow"
        Case "change": NormalizeAttributeName = "change"
        Case "changepct": NormalizeAttributeName = "changePercent"
        Case "shares": NormalizeAttributeName = "sharesOutstanding"
        Case "avgvol": NormalizeAttributeName = "avgVolume"
        Case "sma50": NormalizeAttributeName = "priceAvg50"
        Case "sma200": NormalizeAttributeName = "priceAvg200"
        Case "dividendyield": NormalizeAttributeName = "dividendYield"
        Case "dividendamount": NormalizeAttributeName = "dividendAmount"
        Case Else: NormalizeAttributeName = attr
    End Select
End Function

'
' Format JSON data as 2D array for Excel
'
Private Function FormatDataForExcel(jsonData As Object) As Variant
    Dim data(1 To 23, 1 To 2) As Variant

    data(1, 1) = "Symbol": data(1, 2) = GetValue(jsonData, "symbol")
    data(2, 1) = "Price": data(2, 2) = GetValue(jsonData, "price")
    data(3, 1) = "Open": data(3, 2) = GetValue(jsonData, "open")
    data(4, 1) = "Day High": data(4, 2) = GetValue(jsonData, "dayHigh")
    data(5, 1) = "Day Low": data(5, 2) = GetValue(jsonData, "dayLow")
    data(6, 1) = "Previous Close": data(6, 2) = GetValue(jsonData, "previousClose")
    data(7, 1) = "Change": data(7, 2) = GetValue(jsonData, "change")
    data(8, 1) = "Change %": data(8, 2) = GetValue(jsonData, "changePercent")
    data(9, 1) = "Volume": data(9, 2) = GetValue(jsonData, "volume")
    data(10, 1) = "Avg Volume": data(10, 2) = GetValue(jsonData, "avgVolume")
    data(11, 1) = "52-Week High": data(11, 2) = GetValue(jsonData, "yearHigh")
    data(12, 1) = "52-Week Low": data(12, 2) = GetValue(jsonData, "yearLow")
    data(13, 1) = "50-Day MA": data(13, 2) = GetValue(jsonData, "priceAvg50")
    data(14, 1) = "200-Day MA": data(14, 2) = GetValue(jsonData, "priceAvg200")
    data(15, 1) = "Market Cap": data(15, 2) = GetValue(jsonData, "marketCap")
    data(16, 1) = "P/E Ratio": data(16, 2) = GetValue(jsonData, "peRatio")
    data(17, 1) = "EPS": data(17, 2) = GetValue(jsonData, "eps")
    data(18, 1) = "Shares Outstanding": data(18, 2) = GetValue(jsonData, "sharesOutstanding")
    data(19, 1) = "Dividend Yield": data(19, 2) = GetValue(jsonData, "dividendYield")
    data(20, 1) = "Dividend Amount": data(20, 2) = GetValue(jsonData, "dividendAmount")
    data(21, 1) = "Company": data(21, 2) = GetValue(jsonData, "company")
    data(22, 1) = "Exchange": data(22, 2) = GetValue(jsonData, "exchange")
    data(23, 1) = "Sector": data(23, 2) = GetValue(jsonData, "sector")

    FormatDataForExcel = data
End Function

'
' Helper to get value from JSON object
'
Private Function GetValue(jsonData As Object, key As String) As Variant
    If jsonData.Exists(key) Then
        If IsNull(jsonData(key)) Or IsEmpty(jsonData(key)) Then
            GetValue = "N/A"
        Else
            GetValue = jsonData(key)
        End If
    Else
        GetValue = "N/A"
    End If
End Function

' ============================================================================
' CACHE MANAGEMENT (Simple worksheet-based cache)
' ============================================================================

'
' Get data from cache worksheet
'
Private Function GetFromCache(key As String) As String
    On Error Resume Next

    Dim ws As Worksheet
    Set ws = GetCacheWorksheet

    If ws Is Nothing Then
        GetFromCache = ""
        Exit Function
    End If

    Dim lastRow As Long
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row

    Dim i As Long
    For i = 2 To lastRow
        If ws.Cells(i, 1).value = key Then
            ' Check if expired
            Dim cacheTime As Date
            cacheTime = ws.Cells(i, 3).value

            If DateDiff("n", cacheTime, Now) < CACHE_DURATION_MINUTES Then
                GetFromCache = ws.Cells(i, 2).value
                Exit Function
            Else
                ' Expired - delete row
                ws.Rows(i).Delete
                Exit For
            End If
        End If
    Next i

    GetFromCache = ""
End Function

'
' Save data to cache worksheet
'
Private Sub SaveToCache(key As String, data As String)
    On Error Resume Next

    Dim ws As Worksheet
    Set ws = GetCacheWorksheet

    If ws Is Nothing Then Exit Sub

    Dim lastRow As Long
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row + 1

    ws.Cells(lastRow, 1).value = key
    ws.Cells(lastRow, 2).value = data
    ws.Cells(lastRow, 3).value = Now
End Sub

'
' Get or create cache worksheet
'
Private Function GetCacheWorksheet() As Worksheet
    On Error Resume Next

    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets("_DivvCache")

    If ws Is Nothing Then
        ' Create cache worksheet
        Set ws = ThisWorkbook.Sheets.Add
        ws.Name = "_DivvCache"
        ws.Visible = xlSheetVeryHidden

        ' Add headers
        ws.Cells(1, 1).value = "Key"
        ws.Cells(1, 2).value = "Data"
        ws.Cells(1, 3).value = "Timestamp"
    End If

    Set GetCacheWorksheet = ws
End Function

' ============================================================================
' JSON PARSER (Simple implementation)
' ============================================================================

'
' Simple JSON parser
' Returns Dictionary object with key-value pairs
'
Private Function ParseJSON(jsonString As String) As Object
    On Error GoTo ErrorHandler

    ' Use native JSON parsing if available (Excel 2016+)
    Set ParseJSON = CreateObject("Scripting.Dictionary")

    ' Remove outer braces
    jsonString = Trim(jsonString)
    If Left(jsonString, 1) = "{" Then jsonString = Mid(jsonString, 2)
    If Right(jsonString, 1) = "}" Then jsonString = Left(jsonString, Len(jsonString) - 1)

    ' Split by comma (simple parser - doesn't handle nested objects)
    Dim pairs() As String
    pairs = Split(jsonString, ",")

    Dim pair As Variant
    For Each pair In pairs
        Dim keyValue() As String
        keyValue = Split(pair, ":")

        If UBound(keyValue) >= 1 Then
            Dim key As String
            Dim value As String

            key = Trim(Replace(Replace(keyValue(0), """", ""), "'", ""))
            value = Trim(Replace(Replace(keyValue(1), """", ""), "'", ""))

            ' Try to convert to number if possible
            If IsNumeric(value) Then
                ParseJSON.Add key, CDbl(value)
            ElseIf LCase(value) = "null" Then
                ParseJSON.Add key, Null
            Else
                ParseJSON.Add key, value
            End If
        End If
    Next pair

    Exit Function

ErrorHandler:
    Set ParseJSON = Nothing
End Function

' ============================================================================
' HELPER FUNCTIONS
' ============================================================================

'
' Clear cache (utility function)
'
Public Sub ClearDivvCache()
    On Error Resume Next

    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets("_DivvCache")

    If Not ws Is Nothing Then
        ws.Cells.Clear
        ws.Cells(1, 1).value = "Key"
        ws.Cells(1, 2).value = "Data"
        ws.Cells(1, 3).value = "Timestamp"

        MsgBox "Divv cache cleared successfully!", vbInformation
    End If
End Sub

'
' Test connection to Divv API
'
Public Sub TestDivvConnection()
    Dim result As Variant
    result = DIVV("AAPL", "price")

    If IsError(result) Then
        MsgBox "Connection failed! Check API_BASE_URL and make sure API is running.", vbCritical
    Else
        MsgBox "Connection successful! AAPL price: $" & result, vbInformation
    End If
End Sub
