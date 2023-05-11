import xlrd

from library import debug, common


class DatasheetManager:
    def __init__(self, brand):
        self.brand = brand

    def readDatasheet(self, datasheetType, datasheetPath, datasheetIndex=0, headerRow=0):
        debug.debug(self.brand, 0, f"Start reading {datasheetPath}")

        headers = []
        data = []

        if datasheetType == "XLSX":
            wb = xlrd.open_workbook(datasheetPath)
            sh = wb.sheet_by_index(datasheetIndex)

            for colId in range(0, sh.ncols):
                colName = common.formatText(sh.cell_value(headerRow, colId))
                headers.append(colName)

            for rowId in range(headerRow + 1, sh.nrows):
                row = []
                for colId in range(0, sh.ncols):
                    colValue = common.formatText(sh.cell_value(rowId, colId))
                    row.append(colValue)
                data.append(row)

        debug.debug(self.brand, 0,
                    f"Finished reading the {self.brand} datasheet")

        return (headers, data)
