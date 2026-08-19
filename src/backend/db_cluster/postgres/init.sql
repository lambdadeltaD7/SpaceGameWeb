CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users(
    user_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_name VARCHAR(64) UNIQUE,
    user_email VARCHAR(64),
    user_password VARCHAR(64),
    pass_salted_hashed VARCHAR(128),
    is_admin BOOLEAN,
    res1 INT CHECK(res1 >= 0),
    res2 INT CHECK(res2 >= 0)
);


CREATE TABLE IF NOT EXISTS worlds(
    world_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INT,
    seed INT CHECK(seed >= 0),
    w INT CHECK( (w >= 16) AND (w <= 64) ),
    h INT CHECK( (h >= 16) AND (h <= 64) ),
    is_public BOOLEAN
);


CREATE TABLE IF NOT EXISTS planets(
    planet_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    world_id INT,
    user_id INT,
    res1 INT CHECK(res1 >= 0),
    res2 INT CHECK(res2 >= 0),
    x INT CHECK(x >= 0),
    y INT CHECK(y >= 0),
    shield_on BOOLEAN
);


CREATE TABLE IF NOT EXISTS transactions(
    transaction_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_from_id INT,
    user_to_id INT,
    res1 INT CHECK(res1 >= 0),
    res2 INT CHECK(res2 >= 0),
    created_at BIGINT CHECK(created_at >= 0)
);


CREATE TABLE IF NOT EXISTS miners(
    miner_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    world_id INT,
    user_id INT,
    x INT CHECK(x >= 0),
    y INT CHECK(y >= 0)
);


INSERT INTO 
users (user_name, user_email, user_password, pass_salted_hashed, is_admin, res1, res2) 
VALUES
('admin1', 'cool1@gmail.com', 'sudo1', crypt('sudo1', gen_salt('bf')), true,  9999, 9999),
('admin2', 'cool2@gmail.com', 'sudo2', crypt('sudo2', gen_salt('bf')), true,  9999, 9999),
('user1',  'lox1@gmail.com',  'pass1', crypt('pass1', gen_salt('bf')), false, 100,  100),
('user2',  'lox2@gmail.com',  'pass2', crypt('pass2', gen_salt('bf')), false, 100,  100);
