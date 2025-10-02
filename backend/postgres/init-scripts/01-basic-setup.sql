# Creating users just for reading
CREATE USER read_only_user WITH PASSWORD 'readonly123';
GRANT CONNECT ON DATABASE resume_db TO read_only_user;
GRANT USAGE ON SCHEMA public TO read_only_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO read_only_user;

# Creating test DB
CREATE DATABASE resume_test;