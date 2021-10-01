## Builtin
import pathlib
## This Module
from aldb2.RecordReader import master
## Third Party
import click

@click.command()
@click.option("--recurse", "-r", is_flag=True,  default = False)
def compilemaster(recurse):
    dire = pathlib.Path.cwd()
    click.echo("Compile Master Stats and Episodes...")
    master.compile_directory(dire, recurse= recurse)
    click.echo("Done")