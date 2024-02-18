from aldb2.RecordReader import classes
import typing


def main():
    books = classes.listvalidfilenames(r"C:\Users\adama\Dropbox\][Video Editing\AnimeLife", recurse=True)
    records:typing.List[classes.SeasonRecord] = []
    for book in books:
        records.append(classes.SeasonRecord(book, data_only= False))
    records.sort()
    records.sort(key = lambda record: record.recordstats.version)
    if len(records) <= 1:
        print(f"Not enough Records to Compare: {len(records)}")

    currentrecord = records.pop(0)
    print(currentrecord)
    currentversion = currentrecord.recordstats.version
    currentcolumns = {}
    for header,column in zip((table:=currentrecord.week(1).table).headerrange().row(0),table.datarange().row(0)):
        if not column: continue
        if str(column).startswith("="):
            currentcolumns[header] = column
        
    
    while records:
        newrecord = records.pop(0)
        print(newrecord)
        newversion = newrecord.recordstats.version
        firstprint = dict(firstprint=True)
        def addheader(*args):
            if firstprint["firstprint"]:
                print(f"------VERSION: {newversion}------")
                firstprint["firstprint"] = False
            print(*args)
        existingheaders = list(currentcolumns)
        for header,column in zip((table:=newrecord.week(1).table).headerrange().row(0),table.datarange().row(0)):
            if not column or not str(column).startswith("="):
                continue
            if header not in existingheaders:
                addheader(f"New Column: {header}\n\t{column}")
                currentcolumns[header] = column
                continue
            elif column != currentcolumns[header]:
                addheader(f"Column Value Change:\n\t{header}:\n\t\t{currentcolumns[header]}\n\t=>\n\t\t{column}")
                currentcolumns[header] = column
            existingheaders.remove(header)
        for header in existingheaders:
            addheader(f"Column Removed: {header}")
            currentcolumns.pop(header)

    print("Done")

if __name__ == "__main__":
    main()