######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################
"""
Flask CLI Command Extensions
"""
import click
from flask.cli import with_appcontext
from service.models import db


######################################################################
# Command to recreate database
######################################################################
@click.command("db-create")
@with_appcontext
def db_create():
    """Recreates database tables"""
    click.echo("Recreating database tables...")
    db.drop_all()      # ✅ Mock expects this
    db.create_all()
    click.echo("Database recreated successfully!")


######################################################################
# Command to drop all tables
######################################################################
@click.command("db-drop")
@with_appcontext
def db_drop():
    """Drops all database tables"""
    click.echo("Dropping all database tables...")
    db.drop_all()
    click.echo("All tables dropped successfully!")


######################################################################
# CLI registration helper
######################################################################
def init_cli(app):
    """Registers Flask CLI commands with the app"""
    app.cli.add_command(db_create)
    app.cli.add_command(db_drop)
