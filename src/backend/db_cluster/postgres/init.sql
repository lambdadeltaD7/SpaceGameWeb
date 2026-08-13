CREATE TABLE IF NOT EXISTS users(
    user_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_name VARCHAR(64) UNIQUE,
    user_email VARCHAR(64),
    user_password VARCHAR(64),
    is_admin BOOLEAN,
    res1 INT CHECK(res1 >= 0),
    res2 INT CHECK(res2 >= 0)
);

INSERT INTO 
users (user_name, user_email, user_password, is_admin, res1, res2) 
VALUES
('admin1', 'cool1@gmail.com', 'sudo1', true, 9999, 9999),
('admin2', 'cool2@gmail.com', 'sudo2', true, 9999, 9999),
('user1', 'lox1@gmail.com', 'pass1', false, 100, 100),
('user2', 'lox2@gmail.com', 'pass2', false, 100, 100);