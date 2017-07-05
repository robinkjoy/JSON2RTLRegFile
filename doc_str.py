vbs_header = '''Option Explicit
Sub Main()

    Dim oWord, oDoc
    Set oWord = CreateObject("Word.Application")
    Set oDoc = oWord.Documents.Add()

    Dim regStrings(3)
    Dim fieldStrings(5)
'''
vbs_reg = '''
    ' Reg {num}
    regStrings(0) = "{desc}"
    regStrings(1) = "{name}"
    regStrings(2) = "{offset}"
    InsertRegTable oWord, oDoc.Paragraphs.Last.Range, regStrings
'''
vbs_field = '''    ' Field {num}
    fieldStrings(0) = "{name}"
    fieldStrings(1) = "[{bits}]"
    fieldStrings(2) = "{type}"
    fieldStrings(3) = {default}
    fieldStrings(4) = "{desc}"
    InsertFieldRow oDoc.Range.Tables(oDoc.Range.Tables.Count), fieldStrings
'''
vbs_footer = '''
    oDoc.SaveAs("D:\\regs\svn\\test_doc.docx")
    oWord.Quit

End Sub'''
