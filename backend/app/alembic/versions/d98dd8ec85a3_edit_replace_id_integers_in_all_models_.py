"""Edit replace id integers in all models to use UUID instead

Revision ID: d98dd8ec85a3
Revises: 9c0a54914c78
Create Date: 2024-07-19 04:08:04.000976

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'd98dd8ec85a3'
down_revision = '9c0a54914c78'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == 'postgresql'
    is_mysql = bind.dialect.name == 'mysql'
    insp = inspect(bind)

    def column_exists(table_name, column_name):
        columns = insp.get_columns(table_name)
        return any(c['name'] == column_name for c in columns)

    # Ensure appropriate UUID handling based on database dialect
    if is_postgresql:
        op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        uuid_type = postgresql.UUID(as_uuid=True)
        uuid_default = sa.text('uuid_generate_v4()')
        user_table = '"user"'
        uuid_populate = 'uuid_generate_v4()'
    elif is_mysql:
        # MySQL doesn't have a native UUID type like PG, typically String(36) is used
        uuid_type = sa.String(36)
        uuid_default = sa.text('(UUID())')
        user_table = '`user` '
        uuid_populate = '(UUID())'
    else:
        # Fallback for other dialects
        uuid_type = sa.String(36)
        uuid_default = None
        user_table = 'user'
        uuid_populate = None

    # Create a new UUID column with a default UUID value
    if not column_exists('user', 'new_id'):
        op.add_column('user', sa.Column('new_id', uuid_type, nullable=True, default=uuid_default))
    if not column_exists('item', 'new_id'):
        op.add_column('item', sa.Column('new_id', uuid_type, nullable=True, default=uuid_default))
    if not column_exists('item', 'new_owner_id'):
        op.add_column('item', sa.Column('new_owner_id', uuid_type, nullable=True))

    # Populate the new columns with UUIDs
    if uuid_populate:
        op.execute(f'UPDATE {user_table} SET new_id = {uuid_populate} WHERE new_id IS NULL')
        op.execute(f'UPDATE item SET new_id = {uuid_populate} WHERE new_id IS NULL')
    
    # Populate foreign key relation
    op.execute(f'UPDATE item SET new_owner_id = (SELECT new_id FROM {user_table} WHERE {user_table}.id = item.owner_id) WHERE new_owner_id IS NULL')

    # Set the new_id as not nullable
    op.alter_column('user', 'new_id', nullable=False, type_=uuid_type)
    op.alter_column('item', 'new_id', nullable=False, type_=uuid_type)

    # Drop old constraints and rename new columns
    # Note: constraint names might vary by DB, using generic handling
    try:
        op.drop_constraint('item_owner_id_fkey', 'item', type_='foreignkey')
    except Exception:
        pass

    if column_exists('item', 'owner_id'):
        op.drop_column('item', 'owner_id')
    if column_exists('item', 'new_owner_id'):
        op.alter_column('item', 'new_owner_id', new_column_name='owner_id', type_=uuid_type)

    # Re-handle primary keys
    try:
        if is_postgresql:
            op.drop_constraint('user_pkey', 'user', type_='primary')
            op.drop_constraint('item_pkey', 'item', type_='primary')
        elif is_mysql:
            # Check if PK exists before dropping
            pk_user = insp.get_pk_constraint('user')
            if pk_user and pk_user.get('constrained_columns'):
                op.execute('ALTER TABLE `user` DROP PRIMARY KEY')
            pk_item = insp.get_pk_constraint('item')
            if pk_item and pk_item.get('constrained_columns'):
                op.execute('ALTER TABLE item DROP PRIMARY KEY')
    except Exception:
        pass

    if column_exists('user', 'id'):
        op.drop_column('user', 'id')
    if column_exists('user', 'new_id'):
        op.alter_column('user', 'new_id', new_column_name='id', type_=uuid_type)

    if column_exists('item', 'id'):
        op.drop_column('item', 'id')
    if column_exists('item', 'new_id'):
        op.alter_column('item', 'new_id', new_column_name='id', type_=uuid_type)

    # Create primary key constraint
    op.create_primary_key('user_pkey', 'user', ['id'])
    op.create_primary_key('item_pkey', 'item', ['id'])

    # Recreate foreign key constraint
    op.create_foreign_key('item_owner_id_fkey', 'item', 'user', ['owner_id'], ['id'])

def downgrade():
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == 'postgresql'
    is_mysql = bind.dialect.name == 'mysql'
    insp = inspect(bind)

    def column_exists(table_name, column_name):
        columns = insp.get_columns(table_name)
        return any(c['name'] == column_name for c in columns)

    # Reverse the upgrade process
    if not column_exists('user', 'old_id'):
        op.add_column('user', sa.Column('old_id', sa.Integer, autoincrement=True))
    if not column_exists('item', 'old_id'):
        op.add_column('item', sa.Column('old_id', sa.Integer, autoincrement=True))
    if not column_exists('item', 'old_owner_id'):
        op.add_column('item', sa.Column('old_owner_id', sa.Integer, nullable=True))

    if is_postgresql:
        user_table = '"user"'
        # Generate sequences for the integer IDs if not exist
        op.execute('CREATE SEQUENCE IF NOT EXISTS user_id_seq AS INTEGER OWNED BY "user".old_id')
        op.execute('CREATE SEQUENCE IF NOT EXISTS item_id_seq AS INTEGER OWNED BY item.old_id')

        op.execute('SELECT setval(\'user_id_seq\', COALESCE((SELECT MAX(old_id) + 1 FROM "user"), 1), false)')
        op.execute('SELECT setval(\'item_id_seq\', COALESCE((SELECT MAX(old_id) + 1 FROM item), 1), false)')

        op.execute('UPDATE "user" SET old_id = nextval(\'user_id_seq\')')
        op.execute('UPDATE item SET old_id = nextval(\'item_id_seq\'), old_owner_id = (SELECT old_id FROM "user" WHERE "user".id = item.owner_id)')
    elif is_mysql:
        user_table = '`user` '
        # MySQL AUTO_INCREMENT handles this more easily but we need to populate values first
        # Use a temporary variable to simulate sequence
        op.execute('SET @count := 0')
        op.execute(f'UPDATE {user_table} SET old_id = (@count := @count + 1)')
        op.execute('SET @count := 0')
        op.execute('UPDATE item SET old_id = (@count := @count + 1)')
        op.execute(f'UPDATE item SET old_owner_id = (SELECT old_id FROM {user_table} WHERE {user_table}.id = item.owner_id)')
    else:
        user_table = 'user'

    # Drop new columns and rename old columns back
    try:
        op.drop_constraint('item_owner_id_fkey', 'item', type_='foreignkey')
    except Exception:
        pass
        
    if column_exists('item', 'owner_id'):
        op.drop_column('item', 'owner_id')
    if column_exists('item', 'old_owner_id'):
        op.alter_column('item', 'old_owner_id', new_column_name='owner_id', type_=sa.Integer)

    try:
        if is_postgresql:
            op.drop_constraint('user_pkey', 'user', type_='primary')
            op.drop_constraint('item_pkey', 'item', type_='primary')
        elif is_mysql:
            pk_user = insp.get_pk_constraint('user')
            if pk_user and pk_user.get('constrained_columns'):
                op.execute('ALTER TABLE `user` DROP PRIMARY KEY')
            pk_item = insp.get_pk_constraint('item')
            if pk_item and pk_item.get('constrained_columns'):
                op.execute('ALTER TABLE item DROP PRIMARY KEY')
    except Exception:
        pass

    if column_exists('user', 'id'):
        op.drop_column('user', 'id')
    if column_exists('user', 'old_id'):
        op.alter_column('user', 'old_id', new_column_name='id', type_=sa.Integer)

    if column_exists('item', 'id'):
        op.drop_column('item', 'id')
    if column_exists('item', 'old_id'):
        op.alter_column('item', 'old_id', new_column_name='id', type_=sa.Integer)

    # Create primary key constraint
    op.create_primary_key('user_pkey', 'user', ['id'])
    op.create_primary_key('item_pkey', 'item', ['id'])

    # Recreate foreign key constraint
    op.create_foreign_key('item_owner_id_fkey', 'item', 'user', ['owner_id'], ['id'])
