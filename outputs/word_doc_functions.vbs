' Enumerations https://msdn.microsoft.com/en-us/library/office/aa211923(v=office.11).aspx
Option Explicit
Sub InsertRegTable(oWord, oRange, regStrings)

    With oRange
        .Paragraphs.Add
        With .Paragraphs(1)
            .Style = -3
            .Range.Text = regStrings(0)
        End With
        .Paragraphs.Add
        With .Paragraphs(2)
            .Style = -1
        End With
    End With
    
    oRange.Tables.Add oRange.Paragraphs(2).Range, 4, 5
    Dim oTable
    Set oTable = oRange.Tables(1)
    
    ' Set border properties
    With oTable.Borders
     .InsideLineStyle = 1
     .OutsideLineStyle = 1
    End With
    
    ' Set table properties
    With oTable
        .Columns(1).Width = oWord.InchesToPoints(1.1)
        .Columns(2).Width = oWord.InchesToPoints(0.5)
        .Columns(3).Width = oWord.InchesToPoints(0.5)
        .Columns(4).Width = oWord.InchesToPoints(1.1)
        .Columns(5).Width = oWord.InchesToPoints(3.2)
        Dim row
        For Each row In .Rows
            row.Cells.VerticalAlignment = 1
        Next
    End With

    ' Insert table contents
    SetHeader oTable, 1, 1, "Register Name"
    oTable.Cell(1, 2).Range.Text = regStrings(1)
    SetHeader oTable, 2, 1, "Offset"
    oTable.Cell(2, 2).Range.Text = regStrings(2)
    SetHeader oTable, 3, 1, "Fields"
    SetHeader oTable, 4, 1, "Field Name"
    SetHeader oTable, 4, 2, "Bits"
    SetHeader oTable, 4, 3, "Type"
    SetHeader oTable, 4, 4, "Default Value"
    SetHeader oTable, 4, 5, "Description"
    
    ' Merge cells
    MergeCells oWord.ActiveDocument, oTable, 1, 2, 1, 5
    MergeCells oWord.ActiveDocument, oTable, 2, 2, 2, 5
    MergeCells oWord.ActiveDocument, oTable, 3, 1, 3, 5
    oTable.Cell(3, 1).Range.ParagraphFormat.Alignment = 1

End Sub

Sub InsertFieldRow(oTable, fieldStrings)
    Dim oRow
    oTable.Rows.Add
    Set oRow = oTable.Rows(oTable.Rows.Count)
    Dim i
    For i = 0 To 4
        oRow.Cells(i + 1).Range.Text = fieldStrings(i)
        oRow.Cells(i + 1).Range.Font.Bold = False
    Next
End Sub

Sub MergeCells(doc, oTable, si, sj, ei, ej)
    doc.Range(oTable.Cell(si, sj).Range.Start, oTable.Cell(ei, ej).Range.End).Cells.Merge
End Sub

Sub SetHeader(oTable, row, col, header)
    With oTable.Cell(row, col).Range
        .Text = header
        .Font.Bold = True
    End With
End Sub
