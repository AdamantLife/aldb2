## Builtin
import pathlib
## This Module
from aldb2.RecordReader import master
## Third Party
import click

@click.group()
def cli():
    pass

@cli.command()
@click.option("--recurse", "-r", is_flag=True,  default = False)
def compilemaster(recurse):
    dire = pathlib.Path.cwd()
    click.echo("Compile Master Stats and Episodes...")
    master.compile_directory(dire, recurse= recurse)
    click.echo("Done")


@cli.command()
@click.option("--directory", "-d",  type=click.Path(exists=True), default = pathlib.Path.cwd())
@click.option("--output", "-o", type=click.Path(), default = "master_firstepisodes.csv")
@click.option("--recurse", "-r", is_flag=True,  default = False)
def compile_firstepisodes(directory, output, recurse):
    click.echo("Compile First Episodes...")
    master.compile_firstepisodes(directory, output, recurse)

@cli.command()
@click.option("--directory", "-d",  type=click.Path(exists=True), default = pathlib.Path.cwd())
@click.option("--output", "-o", type=click.Path(), default = "master_lastepisodes.csv")
@click.option("--recurse", "-r", is_flag=True,  default = False)
def compile_lastepisodes(directory, output, recurse):
    click.echo("Compile Last Episodes...")
    master.compile_lastepisodes(directory, output, recurse)
    
    

if __name__ == "__main__":
    cli()