ALTER SYSTEM SET listen_addresses = '*';
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_error_statement = 'ERROR';
ALTER SYSTEM SET archive_mode = 'on';
ALTER SYSTEM SET archive_command = 'cp %p /oracle/pg_data/archive/%f';
ALTER SYSTEM SET max_wal_senders = 10;
ALTER SYSTEM SET wal_level = 'replica';
ALTER SYSTEM SET wal_log_hints = 'on';
ALTER SYSTEM SET log_replication_commands = 'on';
ALTER ROLE postgres PASSWORD 'Qq12345';

CREATE USER repl_user WITH REPLICATION ENCRYPTED PASSWORD 'repl_user';
SELECT pg_create_physical_replication_slot('replication_slot');


CREATE TABLE emails(
    ID SERIAL PRIMARY KEY,
    email VARCHAR (200) NOT NULL
);

CREATE TABLE phone_numbers(
    ID SERIAL PRIMARY KEY,
    number VARCHAR (200)
);

INSERT INTO emails (ID, email) VALUES
(1,'johndoe@email.com'),
(2, 'janesmith@email.com');

INSERT INTO phone_numbers (ID, number) VALUES
(1,'8 888 88-88-88'),
(2, '8 999 99-99-99');