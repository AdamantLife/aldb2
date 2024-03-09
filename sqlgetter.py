import AL_Filemodules
import pathlib                     
import json

here = pathlib.Path().resolve()
files = AL_Filemodules.iterdir_re(here, "sql.json", recurse=True)
out = []
for file in files:
    if "test" in str(file).lower(): continue
    print(file)
    with open(file,'r') as f:
        parsed = json.load(f)
        for table in parsed.get("tables"):
            if table.get("sql"):
                out.append(table['sql']+";")

with open("output.sql", "w") as f:
    f.write("\n".join(out))