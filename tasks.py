from invoke import task


@task
def dev(ctx):
    ctx.run("FLASK_DEBUG=1 PORT=3000 AC_BASE_URL=https://d39ac125.ngrok.io python web.py")


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
    # ctx.run("python -mpickle clients.pk")


@task
def test(ctx):
    ctx.run("python -m pytest", pty=True)
