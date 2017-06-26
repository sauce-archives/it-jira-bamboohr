from invoke import task, Collection
from app.web import ac


@task
def dev(ctx):
    """Launch Dev Server"""
    ctx.run("python main.py", env={
        "FLASK_DEBUG": "1",
        "PORT": "3000",
    }, replace_env=False)


@task
def initdb(ctx):
    from app import app, db
    with app.app_context():
        db.create_all()


@task
def resetdb(ctx):
    from app import app, db
    with app.app_context():
        db.drop_all()
        db.create_all()


@task
def view(ctx):
    from json import dumps
    from app import app, Client
    with app.app_context():
        print dumps([
            dict(c) for c in Client.query.all()
        ])


@task
def test(ctx):
    ctx.run("python -m pytest", pty=True)


ns = Collection()
ns.add_collection(ac.tasks())
ns.add_task(dev)
ns.add_task(test)
ns.add_task(resetdb)
ns.add_task(initdb)
