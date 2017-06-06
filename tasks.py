from invoke import task


@task
def dev(ctx):
    ctx.run("python web.py", env={
        "FLASK_DEBUG": "1",
        "PORT": "3000",
        "AC_BASE_URL": "https://d39ac125.ngrok.io"
    }, replace_env=False)


@task
def initdb(ctx):
    from web import db
    db.create_all()


@task
def view(ctx):
    from web import Client
    import json
    print json.dumps([
        c.as_dict() for c in Client.query.all()
    ])


@task
def test(ctx):
    ctx.run("python -m pytest", pty=True)
