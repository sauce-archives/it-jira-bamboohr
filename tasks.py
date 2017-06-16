from invoke import task


@task
def dev(ctx):
    ctx.run("python main.py", env={
        "FLASK_DEBUG": "1",
        "PORT": "3000",
        "AC_BASE_URL": "https://dev.gavinmogan.com"
    }, replace_env=False)


@task
def initdb(ctx):
    from app import app, db
    with app.app_context():
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
