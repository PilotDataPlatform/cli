from app.models.service_meta_class import MetaService
import click

def warn(*msgs):
    message = " ".join([str(msg) for msg in msgs])
    click.secho(str(message), fg="yellow")


def error(*msgs):
    message = " ".join([str(msg) for msg in msgs])
    click.secho(str(message), fg="red")


def succeed(*msgs):
    message = " ".join([str(msg) for msg in msgs])
    click.secho(str(message), fg="green")


def info(*msgs):
    message = " ".join([str(msg) for msg in msgs])
    click.secho(str(message), fg="white")
