' ============================================================================
' Dividend API Excel Add-in
' ============================================================================
' Custom functions to fetch dividend stock data directly in Excel
' Usage: =DIVV_PRICE("AAPL"), =DIVV_DIVIDEND("AAPL"), etc.
' ============================================================================

Option Explicit

' ============================================================================
' CONFIGURATION
' ============================================================================
Private Const API_BASE_URL As String = "https://api.yourdomain.com/v1"
Private Const API_KEY_CELL As String = "Settings!A2" ' Where users store their API key

' ============================================================================
' CORE API FUNCTION
' ============================================================================
Private Function CallAPI(endpoint As String) As String
    Dim http As Object
    Dim apiKey As String
    Dim url As String

    ' Get API key from settings cell
    On Error Resume Next
    apiKey = Range(API_KEY_CELL).Value
    On Error GoTo 0

    If apiKey = "" Then
        CallAPI = "ERROR: API Key not found in " & API_KEY_CELL
        Exit Function
    End If

    ' Build URL
    url = API_BASE_URL & endpoint

    ' Create HTTP request
    Set http = CreateObject("MSXML2.XMLHTTP")

    ' Make request with API key in header
    http.Open "GET", url, False
    http.setRequestHeader "X-API-Key", apiKey
    http.setRequestHeader "Content-Type", "application/json"
    http.Send

    ' Return response
    If http.Status = 200 Then
        CallAPI = http.responseText
    Else
        CallAPI = "ERROR: " & http.Status & " - " & http.statusText
    End If

    Set http = Nothing
End Function

' ============================================================================
' HELPER: Parse JSON (simple parser for specific fields)
' ============================================================================
Private Function ParseJSON(jsonText As String, fieldName As String) As String
    Dim startPos As Long
    Dim endPos As Long
    Dim searchStr As String

    searchStr = """" & fieldName & """:"
    startPos = InStr(jsonText, searchStr)

    If startPos = 0 Then
        ParseJSON = ""
        Exit Function
    End If

    startPos = startPos + Len(searchStr)

    ' Skip whitespace and quotes
    Do While Mid(jsonText, startPos, 1) = " " Or Mid(jsonText, startPos, 1) = """"
        startPos = startPos + 1
    Loop

    ' Find end of value
    endPos = startPos
    Do While endPos <= Len(jsonText)
        Dim ch As String
        ch = Mid(jsonText, endPos, 1)
        If ch = "," Or ch = "}" Or ch = """" Or ch = "]" Then
            Exit Do
        End If
        endPos = endPos + 1
    Loop

    ParseJSON = Mid(jsonText, startPos, endPos - startPos)
End Function

' ============================================================================
' STOCK PRICE FUNCTIONS
' ============================================================================

Public Function DIVV_PRICE(symbol As String) As Variant
    ' Get latest stock price
    ' Usage: =DIVV_PRICE("AAPL")

    Dim response As String
    Dim price As String

    response = CallAPI("/stocks/" & symbol & "/latest-price")

    If Left(response, 6) = "ERROR:" Then
        DIVV_PRICE = response
        Exit Function
    End If

    price = ParseJSON(response, "close")

    If price <> "" Then
        DIVV_PRICE = CDbl(price)
    Else
        DIVV_PRICE = "N/A"
    End If
End Function

Public Function DIVV_CHANGE(symbol As String) As Variant
    ' Get price change percentage
    ' Usage: =DIVV_CHANGE("AAPL")

    Dim response As String
    Dim change As String

    response = CallAPI("/stocks/" & symbol & "/latest-price")

    If Left(response, 6) = "ERROR:" Then
        DIVV_CHANGE = response
        Exit Function
    End If

    change = ParseJSON(response, "change_percent")

    If change <> "" Then
        DIVV_CHANGE = CDbl(change) / 100
    Else
        DIVV_CHANGE = "N/A"
    End If
End Function

' ============================================================================
' DIVIDEND FUNCTIONS
' ============================================================================

Public Function DIVV_YIELD(symbol As String) As Variant
    ' Get dividend yield
    ' Usage: =DIVV_YIELD("AAPL")

    Dim response As String
    Dim yld As String

    response = CallAPI("/stocks/" & symbol)

    If Left(response, 6) = "ERROR:" Then
        DIVV_YIELD = response
        Exit Function
    End If

    yld = ParseJSON(response, "dividend_yield")

    If yld <> "" Then
        DIVV_YIELD = CDbl(yld) / 100
    Else
        DIVV_YIELD = "N/A"
    End If
End Function

Public Function DIVV_ANNUAL(symbol As String) As Variant
    ' Get annual dividend amount
    ' Usage: =DIVV_ANNUAL("AAPL")

    Dim response As String
    Dim annual As String

    response = CallAPI("/dividends/" & symbol & "/metrics")

    If Left(response, 6) = "ERROR:" Then
        DIVV_ANNUAL = response
        Exit Function
    End If

    annual = ParseJSON(response, "ttm_dividend")

    If annual <> "" Then
        DIVV_ANNUAL = CDbl(annual)
    Else
        DIVV_ANNUAL = "N/A"
    End If
End Function

Public Function DIVV_NEXT_DATE(symbol As String) As Variant
    ' Get next ex-dividend date
    ' Usage: =DIVV_NEXT_DATE("AAPL")

    Dim response As String
    Dim nextDate As String

    response = CallAPI("/dividends/" & symbol & "/next")

    If Left(response, 6) = "ERROR:" Then
        DIVV_NEXT_DATE = response
        Exit Function
    End If

    nextDate = ParseJSON(response, "ex_dividend_date")

    If nextDate <> "" Then
        DIVV_NEXT_DATE = CDate(nextDate)
    Else
        DIVV_NEXT_DATE = "N/A"
    End If
End Function

Public Function DIVV_NEXT_AMOUNT(symbol As String) As Variant
    ' Get next dividend amount
    ' Usage: =DIVV_NEXT_AMOUNT("AAPL")

    Dim response As String
    Dim amount As String

    response = CallAPI("/dividends/" & symbol & "/next")

    If Left(response, 6) = "ERROR:" Then
        DIVV_NEXT_AMOUNT = response
        Exit Function
    End If

    amount = ParseJSON(response, "dividend")

    If amount <> "" Then
        DIVV_NEXT_AMOUNT = CDbl(amount)
    Else
        DIVV_NEXT_AMOUNT = "N/A"
    End If
End Function

Public Function DIVV_FREQUENCY(symbol As String) As Variant
    ' Get dividend frequency
    ' Usage: =DIVV_FREQUENCY("AAPL")

    Dim response As String
    Dim freq As String

    response = CallAPI("/dividends/" & symbol & "/metrics")

    If Left(response, 6) = "ERROR:" Then
        DIVV_FREQUENCY = response
        Exit Function
    End If

    freq = ParseJSON(response, "frequency")

    If freq <> "" Then
        DIVV_FREQUENCY = freq
    Else
        DIVV_FREQUENCY = "N/A"
    End If
End Function

' ============================================================================
' ETF FUNCTIONS
' ============================================================================

Public Function DIVV_AUM(symbol As String) As Variant
    ' Get Assets Under Management for ETFs
    ' Usage: =DIVV_AUM("SPY")

    Dim response As String
    Dim aum As String

    response = CallAPI("/stocks/" & symbol)

    If Left(response, 6) = "ERROR:" Then
        DIVV_AUM = response
        Exit Function
    End If

    aum = ParseJSON(response, "aum")

    If aum <> "" Then
        DIVV_AUM = CDbl(aum)
    Else
        DIVV_AUM = "N/A"
    End If
End Function

Public Function DIVV_IV(symbol As String) As Variant
    ' Get Implied Volatility (for covered call ETFs)
    ' Usage: =DIVV_IV("XYLD")

    Dim response As String
    Dim iv As String

    response = CallAPI("/stocks/" & symbol & "/latest-price")

    If Left(response, 6) = "ERROR:" Then
        DIVV_IV = response
        Exit Function
    End If

    iv = ParseJSON(response, "iv")

    If iv <> "" Then
        DIVV_IV = CDbl(iv) / 100
    Else
        DIVV_IV = "N/A"
    End If
End Function

Public Function DIVV_STRATEGY(symbol As String) As Variant
    ' Get ETF investment strategy
    ' Usage: =DIVV_STRATEGY("XYLD")

    Dim response As String
    Dim strategy As String

    response = CallAPI("/stocks/" & symbol)

    If Left(response, 6) = "ERROR:" Then
        DIVV_STRATEGY = response
        Exit Function
    End If

    strategy = ParseJSON(response, "investment_strategy")

    If strategy <> "" Then
        DIVV_STRATEGY = strategy
    Else
        DIVV_STRATEGY = "N/A"
    End If
End Function

' ============================================================================
' COMPANY INFO FUNCTIONS
' ============================================================================

Public Function DIVV_NAME(symbol As String) As Variant
    ' Get company/ETF name
    ' Usage: =DIVV_NAME("AAPL")

    Dim response As String
    Dim name As String

    response = CallAPI("/stocks/" & symbol)

    If Left(response, 6) = "ERROR:" Then
        DIVV_NAME = response
        Exit Function
    End If

    name = ParseJSON(response, "name")

    If name <> "" Then
        DIVV_NAME = name
    Else
        DIVV_NAME = "N/A"
    End If
End Function

Public Function DIVV_SECTOR(symbol As String) As Variant
    ' Get sector
    ' Usage: =DIVV_SECTOR("AAPL")

    Dim response As String
    Dim sector As String

    response = CallAPI("/stocks/" & symbol)

    If Left(response, 6) = "ERROR:" Then
        DIVV_SECTOR = response
        Exit Function
    End If

    sector = ParseJSON(response, "sector")

    If sector <> "" Then
        DIVV_SECTOR = sector
    Else
        DIVV_SECTOR = "N/A"
    End If
End Function

Public Function DIVV_INDUSTRY(symbol As String) As Variant
    ' Get industry
    ' Usage: =DIVV_INDUSTRY("AAPL")

    Dim response As String
    Dim industry As String

    response = CallAPI("/stocks/" & symbol)

    If Left(response, 6) = "ERROR:" Then
        DIVV_INDUSTRY = response
        Exit Function
    End If

    industry = ParseJSON(response, "industry")

    If industry <> "" Then
        DIVV_INDUSTRY = industry
    Else
        DIVV_INDUSTRY = "N/A"
    End If
End Function

' ============================================================================
' SCREENER FUNCTIONS
' ============================================================================

Public Function DIVV_HIGH_YIELD(minYield As Double, Optional limit As Integer = 10) As Variant
    ' Get high-yield stocks
    ' Usage: =DIVV_HIGH_YIELD(5, 10)
    ' Returns: Array of symbols

    Dim response As String
    Dim results() As String
    Dim i As Integer

    response = CallAPI("/screeners/high-yield?min_yield=" & minYield & "&limit=" & limit)

    If Left(response, 6) = "ERROR:" Then
        DIVV_HIGH_YIELD = response
        Exit Function
    End If

    ' Parse symbols from response (simplified)
    ' In production, use proper JSON parser
    DIVV_HIGH_YIELD = "Use /screeners/high-yield endpoint"
End Function

' ============================================================================
' UTILITY FUNCTIONS
' ============================================================================

Public Function DIVV_API_STATUS() As String
    ' Check API connection status
    ' Usage: =DIVV_API_STATUS()

    Dim response As String

    response = CallAPI("/health")

    If Left(response, 6) = "ERROR:" Then
        DIVV_API_STATUS = "Disconnected"
    Else
        DIVV_API_STATUS = "Connected"
    End If
End Function

Public Function DIVV_REFRESH()
    ' Force refresh all DIVV_ functions
    ' Usage: =DIVV_REFRESH() or assign to button

    Application.CalculateFullRebuild
    DIVV_REFRESH = "Refreshed at " & Now()
End Function
